import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
TASKS_DB_ID = os.getenv("TASKS_DB_ID")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

url = f"https://api.notion.com/v1/databases/{TASKS_DB_ID}/query"

print("🔍 Пытаюсь отправить запрос:")
print("URL:", url)
print("DB ID length:", len(TASKS_DB_ID))

print("\n=== ОТВЕТ NOTION ===")
res = requests.post(url, headers=headers, json={})
print("Status code:", res.status_code)
print("Raw response:")
print(res.text)
