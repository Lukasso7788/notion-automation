from notion_client import query_database
import os

TASKS_DB_ID = os.getenv("TASKS_DB_ID")

print("🔍 Тест: читаем Tasks...")

data = query_database(TASKS_DB_ID)
print("Количество записей:", len(data["results"]))
print("Первый объект:")
if data["results"]:
    print(data["results"][0])
else:
    print("Таблица пока пустая.")
