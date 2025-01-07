import os
import csv
import json
import requests
from bs4 import BeautifulSoup

# Define the URL base and maximum page number
base_url = 'https://www.eu-startups.com/directory/?wpbdp_sort=field-1'
max_page_number = 15  # Adjust this as needed

# Define paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, 'data')
data_file = os.path.join(data_dir, 'eu_ai_companies.csv')
datapackage_file = os.path.join(data_dir, 'datapackage.json')

# Define the header for the CSV file
header = ['Name', 'Category', 'Based in', 'Tags', 'Founded']

# Ensure the directory for the file exists
def ensure_directory_exists(filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

# Create a default datapackage
def create_default_datapackage(filepath):
    default_structure = {
        "title": "EU AI Companies",
        "name": "eu-ai-companies",
        "description": "This Data Package contains information about EU AI companies.",
        "sources": [{"name": "eu-startups.com", "path": base_url, "title": "EU Startups Directory"}],
        "contributors": [{"name": "Your Name", "role": "maintainer"}],  # Replace with your name
        "licenses": [{"name": "CC0-1.0", "path": "https://creativecommons.org/publicdomain/zero/1.0/", "title": "Creative Commons Zero v1.0 Universal"}],
        "resources": [{"name": "eu_ai_companies.csv", "path": "data/eu_ai_companies.csv", "mediatype": "text/csv", "bytes": 0,
                       "schema": {"fields": [{"name": "Name", "type": "string"}, {"name": "Category", "type": "string"},
                                           {"name": "Based in", "type": "string"}, {"name": "Tags", "type": "string"},
                                           {"name": "Founded", "type": "string"}]}}],
        "collection": "business-data"
    }
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(default_structure, file, indent=2)

# Scrape data and update the CSV file
def update_dataset():
    ensure_directory_exists(data_file)
    all_companies_data = []

    for page_number in range(1, max_page_number + 1):
        if page_number == 1:
            page_url = base_url
        else:
            page_url = f"https://www.eu-startups.com/directory/page/{page_number}/?wpbdp_sort=field-1"

        print(f"Scraping page {page_number}: {page_url}")

        try:
            response = requests.get(page_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            listing_elements = soup.find_all("div", class_="wpbdp-listing")

            if not listing_elements:
                print(f"No listings found on page {page_number}.")
                continue

            for listing in listing_elements:
                company_data = {key: None for key in header}

                company_title = listing.select_one(".listing-title h3 a")
                if company_title:
                    company_data["Name"] = company_title.text.strip()

                detail_elements = listing.find_all("div", class_="wpbdp-field-display")
                for element in detail_elements:
                    label_element = element.find("span", class_="field-label")

                    if label_element:
                        label_text = label_element.text.strip().replace(":", "").replace(u'\xa0', u' ')
                        value_element = element.find("div", class_="value")

                        if value_element and value_element.text.strip():
                            value = value_element.text.strip()
                            if label_text in company_data:
                                if label_text == "Category":
                                    category_link = value_element.find("a")
                                    company_data["Category"] = category_link.text.strip() if category_link else value
                                else:
                                    company_data[label_text] = value

                all_companies_data.append(company_data)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from {page_url}: {e}")
            continue

    try:
        with open(data_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=header)
            writer.writeheader()
            writer.writerows(all_companies_data)
        print(f"CSV file '{data_file}' updated successfully.")
    except Exception as e:
        print(f"Error writing to CSV file '{data_file}': {e}")

# Update the datapackage with the file size
def update_byte_datapackage():
    ensure_directory_exists(datapackage_file)

    if not os.path.exists(datapackage_file):
        create_default_datapackage(datapackage_file)

    try:
        file_stats = os.stat(data_file)
        file_size = file_stats.st_size

        with open(datapackage_file, 'r', encoding='utf-8') as file:
            data_json = json.load(file)

        data_json['resources'][0]['bytes'] = int(file_size)

        with open(datapackage_file, 'w', encoding='utf-8') as file:
            json.dump(data_json, file, indent=2)

        print(f"Datapackage '{datapackage_file}' updated successfully.")
    except Exception as e:
        print(f"Error updating datapackage '{datapackage_file}': {e}")

# Main entry point
if __name__ == '__main__':
    update_dataset()
    update_byte_datapackage()