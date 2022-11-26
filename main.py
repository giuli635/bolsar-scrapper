import argparse
import os
import tempfile
import traceback
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common import exceptions
from shutil import move


def organize_closing_data(source_directory, dest_directory, titles):
    if os.path.exists(source_directory):
        working_directory = __create_directory(dest_directory)
        files = os.listdir(source_directory)
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


def get_closing_data(date, browser):
    browser.get(f"https://bolsar.info/cierre/cierre_{date}.html")

    titles = browser.find_elements(By.CSS_SELECTOR, "span.mercados")
    titles = list(map(lambda x: x.text.lower().replace(" ", "_"), titles))
    titles = titles[titles.index("paneles") + 1 :]

    buttons = browser.find_elements(By.CLASS_NAME, "buttons-csv")
    for button in buttons:
        button.click()

    return titles


def __create_browser(directory=None, browser_binary=None):
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
    except DeprecationWarning:
        pass
    except Exception:
        traceback.print_exc()

    return browser


def __create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    os.chdir(directory)
    directory = os.getcwd()

    return directory


def __create_parser():
    parser = argparse.ArgumentParser(
        prog="bolsar-scrapper",
        description="A basic web scrapper for bolsar.info",
        epilog="Made by Giuliano Taormina",
    )

    parser.add_argument(
        "-b",
        dest="browser_binary",
        action="store",
        default=None,
        help="Sets the browser binary location",
    )

    parser.add_argument(
        "-d",
        dest="directory",
        action="store",
        default="",
        help="Sets the working directory",
    )

    parser.add_argument(
        "-t",
        dest="date",
        action="store",
        help="Sets the dates to get data from",
        nargs="*",
    )

    parser.add_argument(
        "-c",
        dest="action",
        action="store_const",
        const=0,
        default=0,
        help="Gets the closing data of the specified date, if not, of the current date",
    )

    return parser


if __name__ == "__main__":
    CURRENT_DATE = date.today().strftime("%Y-%m-%d")
    parser = __create_parser()
    args = parser.parse_args()

    directory = args.directory
    browser_binary = args.browser_binary

    match args.action:
        case 0:
            dest_directory = os.path.join(directory, CURRENT_DATE)
            if not os.path.exists(dest_directory):
                with tempfile.TemporaryDirectory() as temp_directory:
                    try:
                        browser = __create_browser(temp_directory, browser_binary)
                        titles = get_closing_data(CURRENT_DATE, browser)
                        organize_closing_data(
                            temp_directory, dest_directory, titles
                        )
                    finally:
                        if browser:
                            browser.close()
            else:
                print(f"There is already a directory for the specified date ({CURRENT_DATE}), check the content")
