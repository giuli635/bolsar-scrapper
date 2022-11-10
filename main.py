import os
import traceback
import csv
import argparse
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common import exceptions

CURRENT_DATE = date.today()

parser = argparse.ArgumentParser(
    prog="bolsar-scrapper",
    description="A basic web scrapper for bolsar.info",
    epilog="Made by Giuliano Taormina",
)

parser.add_argument(
    "-b",
    dest="browserBinary",
    action="store",
    help="Specifies the browser binary location",
)
parser.add_argument(
    "-d", dest="directory", action="store", help="Specifies the working directory"
)
args = parser.parse_args()

directory = args.directory if args.directory else ""
browserBinary = args.browserBinary


def organizeClosingData(directory, date, browser):
    workingDirectory = os.path.join(directory, date)

    titles = getClosingData(date, browser)

    if os.path.exists(workingDirectory):
        files = os.listdir(workingDirectory)
        for i in range(0, len(files)):
            if files[i].endswith(".csv"):
                os.rename(
                    os.path.join(workingDirectory, files[i]),
                    os.path.join(workingDirectory, titles[i] + ".csv"),
                )

    negociatedAmounts = list(zip(*getNegotiatedAmounts(browser)))

    with open(
        os.path.join(workingDirectory, "montos_negociados.csv"), "w", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerows(negociatedAmounts[0:2])


def checkIfDataExists(directory, date):
    return os.path.exists(os.path.join(directory, date))


def getNegotiatedAmounts(browser):
    negociatedAmounts = []
    negociatedAmountsTable = browser.find_element(By.ID, "tabla")
    negociatedAmountsTableBody = negociatedAmountsTable.find_element(
        By.TAG_NAME, "tbody"
    )
    negociatedAmountsRows = negociatedAmountsTableBody.find_elements(By.TAG_NAME, "tr")

    for row in negociatedAmountsRows:
        rowContent = []
        for cell in row.find_elements(By.TAG_NAME, "td"):
            rowContent.append(cell.text)
        negociatedAmounts.append(rowContent)

    return negociatedAmounts


def getClosingData(date, browser):
    browser.get(f"https://bolsar.info/cierre/cierre_{date}.html")

    titles = browser.find_elements(By.CSS_SELECTOR, "span.mercados")
    titles = list(map(lambda x: x.text.lower().replace(" ", "_"), titles))
    titles = titles[titles.index("paneles") + 1 :]

    buttons = browser.find_elements(By.CLASS_NAME, "buttons-csv")
    for button in buttons:
        button.click()

    return titles


if __name__ == "__main__":
    browser = None

    if not directory.startswith("/"):
        directory = os.path.join(os.getcwd(), directory)

    if not checkIfDataExists(directory, "2022-10-07"):
        try:
            options = webdriver.FirefoxOptions()
            options.set_preference("browser.download.folderList", 2)
            options.set_preference("browser.download.manager.showWhenStarting", False)
            options.set_preference(
                "browser.download.dir",
                os.path.join(directory, "2022-10-07"),
            )
            if browserBinary:
                options.binary_location = browserBinary

            options.headless = True

            browser = webdriver.Firefox(options=options)

            organizeClosingData(directory, "2022-10-07", browser)
        except exceptions.SessionNotCreatedException:
            print("Browser binary not found")
        except Exception:
            traceback.print_exc()
        finally:
            if browser:
                browser.close()
