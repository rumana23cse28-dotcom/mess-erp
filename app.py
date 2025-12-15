import os
from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
from datetime import date
from io import BytesIO

# -------- REPORTLAB --------
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from authlib.integrations.flask_client import OAuth
app = Flask(__name__)
app.secret_key = 'mess_erp_secret'
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
DB = 'database/mess.db'
PER_DAY_CHARGE = 120


oauth = OAuth(app)

oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)



# ================= DB CONNECTION =================
def get_db():
    return sqlite3.connect(DB)


# ================= LOGIN =================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        con = get_db()
        cur = con.cursor()
        cur.execute(
            "SELECT role FROM users WHERE email=? AND password=?",
            (request.form['email'], request.form['password'])
        )
        user = cur.fetchone()
        con.close()

        if user:
            session['user'] = request.form['email']
            session['role'] = user[0]
            return redirect(f"/{user[0]}/dashboard")

    return render_template('auth/login.html')


# ================= GOOGLE LOGIN (DEMO) =================
@app.route("/login/google")
def google_login():
    redirect_uri = "http://127.0.0.1:5000/auth/google/callback"
    return oauth.google.authorize_redirect(redirect_uri)

@app.route("/auth/google/callback")
def google_callback():
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.get("https://www.googleapis.com/oauth2/v2/userinfo").json()

    email = user_info["email"]

    # ---------- ROLE DECISION ----------
    if email == "principal@gmail.com":
        role = "principal"
    elif email == "incharge@gmail.com":
        role = "incharge"
    else:
        role = "student"
    # ----------------------------------

    con = get_db()
    cur = con.cursor()

    cur.execute("SELECT role FROM users WHERE email=?", (email,))
    user = cur.fetchone()

    if not user:
        cur.execute(
            "INSERT INTO users (email, password, role) VALUES (?,?,?)",
            (email, "google", role)
        )
        con.commit()
    else:
        role = user[0]   # DB role priority

    con.close()

    session["user"] = email
    session["role"] = role

    return redirect(f"/{role}/dashboard")

# ================= DASHBOARDS =================
@app.route('/principal/dashboard')
def principal_dashboard():
    if session.get('role') != 'principal':
        return redirect('/')

    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM inventory")
    total_items = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM inventory WHERE remaining < 5")
    low_stock = cur.fetchone()[0]
    con.close()

    return render_template(
        'principal/dashboard.html',
        role='principal',
        total_items=total_items,
        low_stock=low_stock
    )


@app.route('/incharge/dashboard')
def incharge_dashboard():
    if session.get('role') != 'incharge':
        return redirect('/')
    return render_template('mess_incharge/dashboard.html', role='incharge')


@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect('/')
    return render_template('student/dashboard.html', role='student')


# ================= INVENTORY =================
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if 'role' not in session:
        return redirect('/')

    role = session['role']
    can_add = role in ['principal', 'incharge']

    con = get_db()
    cur = con.cursor()

    if request.method == 'POST' and can_add:
        added = float(request.form['added'])
        used = float(request.form['used'])

        cur.execute("""
            INSERT INTO inventory
            (item, added_qty, used_qty, remaining, date)
            VALUES (?,?,?,?,?)
        """, (
            request.form['item'],
            added,
            used,
            added - used,
            str(date.today())
        ))
        con.commit()

    cur.execute("SELECT * FROM inventory ORDER BY date DESC")
    data = cur.fetchall()
    con.close()

    template = (
        'principal/inventory.html'
        if role == 'principal'
        else 'mess_incharge/inventory.html'
    )

    return render_template(template, role=role, data=data, can_add=can_add)


# ================= INVENTORY PDF =================
@app.route('/inventory/pdf')
def inventory_pdf():
    if session.get('role') != 'principal':
        return redirect('/')

    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT item, added_qty, used_qty, remaining, date FROM inventory")
    rows = cur.fetchall()
    con.close()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Inventory Report</b>", styles['Title']))
    elements.append(Paragraph("<br/>", styles['Normal']))

    table = Table([["Item","Added","Used","Remaining","Date"]] + rows)
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.darkblue),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),1,colors.black),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name="inventory_report.pdf",
                     mimetype="application/pdf")


