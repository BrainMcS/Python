import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_company_data(url, max_pages=10):  # Added max_pages parameter with default 10
    all_companies_data = []

    for page_number in range(1, max_pages + 1):
        if page_number == 1:
            page_url = url  # Use original URL for the first page
        else:
            page_url = f"https://www.eu-startups.com/directory/page/{page_number}/?wpbdp_sort=field-1"  # Construct URL for subsequent pages

        print(f"Scraping page {page_number}: {page_url}")

        try:
            response = requests.get(page_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            listing_elements = soup.find_all("div", class_="wpbdp-listing")

            for listing in listing_elements:
                company_data = {"Name": None, "Category": None, "Based in": None, "Tags": None, "Founded": None}

                company_title = listing.select_one(".listing-title h3 a")
                if company_title:
                    company_data["Name"] = company_title.text.strip()
                    print(f"Name found on page {page_number}:", company_data["Name"])

                detail_elements = listing.find_all("div", class_="wpbdp-field-display")

                for element in detail_elements:
                    label_element = element.find("span", class_="field-label")

                    if label_element:
                        label_text = label_element.text.strip().replace(":", "").replace(u'\xa0', u' ')
                        value_element = element.find("div", class_="value")

                        if value_element and value_element.text.strip():
                            value = value_element.text.strip()
                            if label_text == "Category":
                                category_link = value_element.find("a")
                                company_data["Category"] = category_link.text.strip() if category_link else value
                                print(f"Category found on page {page_number}:", company_data["Category"])
                            elif label_text == "Based in":
                                company_data["Based in"] = value
                                print(f"Based in found on page {page_number}:", company_data["Based in"])
                            elif label_text == "Tags":
                                company_data["Tags"] = value
                                print(f"Tags found on page {page_number}:", company_data["Tags"])
                            elif label_text == "Founded":
                                company_data["Founded"] = value
                                print(f"Founded found on page {page_number}:", company_data["Founded"])
                        else:
                            print(f"Value for {label_text} on page {page_number} is empty")
                    else:
                        print(f"Label element not found on page {page_number}")

                all_companies_data.append(company_data)

        except requests.exceptions.RequestException as e:
            print(f"An error occurred fetching page {page_number}: {e}")

    return all_companies_data

if __name__ == "__main__":
    start_url = "https://www.eu-startups.com/directory/?wpbdp_sort=field-1"
    max_pages_to_scrape = 10  # Set the maximum number of pages you want to scrape here
    all_data = scrape_company_data(start_url, max_pages_to_scrape)

    if all_data:
        print("\nAll Scraped Data:", all_data)
        df = pd.DataFrame(all_data)
        df.to_csv("company_data.csv", index=False, encoding="utf-8", mode='w', header=True)
        print("Data saved to company_data.csv")
    else:
        print("Failed to scrape company data.")