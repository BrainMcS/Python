import os
import csv
import json
import requests
from bs4 import BeautifulSoup

# Define the base directory where the 'data' folder should be located (outside the script folder)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Get the parent directory of the script
data_dir = os.path.join(base_dir, 'data')  # Create 'data' folder directly in the project root directory
data = os.path.join(data_dir, 'top-level-domain-names.csv')
datapackage = os.path.join(data_dir, 'datapackage.json')

# Dynamic URL (can be changed or passed as a parameter)
url = 'https://www.iana.org/domains/root/db'

# Ensure the directory for the file exists
def ensure_directory_exists(filepath):
    """Ensure the directory for the given filepath exists."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)  # Creates the 'data' folder if it doesn't exist

# Create a dynamic datapackage if it doesn't exist
def create_default_datapackage(filepath, header, url, title="Top Level Domain Names", description="This Data Package contains the delegation details of top-level domains", source_name="The Internet Assigned Numbers Authority (IANA)", contributor_name="Brian Nickson", license_name="ODC-PDDL-1.0"):
    """Create a dynamic datapackage.json file if it doesn't exist."""
    
    # Dynamically build the datapackage structure
    default_structure = {
        "title": title,
        "name": title.lower().replace(" ", "-"),
        "description": description,
        "sources": [
            {
                "name": source_name,
                "path": url,
                "title": source_name
            }
        ],
        "contributors": [
            {
                "name": contributor_name,
                "role": "maintainer"
            }
        ],
        "licenses": [
            {
                "name": license_name,
                "path": "http://opendatacommons.org/licenses/pddl/",
                "title": "Open Data Commons Public Domain Dedication and License v1.0"
            }
        ],
        "resources": [
            {
                "name": f"{title.lower().replace(' ', '-')}.csv",  # Dynamically generate CSV file name based on title
                "path": f"data/{title.lower().replace(' ', '-')}.csv",
                "mediatype": "text/csv",
                "bytes": 0,  # Placeholder value for now
                "schema": {
                    "fields": [{"name": field, "type": "string"} for field in header]
                }
            }
        ],
        "collection": "reference-data"
    }

    with open(filepath, 'w') as file:
        json.dump(default_structure, file, indent=2)

# Scrape data and return the header and rows
def scrape_data(url):
    """Scrape data from the given URL and return the HTML table rows and header."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for HTTP issues
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find("table", {"class": "iana-table"})
    if not table:
        print("Error: Unable to find the table in the HTML response.")
        return None, None

    # Extract headers dynamically by looking for the table's header row (<th>)
    header_row = table.find_all('th')
    header = [th.text.strip() for th in header_row] if header_row else []

    # Extract data rows (content under <td>)
    rows = []
    for row in table.find_all('tr'):
        row_data = [cell.text.strip() for cell in row.find_all('td') if cell.text.strip()]
        if row_data:  # Only add non-empty rows
            rows.append(row_data)

    return header, rows

def save_to_csv(data, header, filepath):
    """Save the scraped data to a CSV file."""
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(header)  # Write dynamic header
            writer.writerows(data)
        print(f"CSV file '{filepath}' updated successfully.")
    except Exception as e:
        print(f"Error writing to CSV file '{filepath}': {e}")

def update_datapackage(filepath, csv_filepath, header, url, title="Top Level Domain Names", contributor_name="Brian Nickson"):
    """Update the 'bytes' field in datapackage.json with the size of the CSV file."""
    ensure_directory_exists(filepath)

    if not os.path.exists(filepath):
        create_default_datapackage(filepath, header, url, title, contributor_name)

    try:
        # Get data file byte size
        file_stats = os.stat(csv_filepath)
        file_size = file_stats.st_size

        # Load the existing datapackage.json
        with open(filepath, 'r') as file:
            data_json = json.load(file)

        # Update the bytes field in the resources section
        data_json['resources'][0]['bytes'] = int(file_size)
        # Update the schema with dynamic header
        data_json['resources'][0]['schema']['fields'] = [{"name": field, "type": "string"} for field in header]

        # Write the updated datapackage.json
        with open(filepath, 'w') as file:
            json.dump(data_json, file, indent=2)

        print(f"Datapackage '{filepath}' updated successfully.")
    except Exception as e:
        print(f"Error updating datapackage '{filepath}': {e}")

# Main function to update dataset
def update_dataset():
    """Main function to scrape data, save to CSV, and update the datapackage."""
    # Ensure the directory exists
    ensure_directory_exists(data)

    # Scrape the data from the URL and get dynamic header and rows
    header, rows = scrape_data(url)
    if not header or not rows:
        return  # Exit if scraping fails

    # Save the scraped data to a CSV file
    save_to_csv(rows, header, data)

    # Update the datapackage with the new CSV file size and dynamic header
    update_datapackage(datapackage, data, header, url)

# Run the script
if __name__ == '__main__':
    update_dataset()
