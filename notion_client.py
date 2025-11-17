import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def query_database(db_id, payload=None):
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    res = requests.post(url, headers=HEADERS, json=payload or {})
    res.raise_for_status()
    return res.json()

def update_page(page_id, payload):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    res = requests.patch(url, headers=HEADERS, json=payload)
    res.raise_for_status()
    return res.json()

def create_page(db_id, properties, children=None):
    url = "https://api.notion.com/v1/pages"
    body = {
        "parent": {"database_id": db_id},
        "properties": properties
    }
    if children:
        body["children"] = children
    res = requests.post(url, headers=HEADERS, json=body)
    res.raise_for_status()
    return res.json()
