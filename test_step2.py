from schema_utils import get_schema_description
from query_executor import execute_query

print(get_schema_description()[:900])
print(execute_query("SELECT COUNT(*), SUM(od.Sales), SUM(od.Profit) FROM order_details od JOIN orders o ON o.Order_Key=od.Order_Key"))
print(execute_query("SELECT strftime('%Y-%m', Order_Date) AS m, COUNT(*) FROM orders GROUP BY m LIMIT 3"))
try:
    execute_query("DROP TABLE orders")
except ValueError as e:
    print("blocked OK:", e)
    