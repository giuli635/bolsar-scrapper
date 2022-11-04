import os
import traceback
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By

CURRENT_DATE = date.today()
EXECUTION_DIRECTORY = os.getcwd()
CACHE_DIRECTORY = "cache"
DOWNLOAD_DIRECTORY = "download"
# TODO: check if data directory exists

def organizeClosingData(source, destination, date, titles):
    os.mkdir(os.path.join(destination, date))

    files = os.listdir(source)
    for i in range(0, len(files)):
        if (files[i].endswith(".csv")):
            os.rename(os.path.join(source, files[i]),
                      os.path.join(destination, date, titles[i] + ".csv"))

def getNegotiatedAmounts(browser):
    negociatedAmounts = []
    
    return negociatedAmounts

def getClosingData(date, browser):
    browser.get(f"https://bolsar.info/cierre/cierre_{date}.html")

    # titles = browser.find_elements(By.CSS_SELECTOR, "span.mercados")
    # titles = list(map(lambda x : x.text.lower().replace(" ", "_"), titles))
    # titles = titles[titles.index("paneles") + 1:]

    # buttons = browser.find_elements(By.CLASS_NAME, "buttons-csv")
    # for button in buttons:
    #     button.click()

    montosNegociados = []
    tablaMontosNegociados = browser.find_element(By.ID, "tabla")
    cuerpoTablaMontosNegociados = tablaMontosNegociados.find_element(By.TAG_NAME, "tbody")
    filasMontosNegociados = cuerpoTablaMontosNegociados.find_elements(By.TAG_NAME, "tr")

    for row in filasMontosNegociados:
        montosNegociados.append(row.text.split(" "))

    print(montosNegociados)

    return titles

if __name__ == "__main__":
    try:
        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.manager.showWhenStarting", False)
        options.set_preference("browser.download.dir", os.path.join(EXECUTION_DIRECTORY,
                                                                    CACHE_DIRECTORY,
                                                                    DOWNLOAD_DIRECTORY))
        options.headless = True

        browser = webdriver.Firefox(options = options)

        organizeClosingData(os.path.join(EXECUTION_DIRECTORY, CACHE_DIRECTORY, DOWNLOAD_DIRECTORY),
                            os.path.join(EXECUTION_DIRECTORY, CACHE_DIRECTORY), "2022-10-07",
                            getClosingData("2022-10-07", browser))
    except Exception:
        traceback.print_exc()
    finally:
        browser.close()
