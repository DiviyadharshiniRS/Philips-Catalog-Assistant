
import pandas as pd
import sqlite3
from pathlib import Path

# Project directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "database"

DB_DIR.mkdir(exist_ok=True)

DB_PATH = DB_DIR / "catalog.db"

# Company files
companies = {
    "CircuitNova": DATA_DIR / "electronics_catalog.xlsx",
    "Hearthwell": DATA_DIR / "home_appliances_catalog.xlsx"
}

sheets = [
    "products",
    "where_we_sell",
    "product_validity",
    "price_list",
    "third_party_parts"
]

# Create SQLite database
conn = sqlite3.connect(DB_PATH)

try:
    for company, filepath in companies.items():

        if not filepath.exists():
            raise FileNotFoundError(f"Missing file: {filepath}")

        print(f"\nLoading {company}...")

        for sheet in sheets:

            df = pd.read_excel(filepath, sheet_name=sheet)

            # Add company identifier
            df.insert(0, "company", company)

            # Store in SQLite
            table_name = f"{company.lower()}_{sheet}"

            df.to_sql(
                table_name,
                conn,
                if_exists="replace",
                index=False
            )

            print(f"  {table_name}: {len(df)} rows loaded")

    print("\nDatabase created successfully!")

    # Verify tables
    tables = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table'",
        conn
    )

    print("\nTables in database:")
    print(tables.to_string(index=False))

finally:
    conn.close()
