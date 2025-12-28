import sqlite3
import os

# ---------------- CREATE DATABASE FOLDER ----------------
os.makedirs('database', exist_ok=True)

# ---------------- CONNECT DATABASE ----------------
con = sqlite3.connect('database/mess.db')
cur = con.cursor()

# ---------------- USERS TABLE ----------------
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

# ---------------- INVENTORY TABLE ----------------
cur.execute("""
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT,
    added_qty REAL,
    used_qty REAL,
    remaining REAL,
    date TEXT
)
""")

# ---------------- MENU TABLE ----------------
cur.execute("""
CREATE TABLE IF NOT EXISTS menu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    breakfast TEXT,
    lunch TEXT,
    dinner TEXT
)
""")

# ---------------- ATTENDANCE TABLE ----------------
cur.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    student_email TEXT,
    status TEXT
)
""")

# ---------------- MESS BILL TABLE ----------------
cur.execute("""
CREATE TABLE IF NOT EXISTS mess_bill (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_email TEXT,
    month TEXT,
    present_days INTEGER,
    amount REAL,
    status TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS student_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    name TEXT,
    role TEXT,
    branch TEXT,
    semester TEXT,
    phone TEXT,
    address TEXT,
    photo TEXT,
    role TEXT,
)
""")





# ---------------- SAFE DEFAULT USERS INSERT ----------------
def insert_user(email, password, role):
    cur.execute("SELECT id FROM users WHERE email=?", (email,))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO users (email, password, role) VALUES (?,?,?)",
            (email, password, role)
        )

insert_user('principal@gmail.com', '123', 'principal')
insert_user('incharge@gmail.com', '123', 'incharge')
insert_user('student@gmail.com', '123', 'student')

# ---------------- COMMIT & CLOSE ----------------
con.commit()
con.close()

print("✅ Database created successfully with ALL tables")