# ================= MENU =================
@app.route('/menu', methods=['GET', 'POST'])
def menu():
    if 'role' not in session:
        return redirect('/')

    role = session['role']
    con = get_db()
    cur = con.cursor()

    if request.method == 'POST' and role in ['principal', 'incharge']:
        cur.execute("""
            INSERT INTO menu (date, breakfast, lunch, dinner)
            VALUES (?,?,?,?)
        """, (
            request.form['date'],
            request.form['breakfast'],
            request.form['lunch'],
            request.form['dinner']
        ))
        con.commit()

    cur.execute("SELECT * FROM menu ORDER BY date DESC")
    data = cur.fetchall()
    con.close()

    if role in ['principal', 'incharge']:
        return render_template('mess_incharge/menu.html', role=role, data=data)
    else:
        return render_template('student/menu.html', role=role, data=data)
    

    # ================= MENU PDF =================
@app.route('/menu/pdf')
def menu_pdf():
    if session.get('role') != 'principal':
        return redirect('/')

    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT date, breakfast, lunch, dinner FROM menu ORDER BY date DESC")
    rows = cur.fetchall()
    con.close()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Mess Menu Report</b>", styles['Title']))
    elements.append(Paragraph("<br/>", styles['Normal']))

    table_data = [["Date", "Breakfast", "Lunch", "Dinner"]]
    for r in rows:
        table_data.append(list(r))

    table = Table(table_data, colWidths=[90, 130, 130, 130])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkgreen),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="menu_report.pdf",
        mimetype="application/pdf"
    )



# ================= ATTENDANCE =================
@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'role' not in session:
        return redirect('/')

    role = session['role']
    con = get_db()
    cur = con.cursor()

    if request.method == 'POST' and role == 'incharge':
        cur.execute(
            "INSERT INTO attendance (date, student_email, status) VALUES (?,?,?)",
            (str(date.today()), request.form['student_email'], request.form['status'])
        )
        con.commit()

    if role == 'student':
        cur.execute("SELECT date, status FROM attendance WHERE student_email=?",
                    (session['user'],))
        data = cur.fetchall()
        template = 'student/attendance.html'
    elif role == 'principal':
        cur.execute("SELECT date, student_email, status FROM attendance")
        data = cur.fetchall()
        template = 'principal/attendance.html'
    else:
        cur.execute("SELECT date, student_email, status FROM attendance")
        data = cur.fetchall()
        template = 'mess_incharge/attendance.html'

    con.close()
    return render_template(template, role=role, data=data)


# =# ================= ATTENDANCE SUMMARY =================
@app.route('/attendance/summary')
def attendance_summary():
    if 'role' not in session:
        return redirect('/')

    con = get_db()
    cur = con.cursor()

    # -------- STUDENT --------
    if session['role'] == 'student':
        cur.execute("""
            SELECT COUNT(*),
                   SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END)
            FROM attendance
            WHERE student_email=?
        """, (session['user'],))

        total, present = cur.fetchone()
        percent = round((present / total) * 100, 2) if total else 0
        con.close()

        return render_template(
            'student/attendance_summary.html',
            total=total,
            present=present,
            percent=percent
        )

    # -------- PRINCIPAL / INCHARGE --------
    cur.execute("""
        SELECT student_email,
               COUNT(*) AS total_days,
               SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS present_days
        FROM attendance
        GROUP BY student_email
    """)
    data = cur.fetchall()
    con.close()

    # role-wise template
    if session['role'] == 'principal':
        return render_template(
            'principal/attendance_summary.html',
            data=data
        )

    # incharge
    return render_template(
        'mess_incharge/attendance_summary.html',
        data=data
    )


