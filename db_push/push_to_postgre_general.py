import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import csv
import unicodedata

load_dotenv()

def clean_and_validate_data(df, numeric_cols=None, string_number_cols=None):
    """Cleans and validates data based on provided column types."""
    if numeric_cols is None:
        numeric_cols = []
    if string_number_cols is None:
        string_number_cols = []

    cleaned_data = []
    for index, row in df.iterrows():
        cleaned_row = {}
        for col_name, item in row.items():
            if pd.isna(item):
                cleaned_row[col_name] = None
                continue

            if isinstance(item, str):
                item = item.strip()
                item = item.replace("'", "''")
                item = item[:255]
                item = "".join(ch for ch in item if unicodedata.category(ch)[0] != "C")
                try:
                    item = item.encode('utf-8').decode('utf-8')
                except UnicodeDecodeError:
                    item = ""
            elif col_name in numeric_cols:
                try:
                    item = int(item)
                except (ValueError, TypeError):
                    print(f"Invalid '{col_name}' value (index {index}): {item}")
                    item = None
            elif col_name in string_number_cols:
                try:
                    item = item.replace("$", "").replace("M", "000000").replace("K", "000")
                    item = int(float(item))
                except (ValueError, TypeError):
                    print(f"Invalid '{col_name}' value (index {index}): {item}")
                    item = None
            cleaned_row[col_name] = item
        cleaned_data.append(cleaned_row)
    return cleaned_data

def create_table_if_not_exists(cursor, conn, table_name, columns):
    """Creates the table if it doesn't exist, inferring data types."""
    try:
        cursor.execute(f"SELECT to_regclass('{table_name}')")
        table_exists = cursor.fetchone()[0]
        if not table_exists:
            column_defs = []
            for col, example_value in columns.items():
                if isinstance(example_value, int):
                    col_type = "INTEGER"
                elif isinstance(example_value, float):
                    col_type = "NUMERIC"
                elif isinstance(example_value, str):
                    col_type = "VARCHAR(255)"
                else:
                    col_type = "TEXT" #Default is TEXT

                column_defs.append(f'"{col}" {col_type}')
            create_table_query = f"""
            CREATE TABLE {table_name} (
                id SERIAL PRIMARY KEY,
                {", ".join(column_defs)}
            )
            """
            cursor.execute(create_table_query)
            conn.commit()
            print(f"Table {table_name} created.")
        else:
            print(f"Table {table_name} already exists.")
    except psycopg2.Error as e:
        print(f"Error checking or creating table: {e}")
        conn.rollback()
        raise #Re-raise the exception to stop execution

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
    csv_file = "scrap_ai_company/data/ai_companies_startupnation.csv" #Change this to the path of your desired CSV file
    table_name = "ai_companies" #Change this to your desired table name
    numeric_columns = ['founded'] #Change this to the names of columns that should be numeric like date, age, etc.
    string_number_columns = ['Employees', 'Total Raised'] #Change this to the names of columns that should be numeric but are stored as strings like 2M, $5K, etc.

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
        cleaned_data = clean_and_validate_data(df, numeric_columns, string_number_columns)

        if cleaned_data:
            example_row = cleaned_data[0]
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            create_table_if_not_exists(cursor, conn, table_name, example_row)
            conn.close()

            upload_cleaned_data_to_postgres(cleaned_data, table_name, db_config)
        else:
            print("No data to process after cleaning.")

    except (pd.errors.ParserError, FileNotFoundError) as e:
        print(f"Error reading CSV file: {e}")
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")