from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def format_answer(user_question, columns, rows):
    data_preview = f"Columns: {columns}\nRows: {rows[:20]}"
    prompt = f"""The user asked: "{user_question}"

Query result:
{data_preview}

Write a short, clear, natural-language answer (2-4 sentences) summarizing this result."""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()