# Attendance module
import sqlite3
from datetime import date

DB = 'database/mess.db'

def get_db():
    return sqlite3.connect(DB)

def mark_attendance(student_email, status):
    con = get_db()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO attendance (student_email, status, date)
        VALUES (?,?,?)
    """, (student_email, status, date.today()))
    con.commit()
    con.close()

def get_attendance():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM attendance ORDER BY date DESC")
    data = cur.fetchall()
    con.close()
    return data
