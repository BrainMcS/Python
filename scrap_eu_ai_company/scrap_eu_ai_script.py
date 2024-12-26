import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

def scrape_single_company_selenium(url):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        company_data = {"Name": None, "Category": None, "Based in": None, "Tags": None, "Founded": None}

        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "listing-details")))

            try:
                name_element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "entry-title")))
                company_data["Name"] = name_element.text.strip()
            except TimeoutException:
                print("Name element not found.")

            details_element = driver.find_element(By.CLASS_NAME, "listing-details")
            detail_items = details_element.find_elements(By.CLASS_NAME, "wpbdp-field-display")

            for item in detail_items:
                try:
                    label_element = item.find_element(By.CLASS_NAME, "field-label")
                    value_element = item.find_element(By.CLASS_NAME, "value")

                    label = label_element.text.strip().replace(":", "")
                    value = value_element.text.strip()
                    if label in ("Category", "Based in", "Tags", "Founded"): #Only these fields
                        company_data[label] = value
                except StaleElementReferenceException:
                    print("Stale element encountered. Retrying...")
                    continue
                except NoSuchElementException:
                    print("Label or value element not found in current item.")
                    continue

        except TimeoutException:
            print("Listing details not found within timeout.")

        driver.quit()
        return company_data

    except Exception as e:
        print(f"Outer Error: {e}")
        return None

if __name__ == "__main__":
    company_url = "https://www.eu-startups.com/directory/srnt-bdr-serenity/"
    company_data = scrape_single_company_selenium(company_url)

    if company_data:
        print(company_data)
        df = pd.DataFrame([company_data])
        df.to_csv("single_company_data.csv", index=False, encoding="utf-8")
        print("Data saved to single_company_data.csv")
    else:
        print("Could not scrape company data.")