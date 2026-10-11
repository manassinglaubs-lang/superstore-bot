import re
from schema_utils import get_db_connection

FORBIDDEN = ["insert", "update", "delete", "drop", "alter", "truncate", "create",
             "grant", "revoke", "attach", "detach", "pragma", "replace", "vacuum"]

def is_safe_query(sql):
    s = sql.strip().rstrip(";").strip()
    low = s.lower()
    if not (low.startswith("select") or low.startswith("with")):
        return False
    if ";" in s:                      # no multiple statements
        return False
    if re.search(r"\b(" + "|".join(FORBIDDEN) + r")\b", low):
        return False
    return True

def execute_query(sql):
    if not is_safe_query(sql):
        raise ValueError("Blocked: only safe SELECT queries are allowed.")
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql.strip().rstrip(";"))
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return columns, rows
    finally:
        conn.close()