import csv
import json
import os
import tempfile
from shutil import move
from typing import Dict, List

from get_certificate_chain import chain_to_string, get_certificate, walk_the_chain
from requests import ConnectionError, Session
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service


def organize_closing_data(
    source_directory: str, dest_directory: str, titles: List[str]
) -> None:
    """Moves and rename the obtained files to make easier to work with them.

    Arguments:
        source_directory -- directory where the files are located.
        dest_directory -- directory where the files are going to be moved to.
        titles -- list of new names for the files.
    """
    working_directory = __create_directory(dest_directory)
    files = os.listdir(source_directory)
    files.sort(key=lambda str: (len(str), str))
    for i in range(0, len(files)):
        if files[i].endswith(".csv"):
            move(
                os.path.join(source_directory, files[i]),
                os.path.join(working_directory, titles[i] + ".csv"),
            )


def get_negotiated_amounts(browser: webdriver.Firefox) -> List[list]:
    """Obtains the negotiated amounts of money.

    Arguments:
        browser -- Selenium session of Firefox with the required webpage open.

    Returns:
        Matrix containing the amount of money negotiated per financial instrument type in a given day.
    """
    try:
        negotiated_amounts = []
        negotiated_amounts_table = browser.find_element(By.ID, "tabla")
        negotiated_amounts_table_body = negotiated_amounts_table.find_element(
            By.TAG_NAME, "tbody"
        )
        negotiated_amounts_rows = negotiated_amounts_table_body.find_elements(
            By.TAG_NAME, "tr"
        )

        for row in negotiated_amounts_rows:
            row_content = []
            for cell in row.find_elements(By.TAG_NAME, "td"):
                row_content.append(cell.text)
            negotiated_amounts.append(row_content)
    except NoSuchElementException:
        raise NoSuchElementException(
            "Unable to locate the negotiated amounts, probably the source page have changed or the URL is wrong."
        )

    return negotiated_amounts


