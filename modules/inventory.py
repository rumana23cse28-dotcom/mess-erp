# Inventory module

import sqlite3
from datetime import date


DB = 'database/mess.db'


def add_stock(item, added, used):
remaining = float(added) - float(used)
con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute(
'INSERT INTO inventory (item, added_qty, used_qty, remaining, date) VALUES (?,?,?,?,?)',
(item, added, used, remaining, date.today())
)
con.commit()
con.close()


def get_inventory():
con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute('SELECT * FROM inventory ORDER BY date DESC')
data = cur.fetchall()
con.close()
return data
