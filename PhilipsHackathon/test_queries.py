
import sqlite3
import pandas as pd

DB_PATH = "database/catalog.db"

conn = sqlite3.connect(DB_PATH)

# --------------------------------------------------
# QUERY 1: Can we quote EO-10001 in Denmark?
# --------------------------------------------------

print("\n" + "=" * 65)
print("1. QUOTE ELIGIBILITY: EO-10001 IN DENMARK")
print("=" * 65)

query1 = """
SELECT
    w.product_id,
    w.option_id,
    w.has_price,
    w.quotable_countries,
    p.country,
    p.currency,
    p.price_status,
    p.cost_price,
    p.list_price,
    p.is_npi
FROM circuitnova_where_we_sell w
LEFT JOIN circuitnova_price_list p
    ON w.option_id = p.option_id
    AND p.country = 'DK'
WHERE w.option_id = 'EO-10001'
AND (
    w.quotable_countries LIKE 'DK'
    OR w.quotable_countries LIKE 'DK;%'
    OR w.quotable_countries LIKE '%;DK'
    OR w.quotable_countries LIKE '%;DK;%'
)
"""

result1 = pd.read_sql_query(query1, conn)

print(result1.to_string(index=False))

if result1.empty:
    print("Result: No matching sales record found.")
else:
    print("\nDecision:")
    print("Check the price status and NPI exception before quoting.")


# --------------------------------------------------
# QUERY 2: Is EP-1023 export-controlled?
# --------------------------------------------------

print("\n" + "=" * 65)
print("2. EXPORT CONTROL: EP-1023")
print("=" * 65)

query2 = """
SELECT DISTINCT
    product_id,
    product_name,
    export_class,
    country_of_origin,
    quotable_countries
FROM circuitnova_products
WHERE product_id = 'EP-1023'
"""

result2 = pd.read_sql_query(query2, conn)

print(result2.to_string(index=False))

if result2.empty:
    print("Result: Product not found.")
else:
    export_class = result2.iloc[0]["export_class"]

    if export_class in ["EC-1", "EC-2"]:
        print(f"Result: YES - Export controlled ({export_class})")
    else:
        print(f"Result: NO - Not controlled ({export_class})")


# --------------------------------------------------
# QUERY 3: Expired products still on sale
# --------------------------------------------------

print("\n" + "=" * 65)
print("3. EXPIRED PRODUCTS STILL ON SALE")
print("=" * 65)

for company in ["circuitnova", "hearthwell"]:

    query3 = f"""
    SELECT DISTINCT
        v.product_id,
        v.product_name,
        v.valid_to
    FROM {company}_product_validity v
    WHERE date(v.valid_to) < date('now')
    AND EXISTS (
        SELECT 1
        FROM {company}_where_we_sell w
        WHERE w.product_id = v.product_id
    )
    ORDER BY v.valid_to
    """

    result3 = pd.read_sql_query(query3, conn)

    print(f"\n{company.upper()}")
    print("Expired products still on sale:", len(result3))
    print(result3.to_string(index=False))


conn.close()

print("\nAll three SQL tests completed.")
