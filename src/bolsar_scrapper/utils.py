import csv
import os
from .exceptions import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import *
from shutil import move
from typing import List, Tuple


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
        browser -- Selenium session of Firefox with the necessary webpage open.

    Returns:
        Matrix containing the amount of money negotiated per financial instrument type in a given day.
    """
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
    """Downloads every csv present in the bolsar webpage containing the information about the closing of a day.

    Arguments:
        browser -- Selenium session of Firefox the necessary webpage open.

    Returns:
        List of the titles corresponding to the information displayed in the CSVs or empty list if an error ocurred.
    """
    titles = browser.find_elements(By.CSS_SELECTOR, "span.mercados")

    if titles:
        titles = list(map(lambda x: x.text.lower().replace(" ", "_"), titles))
        titles = titles[titles.index("paneles") + 1 :]
        buttons = browser.find_elements(By.CLASS_NAME, "buttons-csv")
        for button in buttons:
            button.click()
    else:
        raise NoSuchElementException("Unable to locate the closing data.")

    return titles


def get_and_organize_closing_data(
    browser: webdriver.Firefox,
    source_directory: str,
    dest_directory: str,
    date: str,
    negotiated_amounts: bool,
) -> None:
    """Wrapper function to get the closing data and the negotiated amounts of a certain day, also managing the opening of the corresponding webpage.

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
        try:
            titles = get_closing_data(browser)
            organize_closing_data(source_directory, directory, titles)
            if negotiated_amounts:
                negotiated_amounts_to_csv(directory, get_negotiated_amounts(browser))
        except NoSuchElementException:
            raise WrongDateException(
                "Check the entered dates, the resultant URL is probably wrong or the stock wasn't open that day",
            )
    else:
        raise FileExistsError(
            f"There is already a directory for the specified date ({date}), check the content",
        )


def get_stock_data(browser: webdriver.Firefox, stock: str) -> Tuple[str, float]:
    """Obtains the name of the company that issues the specified stock along with its nominal value.

    Arguments:
        browser -- Selenium session of Firefox.
        stock -- name of the stock.

    Returns:
        Tuple containing the issuer of the stock and its nominal value or a tuple of an empty string and 0.
    """
    browser.get(f"https://bolsar.info/infoEspecie.php?especie={stock}")
    table = browser.find_element(By.ID, "titulo-table").text
    rows = table.splitlines()
    issuer = ""
    nominal_value = 0

    for row in rows:
        if "EMISOR" in row:
            issuer = row.split(" ")[1:]
            issuer = " ".join(issuer)
        elif "VALOR NOMINAL" in row:
            nominal_value = row.split(" ")[2]
            nominal_value = float(nominal_value.replace(",", "."))

    return issuer, nominal_value


def create_browser(
    download_directory: str = None, browser_binary: str = None
) -> webdriver.Firefox:
    """Create a Selenium session of Firefox, including basic configuration, such as enabling headless and configuring downloads directory and the binary's location

    Keyword Arguments:
        download_directory -- download directory for Firefox. (default: {None})
        browser_binary -- the binary's location on the system. (default: {None})

    Returns:
        A Selenium session of Firefox.
    """
    browser = None

    options = webdriver.FirefoxOptions()
    if download_directory:
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir", download_directory)
    if browser_binary:
        options.binary_location = browser_binary
    options.headless = True
    browser = webdriver.Firefox(options=options, service_log_path=os.devnull)

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
