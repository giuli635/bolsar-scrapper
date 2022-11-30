import csv
import os
import sys
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common import exceptions
from shutil import move


def organize_closing_data(source_directory, dest_directory, titles):
    if os.path.exists(source_directory):
        working_directory = __create_directory(dest_directory)
        files = os.listdir(source_directory)
        files.sort(key=lambda str: (len(str), str))
        for i in range(0, len(files)):
            if files[i].endswith(".csv"):
                move(
                    os.path.join(source_directory, files[i]),
                    os.path.join(working_directory, titles[i] + ".csv"),
                )
    else:
        print("Source directory doesn't exists")


def get_negotiated_amounts(browser):
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


def negotiated_amounts_to_csv(directory, negotiated_amounts):
    with open(
        os.path.join(directory, "montos_negociados.csv"), "w", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerows(negotiated_amounts[0:2])


def get_closing_data(browser):
    titles = browser.find_elements(By.CSS_SELECTOR, "span.mercados")
    if titles:
        titles = list(map(lambda x: x.text.lower().replace(" ", "_"), titles))
        titles = titles[titles.index("paneles") + 1 :]

        buttons = browser.find_elements(By.CLASS_NAME, "buttons-csv")
        for button in buttons:
            button.click()
    else:
        print("Could not find the searched elements")

    return titles


def get_and_organize_closing_data(
    browser, source_directory, dest_directory, date, negotiated_amounts
):
    directory = os.path.join(dest_directory, date)
    if not os.path.exists(directory):
        browser.get(f"https://bolsar.info/cierre/cierre_{date}.html")
        titles = get_closing_data(browser)
        if titles:
            organize_closing_data(source_directory, directory, titles)
            if negotiated_amounts:
                negotiated_amounts_to_csv(
                    directory, get_negotiated_amounts(browser)
                )
        else:
            print(
                "Check the entered dates, the resultant URL is probably",
                "wrong or the stock wasn't open that day",
            )
    else:
        print(
            f"There is already a directory for the specified date ({date}),",
            "check the content",
        )


def get_stock_data(browser, stock):
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


def create_browser(directory=None, browser_binary=None):
    browser = None

    try:
        options = webdriver.FirefoxOptions()
        if directory:
            options.set_preference("browser.download.folderList", 2)
            options.set_preference("browser.download.dir", directory)
        if browser_binary:
            options.binary_location = browser_binary
        options.headless = True
        browser = webdriver.Firefox(
            options=options, service_log_path=os.devnull
        )
    except exceptions.SessionNotCreatedException:
        print("Browser binary not found")
        sys.exit(1)
    except DeprecationWarning:
        pass
    except Exception:
        traceback.print_exc()

    return browser


def __create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

    return os.path.abspath(directory)
