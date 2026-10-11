from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_sql(user_question, schema_text):
    prompt = f"""You are a SQLite expert. Given this database schema:

{schema_text}

Convert the user's question into ONE valid SQLite SELECT query.
Rules:
- Return ONLY the raw SQL query — no explanation, no markdown, no backticks.
- Only SELECT statements — never INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE.
- Always include a LIMIT 100 unless the question asks for an aggregate (COUNT, SUM, AVG) with no row-level output.
- Use table/column names EXACTLY as given in the schema.
- This is SQLite, NOT MySQL: for dates use strftime (e.g. strftime('%Y', Order_Date), strftime('%Y-%m', Order_Date)). Never use YEAR(), MONTH(), DATE_FORMAT(), DATE_SUB(), or ILIKE.
- Always join order_details to orders ON order_details.Order_Key = orders.Order_Key (never on Order_ID).
- Count orders with COUNT(DISTINCT Order_ID).
- Sales, Profit and Discount are integers: for ratios/percentages multiply by 100.0 (e.g. SUM(Profit)*100.0/SUM(Sales)) to avoid integer division.
- Discount is a 0/1 flag. "Average discount" = ROUND(AVG(Discount)*100,1) as a percentage of lines discounted.
- Data spans 2014-2017, so "latest year" means 2017.

Question: {user_question}
SQL:"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}]
    )
    sql = response.choices[0].message.content.strip()
    return sql.replace("```sql", "").replace("```", "").strip()