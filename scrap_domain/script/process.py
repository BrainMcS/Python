import os
import csv
import json
import requests
from bs4 import BeautifulSoup

# Define the URL from which to scrape the data
url = 'https://www.iana.org/domains/root/db'

# Define the base directory where the 'data' folder should be located (outside the script folder)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Get the parent directory of the script
data_dir = os.path.join(base_dir, 'data')  # Create 'data' folder directly in the project root directory
data = os.path.join(data_dir, 'top-level-domain-names.csv')
datapackage = os.path.join(data_dir, 'datapackage.json')

# Define the header for the CSV file
header = ['Domain', 'Type', 'Sponsoring Organization']

# Ensure the directory for the file exists
def ensure_directory_exists(filepath):
    """Ensure the directory for the given filepath exists."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)  # Creates the 'data' folder if it doesn't exist

# Create a default datapackage if it doesn't exist
def create_default_datapackage(filepath):
    """Create a default datapackage.json file if it doesn't exist."""
    default_structure = {
        "title": "Top Level Domain Names",
        "name": "top-level-domain-names",
        "description": "This Data Package contains the delegation details of top-level domains",
        "sources": [
            {
                "name": "The Internet Assigned Numbers Authority (IANA)",
                "path": "http://www.iana.org/domains/root/db",
                "title": "The Internet Assigned Numbers Authority (IANA)"
            }
        ],
        "contributors": [
            {
                "name": "Brian Nickson",
                "role": "maintainer"
            }
        ],
        "licenses": [
            {
                "name": "ODC-PDDL-1.0",
                "path": "http://opendatacommons.org/licenses/pddl/",
                "title": "Open Data Commons Public Domain Dedication and License v1.0"
            }
        ],
        "resources": [
            {
                "name": "top-level-domain-names.csv",
                "path": "data/top-level-domain-names.csv",
                "mediatype": "text/csv",
                "bytes": 0,  # Placeholder value for now
                "schema": {
                    "fields": [
                        {
                            "name": "Domain",
                            "type": "string"
                        },
                        {
                            "name": "Type",
                            "type": "string"
                        },
                        {
                            "name": "Sponsoring Organisation",
                            "type": "string"
                        }
                    ]
                }
            }
        ],
        "collection": "reference-data"
    }
    with open(filepath, 'w') as file:
        json.dump(default_structure, file, indent=2)

# Scrape data and update the CSV file
def update_dataset():
    """Scrape data from IANA and write it to a CSV file."""
    ensure_directory_exists(data)  # Ensure the 'data' directory exists

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for HTTP issues
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find("table", {"class": "iana-table"})
    if not table:
        print("Error: Unable to find the table in the HTML response.")
        return

    rows = [header]
    for row in table.find_all('tr'):
        row_data = [cell.text.strip() for cell in row.find_all('td') if cell.text.strip()]
        if row_data:  # Only add non-empty rows
            rows.append(row_data)

    try:
        with open(data, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
        print(f"CSV file '{data}' updated successfully.")
    except Exception as e:
        print(f"Error writing to CSV file '{data}': {e}")

# Update the datapackage with the file size
def update_byte_datapackage():
    """Update the 'bytes' field in datapackage.json with the size of the CSV file."""
    ensure_directory_exists(datapackage)  # Ensure the 'data' directory exists

    # Create datapackage.json if it doesn't exist
    if not os.path.exists(datapackage):
        create_default_datapackage(datapackage)

    try:
        # Get data file byte size
        file_stats = os.stat(data)
        file_size = file_stats.st_size

        # Load the existing datapackage.json
        with open(datapackage, 'r') as file:
            data_json = json.load(file)

        # Update the bytes field in the resources section
        data_json['resources'][0]['bytes'] = int(file_size)

        # Write the updated datapackage.json
        with open(datapackage, 'w') as file:
            json.dump(data_json, file, indent=2)

        print(f"Datapackage '{datapackage}' updated successfully.")
    except Exception as e:
        print(f"Error updating datapackage '{datapackage}': {e}")

# Main entry point
if __name__ == '__main__':
    update_dataset()
    update_byte_datapackage()
