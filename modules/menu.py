# Menu module
import sqlite3

DB = 'database/mess.db'

def get_db():
    return sqlite3.connect(DB)

def add_menu(date, breakfast, lunch, dinner):
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO menu (date, breakfast, lunch, dinner)
        VALUES (?,?,?,?)
    """, (date, breakfast, lunch, dinner))
    con.commit()
    con.close()

def get_menu():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM menu ORDER BY date DESC")
    data = cur.fetchall()
    con.close()
    return data
