import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "superstore.db")

def get_db_connection():
    # read-only: the app can never modify the database
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False)

def get_schema_description():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    schema_text = ""
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()  # (cid, name, type, notnull, default, pk)
        schema_text += f"\nTable: {table}\n"
        for col in columns:
            schema_text += f"  - {col[1]} ({col[2]})\n"
        cursor.execute(f"SELECT * FROM {table} LIMIT 2")
        schema_text += f"  Sample rows: {cursor.fetchall()}\n"

    schema_text += """
Relationships and notes:
- orders.Order_Key is the unique key of orders. Join order_details to orders ON order_details.Order_Key = orders.Order_Key (NEVER join on Order_ID: it is not unique in orders).
- orders.Customer_ID = customers.Customer_ID ; order_details.Product_ID = products.Product_ID
- Order_ID is the business order number; count orders with COUNT(DISTINCT Order_ID).
- Order_Date and Ship_Date are TEXT in 'YYYY-MM-DD' format (data spans 2014-2017).
- Discount is only 0 or 1 (a flag, not a percentage). Sales and Profit are integers.
- Segment values: Consumer, Corporate, Home Office. Region values: East, West, Central, South.
- Category values: Furniture, Office Supplies, Technology.
"""
    conn.close()
    return schema_text