@app.route('/attendance/summary/pdf')
def attendance_summary_pdf():
    if session.get('role') != 'principal':
        return redirect('/')

    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT student_email,
               COUNT(*),
               SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END)
        FROM attendance GROUP BY student_email
    """)
    rows = cur.fetchall()
    con.close()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Attendance Summary Report</b>", styles['Title']))
    elements.append(Paragraph("<br/>", styles['Normal']))

    table_data = [["Student", "Total Days", "Present Days", "Attendance %"]]

    for r in rows:
        percent = round((r[2] / r[1]) * 100, 2) if r[1] else 0
        table_data.append([r[0], r[1], r[2], f"{percent}%"])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.darkblue),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),1,colors.black),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="attendance_summary.pdf",
        mimetype="application/pdf"
    )



# ================= ATTENDANCE PDF =================
@app.route('/attendance/pdf')
def attendance_pdf():
    if session.get('role') != 'principal':
        return redirect('/')

    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT date, student_email, status FROM attendance")
    rows = cur.fetchall()
    con.close()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Attendance Report</b>", styles['Title']))
    elements.append(Paragraph("<br/>", styles['Normal']))

    table = Table([["Date","Student","Status"]] + rows)
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.green),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),1,colors.black),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name="attendance_report.pdf",
                     mimetype="application/pdf")


# ================= BILL =================
@app.route('/bill')
def bill():
    if 'role' not in session:
        return redirect('/')

    con = get_db()
    cur = con.cursor()

    if session['role'] == 'student':
        cur.execute("SELECT * FROM mess_bill WHERE student_email=?",
                    (session['user'],))
    else:
        cur.execute("SELECT * FROM mess_bill")

    data = cur.fetchall()
    con.close()
    return render_template('bill.html', role=session['role'], data=data)


@app.route('/bill/generate')
def generate_bill():
    if session.get('role') != 'principal':
        return redirect('/')

    con = get_db()
    cur = con.cursor()

    cur.execute("""
        SELECT student_email,
               SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END)
        FROM attendance GROUP BY student_email
    """)

    month = date.today().strftime('%B %Y')

    for email, present_days in cur.fetchall():
        amount = present_days * PER_DAY_CHARGE
        cur.execute("""
            INSERT INTO mess_bill
            (student_email, month, present_days, amount, status)
            VALUES (?,?,?,?,?)
        """, (email, month, present_days, amount, 'Due'))

    con.commit()
    con.close()
    return redirect('/bill')


@app.route('/bill/paid/<int:id>')
def bill_paid(id):
    if session.get('role') != 'principal':
        return redirect('/')

    con = get_db()
    cur = con.cursor()
    cur.execute("UPDATE mess_bill SET status='Paid' WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect('/bill')


@app.route('/bill/pdf/<int:id>')
def bill_pdf(id):
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM mess_bill WHERE id=?", (id,))
    b = cur.fetchone()
    con.close()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Mess Bill</b>", styles['Title']))
    elements.append(Paragraph(f"Student: {b[1]}", styles['Normal']))
    elements.append(Paragraph(f"Month: {b[2]}", styles['Normal']))
    elements.append(Paragraph(f"Present Days: {b[3]}", styles['Normal']))
    elements.append(Paragraph(f"Amount: ₹ {b[4]}", styles['Normal']))
    elements.append(Paragraph(f"Status: {b[5]}", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name="mess_bill.pdf",
                     mimetype="application/pdf")
@app.route('/report/monthly/pdf')
def monthly_report_pdf():
    if session.get('role') != 'principal':
        return redirect('/')

    con = get_db()
    cur = con.cursor()

    cur.execute("""
        SELECT a.student_email,
               COUNT(a.id) AS total_days,
               SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present_days,
               b.amount,
               b.status,
               b.month
        FROM attendance a
        LEFT JOIN mess_bill b
        ON a.student_email = b.student_email
        GROUP BY a.student_email
    """)

    rows = cur.fetchall()
    con.close()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Monthly Attendance & Mess Bill Report</b>", styles['Title']))
    elements.append(Paragraph("<br/>", styles['Normal']))

    table_data = [
        ["Student", "Total Days", "Present", "Attendance %", "Amount", "Status"]
    ]

    for r in rows:
        percent = round((r[2]/r[1])*100, 2) if r[1] else 0
        table_data.append([
            r[0], r[1], r[2], f"{percent}%", r[3], r[4]
        ])

    table = Table(table_data, colWidths=[100,70,60,80,70,60])
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.darkblue),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),1,colors.black),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name="monthly_report.pdf",
                     mimetype="application/pdf")

@app.route('/bill/chart')
def bill_chart():
    if session.get('role') != 'principal':
        return redirect('/')

    con = get_db()
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM mess_bill WHERE status='Paid'")
    paid = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM mess_bill WHERE status='Due'")
    due = cur.fetchone()[0]

    con.close()

    return render_template(
        'principal/bill_chart.html',
        paid=paid,
        due=due
    )




# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ================= RUN =================
if __name__ == '__main__':
   if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