def negotiated_amounts_to_csv(directory: str, negotiated_amounts: List[list]) -> None:
    """Transforms the negotiated amounts matrix to a CSV.

    Arguments:
        directory -- directory where the CSV is going to be located.
        negotiated_amounts -- negotiated amounts matrix.
    """
    with open(
        os.path.join(directory, "montos_negociados.csv"), "w", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerows(negotiated_amounts[0:2])


def get_closing_data(browser: webdriver.Firefox) -> List[str]:
    """Downloads every csv present in the bolsar webpage containing the
    information about the closing of a day.

    Arguments:
        browser -- Selenium session of Firefox the necessary webpage open.

    Returns:
        List of the titles corresponding to the information displayed in the
        CSVs or empty list if an error ocurred.
    """
    titles = browser.find_elements(By.CSS_SELECTOR, "span.mercados")

    if titles:
        titles = list(map(lambda x: x.text.lower().replace(" ", "_"), titles))
        titles = titles[titles.index("paneles") + 1 :]
        buttons = browser.find_elements(By.CLASS_NAME, "buttons-csv")
        for button in buttons:
            button.click()
    else:
        raise NoSuchElementException(
            "Unable to locate the closing data, probably the source page have changed or the URL is wrong."
        )

    return titles


def get_and_organize_closing_data(
    browser: webdriver.Firefox,
    source_directory: str,
    dest_directory: str,
    date: str,
    negotiated_amounts: bool,
) -> None:
    """Wrapper function to get the closing data and the negotiated amounts of a
    certain day, also managing the opening of the corresponding webpage.

    Arguments:
        browser -- Selenium session of Firefox.
        source_directory -- directory where the files will be downloaded.
        dest_directory -- directory where the files will be moved to.
        date -- day of which to obtain information.
        negotiated_amounts -- if True gets the negotiated amounts of the day.
    """
    directory = os.path.join(dest_directory, date)
    if not os.path.exists(directory):
        browser.get(f"https://bolsar.info/cierre/cierre_{date}.html")
        titles = get_closing_data(browser)
        organize_closing_data(source_directory, directory, titles)
        if negotiated_amounts:
            negotiated_amounts_to_csv(directory, get_negotiated_amounts(browser))
        browser.get("about:home")
    else:
        raise FileExistsError(
            f"There is already a directory for the specified date ({date}), check the content",
        )


def get_stocks_data(
    browser: webdriver.Firefox, stocks: List[str]
) -> List[Dict[str, str]]:
    """Obtains basic data about the companies that issue the stocks.

    Arguments:
        browser -- Selenium session of Firefox.
        stocks -- list of the stocks to search for.

    Returns:
        List of dictionaries containing the received information.
    """

    info = []

    browser.get("https://open.bymadata.com.ar/#/dashboard")
    browser.get(
        "https://open.bymadata.com.ar/vanoms-be-core/rest/api/bymadata/free/bnown/fichatecnica/"
    )

    jsessionid = browser.get_cookie("JSESSIONID")["value"]

    session = create_stock_data_session(jsessionid)
    for stock in stocks:
        try:
            info.append(get_stock_data(stock, session))
        except ConnectionError:
            session.close()
            session = create_stock_data_session(jsessionid)
            info.append(get_stock_data(stock, session))
    session.close()

    return info


def get_stock_data(stock: str, session: Session) -> Dict[str, str]:
    """Get a JSON with the available data of a given stock.

    Arguments:
        stock -- the name of the stock from which the data will be retrieved.
        session -- a requests session prepared to access to the API.

    Returns:
        A dictionary with the obtained data.
    """
    URL_NOMBRE = "https://open.bymadata.com.ar/vanoms-be-core/rest/api/bymadata/free/bnown/fichatecnica/especies/general"
    URL_DATOS = "https://open.bymadata.com.ar/vanoms-be-core/rest/api/bymadata/free/bnown/fichatecnica/sociedades/general"

    data = {"symbol": stock, "Content-Type": "application/json"}
    stock_data = {"stock": stock}
    r = session.post(
        URL_DATOS,
        json.dumps(data),
    )
    data_response = r.json()["data"]

    r = session.post(
        URL_NOMBRE,
        json.dumps(data),
    )
    name_response = r.json()["data"]

    if name_response:
        stock_data["nombre"] = name_response[0]["emisor"]
    if data_response:
        stock_data.update(data_response[0])

    return stock_data


def create_stock_data_session(jsessionid):
    """Create a requests session to access to the API to retrieve
    the desired data.

    Arguments:
        jsessionid -- the value of a cookie needed to stablish connection with the API.

    Returns:
        A session object prepared to make the requests.
    """
    session = Session()

    session.headers = {
        "Host": "open.bymadata.com.ar",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://open.bymadata.com.ar/",
        "Content-Type": "application/json",
        "Origin": "https://open.bymadata.com.ar",
        "DNT": "1",
        "Connection": "keep-alive",
        "Cookie": f"JSESSIONID={jsessionid}",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

    session.verify = get_bymadata_ssl_certificate()

    return session


def get_bymadata_ssl_certificate():
    certificate = tempfile.NamedTemporaryFile("w+t", delete=False, suffix=".pem")
    certificate.write(
        chain_to_string(walk_the_chain(get_certificate("open.bymadata.com.ar", 443)))
    )
    certificate.close()
    return certificate.name


def create_browser(
    download_directory: str = None, browser_binary: str = None, implicit_wait: int = 10
) -> webdriver.Firefox:
    """Create a Selenium session of Firefox, including basic configuration,
    such as enabling headless and configuring downloads directory and the
    binary's location

    Keyword Arguments:
        download_directory -- download directory for Firefox. (default: {None})
        browser_binary -- the binary's location on the system. (default: {None})

    Returns:
        A Selenium session of Firefox.
    """
    browser = None

    options = webdriver.FirefoxOptions()
    service = Service(log_path=os.devnull)
    if download_directory:
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", download_directory)
    if browser_binary:
        options.binary_location = browser_binary
    options.add_argument("-headless")
    browser = webdriver.Firefox(options=options, service=service)
    browser.implicitly_wait(implicit_wait)

    return browser


def __create_directory(directory: str) -> str:
    """Creates a directory if it's not created and returns its absolute path.

    Arguments:
        directory -- directory to create.

    Returns:
        Absolute path of the created directory.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

    return os.path.abspath(directory)
