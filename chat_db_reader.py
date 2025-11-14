# ===============================================================
# reader.py – View Chat History & Summaries
# ===============================================================

import sqlite3
from tabulate import tabulate

DB_PATH = "chat_history.db"   # ✅ FIXED

def connect():
    return sqlite3.connect(DB_PATH)

# ---------------------------------------------------------------
# SHOW ALL MESSAGES
# ---------------------------------------------------------------
def show_all_messages():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, user_id, role, message, timestamp
        FROM messages ORDER BY id ASC
    """)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("\n(No messages found)\n")
        return

    print(tabulate(rows,
                   headers=["ID", "User", "Role", "Message", "Time"],
                   tablefmt="fancy_grid"))

# ---------------------------------------------------------------
# SHOW MESSAGES FOR A SPECIFIC USER
# ---------------------------------------------------------------
def show_user_messages(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, role, message, timestamp
        FROM messages WHERE user_id = ?
        ORDER BY id ASC
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("\n(No messages for this user)\n")
        return

    print(tabulate(rows,
                   headers=["ID", "Role", "Message", "Time"],
                   tablefmt="fancy_grid"))

# ---------------------------------------------------------------
# SHOW SUMMARIES
# ---------------------------------------------------------------
def show_summaries():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, user_id, summary, timestamp
        FROM summaries ORDER BY id ASC
    """)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("\n(No summaries found)\n")
        return

    print(tabulate(rows,
                   headers=["ID", "User", "Summary", "Time"],
                   tablefmt="fancy_grid"))

# ---------------------------------------------------------------
# MAIN MENU
# ---------------------------------------------------------------
def main():
    while True:
        print("\n================ CHAT READER ================\n")
        print("1. Show ALL messages")
        print("2. Show messages for a specific user")
        print("3. Show ALL summaries")
        print("4. Exit\n")

        op = input("Select option: ")

        if op == "1":
            show_all_messages()

        elif op == "2":
            user = input("Enter user_id: ")
            show_user_messages(user)

        elif op == "3":
            show_summaries()

        elif op == "4":
            print("Exiting...")
            break

        else:
            print("Invalid option.\n")

if __name__ == "__main__":
    main()
