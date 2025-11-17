import os
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import json

# === LOAD ENV ===
load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
TASKS_DB_ID = os.getenv("TASKS_DB_ID")
DAILY_LOG_DB_ID = os.getenv("DAILY_LOG_DB_ID")
STRATEGY_DB_ID = os.getenv("STRATEGY_DB_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Kyiv")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}


# ---------------------------------------------------------
# 🔧 BASIC NOTION API UTILITIES
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# 📅 DATE HELPERS
# ---------------------------------------------------------
def get_today():
    tz = ZoneInfo(TIMEZONE)
    return datetime.now(tz).date()


# ---------------------------------------------------------
# 📌 GET TASKS FOR TODAY
# ---------------------------------------------------------
def get_tasks_for_date(date):
    payload = {
        "filter": {
            "property": "Date",
            "date": {"equals": date.isoformat()}
        }
    }
    data = query_database(TASKS_DB_ID, payload)
    return data["results"]


# ---------------------------------------------------------
# 🔁 AUTO-ROLL — переносим невыполненные задачи
# ---------------------------------------------------------
def auto_roll_tasks(tasks):
    today = get_today()
    new_date = today + timedelta(days=2)

    rolled_count = 0

    for task in tasks:
        props = task["properties"]
        status = props.get("Status", {}).get("select", {}).get("name")
        auto_roll_flag = props.get("Auto-roll?", {}).get("checkbox", False)

        if status == "Done":
            continue

        if not auto_roll_flag:
            continue

        page_id = task["id"]

        update_page(page_id, {
            "properties": {
                "Date": {"date": {"start": new_date.isoformat()}},
                "Rollovers": {"number": props.get("Rollovers", {}).get("number", 0) + 1}
            }
        })

        rolled_count += 1

    return rolled_count


# ---------------------------------------------------------
# 📊 CALCULATE STATISTICS
# ---------------------------------------------------------
def calculate_stats(tasks):
    total = len(tasks)
    done_tasks = 0
    planned_min = 0
    actual_min = 0
    deep_work_min = 0

    for task in tasks:
        props = task["properties"]

        status = props.get("Status", {}).get("select", {}).get("name")
        if status == "Done":
            done_tasks += 1

        planned = props.get("Planned duration (min)", {}).get("number")
        actual = props.get("Actual duration (min)", {}).get("number")
        task_type = props.get("Type", {}).get("select", {}).get("name")

        if planned:
            planned_min += planned
        if actual:
            actual_min += actual

        if task_type == "Deep work" and actual:
            deep_work_min += actual

    return {
        "total": total,
        "done": done_tasks,
        "planned_min": planned_min,
        "actual_min": actual_min,
        "deep_work_min": deep_work_min
    }

# ---------------------------------------------------------
# 🧠 SUMMARY FROM OPENAI
# ---------------------------------------------------------

def generate_ai_summary(stats):
    import openai

    openai.api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.getenv("MODEL_NAME", "meta-llama/llama-3.1-8b-instruct")

    client = openai.OpenAI(
        base_url=base_url,
        api_key=openai.api_key,
    )

    prompt = f"""
Ты — мой ИИ-коуч. Вот статистика дня:

Всего задач: {stats['total']}
Выполнено: {stats['done']}
Плановое время: {stats['planned_min']} мин
Реальное время: {stats['actual_min']} мин
Deep work: {stats['deep_work_min']} мин

Сделай короткое summary:
1) Похвала или мягкое подталкивание.
2) Мотивация.
3) Что улучшить завтра (3 пункта).
"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=250,
        temperature=0.7,
    )

    # исправленный возврат текста
    return response.choices[0].message.content


# ---------------------------------------------------------
# 🟢 DAY STATUS — AHEAD / ON TRACK / BEHIND
# ---------------------------------------------------------
def determine_status(stats):
    if stats["total"] == 0:
        return "On track"

    ratio = stats["done"] / stats["total"]

    if ratio >= 0.9:
        return "Ahead"
    elif ratio >= 0.6:
        return "On track"
    else:
        return "Behind"


# ---------------------------------------------------------
# 📝 CREATE DAILY LOG ENTRY
# ---------------------------------------------------------
def create_daily_log(stats, summary):
    today = get_today()

    properties = {
        "Name": {"title": [{"text": {"content": f"Day {today}"}}]},
        "Date": {"date": {"start": today.isoformat()}},
        "Status vs plan": {"select": {"name": determine_status(stats)}},
        "Total tasks": {"number": stats["total"]},
        "Done tasks": {"number": stats["done"]},
        "Planned min": {"number": stats["planned_min"]},
        "Actual min": {"number": stats["actual_min"]},
        "Deep work min": {"number": stats["deep_work_min"]},
        "Raw data (JSON)": {"rich_text": [{"text": {"content": json.dumps(stats)}}]}
    }

    children = [{
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": summary}}]}
    }]

    return create_page(DAILY_LOG_DB_ID, properties, children)


# ---------------------------------------------------------
# 🚀 MAIN LOGIC
# ---------------------------------------------------------
def main():
    today = get_today()
    print(f"=== RUNNING DAILY JOB FOR {today} ===")

    tasks = get_tasks_for_date(today)
    print(f"Loaded {len(tasks)} tasks")

    rolled = auto_roll_tasks(tasks)
    print(f"Rolled over {rolled} tasks")

    stats = calculate_stats(tasks)
    print("Stats:", stats)

    summary = generate_ai_summary(stats)
    print("Summary generated")

    create_daily_log(stats, summary)
    print("Daily log created")

    print("=== DONE ===")


if __name__ == "__main__":
    main()
