# PDF reports module
import sqlite3

DB = 'database/mess.db'

def get_db():
    return sqlite3.connect(DB)

def inventory_report():
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT item, added_qty, used_qty, remaining, date
        FROM inventory
        ORDER BY date DESC
    """)
    data = cur.fetchall()
    con.close()
    return data

def menu_report():
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT date, breakfast, lunch, dinner
        FROM menu
        ORDER BY date DESC
    """)
    data = cur.fetchall()
    con.close()
    return data
