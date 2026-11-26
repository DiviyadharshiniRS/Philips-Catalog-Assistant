
import sqlite3
import pandas as pd

DB_PATH = "database/catalog.db"

conn = sqlite3.connect(DB_PATH)

tables = [
    "circuitnova_products",
    "circuitnova_where_we_sell",
    "circuitnova_product_validity",
    "circuitnova_price_list",
    "hearthwell_products",
    "hearthwell_where_we_sell",
    "hearthwell_product_validity",
    "hearthwell_price_list"
]

for table in tables:
    print("\n" + "=" * 70)
    print("TABLE:", table)
    print("=" * 70)

    # Display column names
    schema = pd.read_sql_query(
        f"PRAGMA table_info({table})", conn
    )

    print("COLUMNS:")
    print(schema["name"].tolist())

    # Display sample records
    sample = pd.read_sql_query(
        f"SELECT * FROM {table} LIMIT 2", conn
    )

    print("\nSAMPLE DATA:")
    print(sample.to_string(index=False))

conn.close()
