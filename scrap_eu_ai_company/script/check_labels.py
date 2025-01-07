from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def find_based_in_element_info(url):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36")

        with webdriver.Chrome(options=options) as driver:
            driver.get(url)
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "listing-details")))

                detail_elements = driver.find_elements(By.CLASS_NAME, "wpbdp-field-display")

                for element in detail_elements:
                    class_attribute = element.get_attribute("class").replace(u'\xa0', u' ') #Replace non-breaking spaces in class attribute
                    if "wpbdp-field-based_in" in class_attribute:
                        print("Found 'Based in' element!")
                        print("Element tag:", element.tag_name)
                        print("Element class:", class_attribute)
                        try:
                            value_element = element.find_element(By.CLASS_NAME, "value")
                            print("Value element tag:", value_element.tag_name)
                            print("Value element class:", value_element.get_attribute("class"))
                        except NoSuchElementException:
                            print("No value element found within 'Based in' element.")
                        return

                print("'Based in' element not found.")
                return None

            except TimeoutException:
                print("Timeout waiting for listing details to load.")
                return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    company_url = "https://www.eu-startups.com/directory/?wpbdp_view=search&kw=%23SRNT+Serenity"
    find_based_in_element_info(company_url)