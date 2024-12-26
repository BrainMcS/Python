from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

# Set up WebDriver with webdriver-manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# Open the website
url = "https://finder.startupnationcentral.org/startups/search?&days=30&alltags=artificial-intelligence&status=Active"
driver.get(url)

# Wait for you to log in manually
print("Please log in manually, and then press Enter to continue...")
input("Press Enter once you're logged in...")

# Wait for the data to load after login
wait = WebDriverWait(driver, 120)  # Increase timeout to 120 seconds
try:
    # Wait for the company data to be visible
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".company")))
    print("Page loaded successfully.")
except Exception as e:
    print(f"Error loading page: {e}")

# Extract headers dynamically from the page
headers = ["Name", "Description", "Founded", "Business Model", "Employees", "Funding Stage", "Total Raised", "Tags"]
print("Extracted Headers:", headers)

# Extract company data
data = []
companies = driver.find_elements(By.CSS_SELECTOR, "a[style='display:flex;']")  # Extract each company card
print(f"Found {len(companies)} companies.")  # Print number of companies found

for company in companies:
    row = []
    try:
        # Extract company name (without extra description)
        name_element = company.find_element(By.CSS_SELECTOR, ".company-name")
        name = name_element.text.strip().replace("\n", " ")  # Replace newline with a space

        # Extract description only if it's separate and doesn't repeat the name
        description = ""
        description_element = company.find_elements(By.CSS_SELECTOR, ".table-row-item")
        if description_element:
            description = description_element[0].text.strip().replace("\n", " ")  # Replace newline with a space
        
        # Use name if description is not present
        full_name = f"{name} - {description}" if description else name

        # Extract other company data
        founded = description_element[1].text.strip() if len(description_element) > 1 else "N/A"
        business_model = description_element[2].text.strip() if len(description_element) > 2 else "N/A"
        employees = description_element[3].text.strip() if len(description_element) > 3 else "N/A"
        funding_stage = description_element[4].text.strip() if len(description_element) > 4 else "N/A"
        total_raised = description_element[5].text.strip() if len(description_element) > 5 else "N/A"
        
        # Extract tags (e.g., artificial-intelligence, climate-tech)
        tags = [tag.text.strip() for tag in company.find_elements(By.CSS_SELECTOR, ".classification")]

        # Store the data in a row
        row.extend([name, description, founded, business_model, employees, funding_stage, total_raised, ", ".join(tags)])
        data.append(row)
    except Exception as e:
        print(f"Error extracting data for company: {e}")
        row = ["N/A"] * len(headers)  # Default if no data is available for that field
        data.append(row)

# Check if data was extracted successfully
if data:
    # Save the data to a CSV
    df = pd.DataFrame(data, columns=headers)
    df.to_csv("ai_companies_startupnation.csv", index=False, quotechar='"')
    print("Scraping completed. Data saved to ai_companies_startupnation.csv")
else:
    print("No data extracted.")

# Close the browser
driver.quit()
