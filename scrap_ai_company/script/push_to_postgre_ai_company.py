import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import csv
import unicodedata

load_dotenv()  # Load environment variables from .env

def clean_and_validate_data(df):
    """Cleans and validates data before database insertion."""
    cleaned_data = []
    for index, row in df.iterrows():
        cleaned_row = {}
        for col_name, item in row.items():
            if pd.isna(item):
                cleaned_row[col_name] = None
                continue

            if isinstance(item, str):
                item = item.strip()
                item = item.replace("'", "''")  # Escape single quotes
                item = item[:255] #Truncate to avoid string data right truncation
                item = "".join(ch for ch in item if unicodedata.category(ch)[0]!="C") #Remove control characters
                try:
                    item = item.encode('utf-8').decode('utf-8') #Ensure utf-8 encoding
                except UnicodeDecodeError:
                    item = "" #Replace with empty string if encoding fails
            elif col_name == 'founded':  # Example numeric validation
                try:
                    item = int(item)
                except (ValueError, TypeError):
                    print(f"Invalid 'founded' value (index {index}): {item}")
                    item = None #Set to None to avoid errors
            elif col_name in ('Employees', 'Total Raised'): #Example of string number validation
                try:
                    item = item.replace("$", "").replace("M", "000000").replace("K", "000") #Clean the string
                    item = int(float(item)) #Convert to int
                except (ValueError, TypeError):
                    print(f"Invalid 'Employees' or 'Total Raised' value (index {index}): {item}")
                    item = None #Set to None to avoid errors
            cleaned_row[col_name] = item
        cleaned_data.append(cleaned_row)
    return cleaned_data

def upload_cleaned_data_to_postgres(cleaned_data, table_name, db_config):
    """Uploads pre-cleaned data to PostgreSQL."""
    conn = None
    try:
        conn = psycopg2.connect(**db_config)
        conn.autocommit = False
        cursor = conn.cursor()

        if cleaned_data:
            columns = ", ".join([f'"{col}"' for col in cleaned_data[0].keys()])
            placeholders = ", ".join(["%s"] * len(cleaned_data[0].values()))
            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

            for index, row_data in enumerate(cleaned_data):
                row_tuple = tuple(row_data.values())
                try:
                    sql = cursor.mogrify(insert_query, row_tuple).decode('utf-8')
                    print(f"Executing SQL: {sql}")
                    cursor.execute(insert_query, row_tuple)
                    conn.commit()
                except psycopg2.Error as e:
                    print(f"Error inserting row (index {index}): {e}")
                    conn.rollback()
                    with open("error_log.csv", "a", newline="", encoding="utf-8") as error_file:
                        writer = csv.writer(error_file)
                        writer.writerow([index, e, list(row_data.values())])
                    break
        else:
            print("No data to insert after cleaning.")

        print(f"Data uploaded to table '{table_name}' successfully on database {db_config['database']}.")
    except psycopg2.Error as err:
        print(f"Database connection or other top-level error: {err}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    csv_file = "scrap_ai_company/data/ai_companies_startupnation.csv"
    table_name = "ai_companies"

    db_config = {
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": os.getenv("POSTGRES_HOST"),
        "database": os.getenv("POSTGRES_DB"),
        "port": os.getenv("POSTGRES_PORT", "5432")
    }
    conn_string = f"dbname={db_config['database']} user={db_config['user']} password={db_config['password']} host={db_config['host']} port={db_config['port']}"
    print(f"Connection String: {conn_string}")

    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
        df.insert(0, 'id', range(1, 1 + len(df)))
        cleaned_data = clean_and_validate_data(df)

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT to_regclass('{table_name}')")
            table_exists = cursor.fetchone()[0]
            if not table_exists:
                if cleaned_data:
                    columns = ", ".join([f'"{col}" VARCHAR(255)' for col in cleaned_data[0].keys()])
                    create_table_query = f"""
                    CREATE TABLE {table_name} (
                        {columns},
                        PRIMARY KEY (id)
                    )
                    """
                    cursor.execute(create_table_query)
                    conn.commit()
                    print(f"Table {table_name} created.")
                else:
                    print("No data to create a table")
            else:
                print(f"Table {table_name} already exists.")
        except psycopg2.Error as e:
            print(f"Error checking or creating table: {e}")
            conn.rollback()
        finally:
            conn.close()

        upload_cleaned_data_to_postgres(cleaned_data, table_name, db_config)

    except (pd.errors.ParserError, FileNotFoundError) as e:
        print(f"Error reading CSV file: {e}")
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")