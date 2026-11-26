
import sqlite3

DB_PATH = "database/catalog.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Validate company name before using it in table names
def get_prefix(company):
    allowed = {
        "circuitnova": "circuitnova",
        "hearthwell": "hearthwell"
    }

    prefix = allowed.get(company.lower())

    if prefix is None:
        raise ValueError("Unknown company: " + company)

    return prefix


# Execute SQL and capture actual execution details
def execute_query(conn, query, parameters, tables):

    rows = conn.execute(query, parameters).fetchall()

    query_details = {
        "sql_query": query.strip(),
        "parameters": list(parameters),
        "database_tables": tables,
        "rows_returned": len(rows)
    }

    return rows, query_details


# TOOL 1: Check quotation eligibility
def check_quote(option_id, country, company="CircuitNova"):

    prefix = get_prefix(company)

    country_codes = {
        "denmark": "DK",
        "india": "IN",
        "germany": "DE",
        "france": "FR",
        "united states": "US",
        "usa": "US",
        "united kingdom": "GB",
        "uk": "GB"
    }

    country_code = country_codes.get(country.lower(), country.upper())

    conn = get_connection()

    query = f"""
    SELECT
        w.product_id,
        w.option_id,
        w.has_price,
        p.country,
        p.currency,
        p.price_status,
        p.cost_price,
        p.list_price,
        p.is_npi
    FROM {prefix}_where_we_sell w
    LEFT JOIN {prefix}_price_list p
        ON w.option_id = p.option_id
        AND p.country = ?
    WHERE w.option_id = ?
    AND (
        ';' || w.quotable_countries || ';'
    ) LIKE ?
    """

    parameters = (
        country_code,
        option_id,
        f"%;{country_code};%"
    )

    try:
        rows, query_details = execute_query(
            conn,
            query,
            parameters,
            [f"{prefix}_where_we_sell", f"{prefix}_price_list"]
        )
    finally:
        conn.close()

    evidence = [dict(row) for row in rows]

    if not evidence:
        return {
            "decision": "NOT FOUND",
            "reason": "No matching sales record found",
            "country_code_checked": country_code,
            "evidence": [],
            "query_details": query_details
        }

    for row in evidence:

        if row["has_price"] != "Yes":
            return {
                "decision": "NOT QUOTABLE",
                "reason": "Sales record does not indicate that a price is available",
                "evidence": evidence,
                "query_details": query_details
            }

        if row["price_status"] is None:
            return {
                "decision": "NOT QUOTABLE",
                "reason": "Required price record is missing",
                "evidence": evidence,
                "policy": "Pricing Policy 2.1 and 2.2",
                "query_details": query_details
            }

        if row["price_status"] == "Cost and list price missing":

            if row["is_npi"] != "Yes":
                return {
                    "decision": "NOT QUOTABLE",
                    "reason": "Cost and list price missing; NPI is No",
                    "evidence": evidence,
                    "policy": "Pricing Policy 3.1 and 3.3",
                    "query_details": query_details
                }

            continue

        if row["price_status"] == "List price not refreshed":
            return {
                "decision": "NOT QUOTABLE",
                "reason": "List price not refreshed",
                "evidence": evidence,
                "policy": "Pricing Policy 4.1",
                "query_details": query_details
            }

        if row["price_status"] == "Available":

            if row["currency"] is None:
                return {
                    "decision": "NOT QUOTABLE",
                    "reason": "Currency missing",
                    "evidence": evidence,
                    "policy": "Pricing Policy 6.1",
                    "query_details": query_details
                }

            cost = row["cost_price"]
            price = row["list_price"]

            if cost is None or price is None:
                return {
                    "decision": "NOT QUOTABLE",
                    "reason": "Price data incomplete",
                    "evidence": evidence,
                    "query_details": query_details
                }

            if cost > 0 and price < 1.2 * cost:
                return {
                    "decision": "NOT QUOTABLE",
                    "reason": "Minimum 20% margin not met",
                    "evidence": evidence,
                    "policy": "Pricing Policy 5.1",
                    "query_details": query_details
                }

    return {
        "decision": "PRICE CHECK PASSED",
        "reason": "No pricing violation detected",
        "evidence": evidence,
        "query_details": query_details
    }


# TOOL 2: Check export classification
def check_export(product_id, company="CircuitNova"):

    prefix = get_prefix(company)
    conn = get_connection()

    query = f"""
    SELECT DISTINCT
        product_id,
        product_name,
        export_class,
        country_of_origin
    FROM {prefix}_products
    WHERE product_id = ?
    """

    parameters = (product_id,)

    try:
        rows, query_details = execute_query(
            conn,
            query,
            parameters,
            [f"{prefix}_products"]
        )
    finally:
        conn.close()

    if not rows:
        return {
            "decision": "NOT FOUND",
            "query_details": query_details
        }

    product = dict(rows[0])

    controlled = product["export_class"] in ["EC-1", "EC-2"]

    return {
        "decision": "CONTROLLED" if controlled else "NOT CONTROLLED",
        "evidence": product,
        "policy": "Export Control Policy 2.2",
        "query_details": query_details
    }


# TOOL 3: Find expired products still on sale
def find_expired_products(company="CircuitNova"):

    prefix = get_prefix(company)
    conn = get_connection()

    query = f"""
    SELECT DISTINCT
        v.product_id,
        v.product_name,
        v.valid_to
    FROM {prefix}_product_validity v
    WHERE date(v.valid_to) < date('now')
    AND EXISTS (
        SELECT 1
        FROM {prefix}_where_we_sell w
        WHERE w.product_id = v.product_id
    )
    ORDER BY v.valid_to
    """

    parameters = ()

    try:
        rows, query_details = execute_query(
            conn,
            query,
            parameters,
            [
                f"{prefix}_product_validity",
                f"{prefix}_where_we_sell"
            ]
        )
    finally:
        conn.close()

    products = [dict(row) for row in rows]

    return {
        "company": company,
        "count": len(products),
        "products": products,
        "policy": "Product Lifecycle Policy 3.1 and 3.2",
        "query_details": query_details
    }


# Quick test
if __name__ == "__main__":

    print("\n--- QUOTE CHECK ---")
    print(check_quote("EO-10001", "Denmark"))

    print("\n--- EXPORT CHECK ---")
    print(check_export("EP-1023"))

    print("\n--- EXPIRED PRODUCTS ---")
    print(find_expired_products("CircuitNova"))

    print("\n--- HEARTHWELL EXPIRED PRODUCTS ---")
    print(find_expired_products("Hearthwell"))
