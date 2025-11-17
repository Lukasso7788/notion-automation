import os
import requests
from dotenv import load_dotenv
from datetime import date

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DAILY_LOG_DB_ID = os.getenv("DAILY_LOG_DB_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

payload = {
    "parent": {"database_id": DAILY_LOG_DB_ID},
    "properties": {
        "Name": {"title": [{"text": {"content": "TEST ENTRY"}}]},
        "Date": {"date": {"start": date.today().isoformat()}},
        "Status vs plan": {"select": {"name": "On track"}},
        "Total tasks": {"number": 5},
        "Done tasks": {"number": 3},
        "Planned min": {"number": 120},
        "Actual min": {"number": 90},
        "Deep work min": {"number": 60},
        "Raw data (JSON)": {"rich_text": [{"text": {"content": "{}"}}]}
    }
}

url = "https://api.notion.com/v1/pages"
res = requests.post(url, headers=HEADERS, json=payload)

print("STATUS:", res.status_code)
print(res.text)
