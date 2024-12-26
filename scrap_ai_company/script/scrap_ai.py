import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import json

class ResumableScraper:
    def __init__(self):
        self.setup_chrome_options()
        self.setup_paths()
        self.header = ["Name", "Description", "Founded", "Business Model", "Employees", 
                      "Funding Stage", "Total Raised", "Tags"]
        
    def setup_chrome_options(self):
        """Setup Chrome options to prevent sleep"""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("detach", True)  # Keep browser open
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--power-save-mode=false")  # Prevent sleep mode
        self.chrome_options = chrome_options
        
    def setup_paths(self):
        """Setup file paths"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(base_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.data_file = os.path.join(self.data_dir, 'ai_companies_startupnation.csv')
        self.progress_file = os.path.join(self.data_dir, 'scraping_progress.json')
        
    def initialize_driver(self):
        """Initialize the Chrome driver"""
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
        self.wait = WebDriverWait(self.driver, 120)
        
    def load_progress(self):
        """Load previous progress if exists"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)
            return progress.get('page_num', 1), progress.get('data', [])
        return 1, []
        
    def save_progress(self, page_num, data):
        """Save current progress"""
        with open(self.progress_file, 'w') as f:
            json.dump({'page_num': page_num, 'data': data}, f)
        # Also save to CSV as backup
        df = pd.DataFrame(data, columns=self.header)
        df.to_csv(self.data_file, index=False, quotechar='"')
        print(f"Progress saved. Current page: {page_num}, Companies collected: {len(data)}")
            
    def extract_company_data(self, company):
        """Extract data from a single company element"""
        try:
            name_element = company.find_element(By.CSS_SELECTOR, ".company-name")
            name = name_element.text.strip().replace("\n", " ")

            description_element = company.find_elements(By.CSS_SELECTOR, ".table-row-item")
            description = description_element[0].text.strip().replace("\n", " ") if description_element else ""

            founded = description_element[1].text.strip() if len(description_element) > 1 else "N/A"
            business_model = description_element[2].text.strip() if len(description_element) > 2 else "N/A"
            employees = description_element[3].text.strip() if len(description_element) > 3 else "N/A"
            funding_stage = description_element[4].text.strip() if len(description_element) > 4 else "N/A"
            total_raised = description_element[5].text.strip() if len(description_element) > 5 else "N/A"
            
            tags = [tag.text.strip() for tag in company.find_elements(By.CSS_SELECTOR, ".classification")]
            
            return [name, description, founded, business_model, employees, funding_stage, total_raised, ", ".join(tags)]
        except Exception as e:
            print(f"Error extracting company data: {e}")
            return ["N/A"] * 8

    def has_next_page(self):
        """Check if there is a next page"""
        try:
            next_span = self.driver.find_element(By.XPATH, "//span[text()='Next']")
            next_button = next_span.find_element(By.XPATH, "./..")
            if 'disabled' not in next_button.get_attribute('class'):
                return next_button
            return None
        except (NoSuchElementException, WebDriverException) as e:
            print(f"Error checking for next page: {e}")
            return None

    def wait_for_companies(self):
        """Wait for companies to load on the page"""
        try:
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[style='display:flex;']")))
            time.sleep(3)
            return True
        except TimeoutException:
            print("Timeout waiting for companies to load")
            return False

    def scrape(self):
        """Main scraping function"""
        url = "https://finder.startupnationcentral.org/startups/search?&days=30&alltags=artificial-intelligence&status=Active"
        
        try:
            # Initialize driver and load page
            self.initialize_driver()
            self.driver.get(url)
            
            # Wait for login
            print("Please log in manually, and then press Enter to continue...")
            input("Press Enter once you're logged in...")
            
            # Load previous progress if any
            page_num, all_data = self.load_progress()
            print(f"Resuming from page {page_num} with {len(all_data)} companies already collected")
            
            # If resuming, navigate to the correct page
            if page_num > 1:
                for _ in range(1, page_num):
                    next_button = self.has_next_page()
                    if next_button:
                        self.driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(3)
            
            while True:
                print(f"\nProcessing page {page_num}...")
                
                if not self.wait_for_companies():
                    break
                
                companies = self.driver.find_elements(By.CSS_SELECTOR, "a[style='display:flex;']")
                print(f"Found {len(companies)} companies on page {page_num}")
                
                for idx, company in enumerate(companies, 1):
                    company_data = self.extract_company_data(company)
                    all_data.append(company_data)
                    print(f"Processed company {idx}/{len(companies)}: {company_data[0]}")
                    
                    # Save progress every 5 companies
                    if idx % 5 == 0:
                        self.save_progress(page_num, all_data)
                
                next_button = self.has_next_page()
                if next_button:
                    print(f"Navigating to page {page_num + 1}")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", next_button)
                    page_num += 1
                    time.sleep(3)
                    # Save progress after each page
                    self.save_progress(page_num, all_data)
                else:
                    print("Reached last page")
                    break
                    
        except Exception as e:
            print(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Final save
            if all_data:
                self.save_progress(page_num, all_data)
                print(f"\nScraping completed or paused. Scraped {len(all_data)} companies across {page_num} pages.")
            
            try:
                self.driver.quit()
            except:
                pass

if __name__ == "__main__":
    scraper = ResumableScraper()
    scraper.scrape()