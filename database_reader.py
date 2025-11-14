import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

print("📘 Reading database:", DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())

cursor.execute("SELECT id, email, password FROM users;")
rows = cursor.fetchall()

print("\n👤 Users in Database:")
for row in rows:
    print(f"ID: {row[0]} | Email: {row[1]} | Password: {row[2]}")

conn.close()
