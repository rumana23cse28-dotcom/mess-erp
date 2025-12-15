# Mess ERP System

Mess ERP System is a **Flask-based web application** designed for complete mess management in colleges.

## 🚀 Features
- 🔐 Role-based Login (Principal, Incharge, Student)
- 📊 Attendance Management & Summary
- 🧾 Inventory Management with PDF Reports
- 🍽️ Mess Menu Management
- 💰 Automatic Mess Billing System
- 📄 PDF Generation (Attendance, Inventory, Bills)
- 🔑 Google Login Integration
- 📈 Charts & Dashboard Analytics

## 🛠️ Tech Stack
- Backend: Flask (Python)
- Database: SQLite
- Frontend: HTML, CSS, Bootstrap, JavaScript
- Reports: ReportLab (PDF)
- Authentication: Flask Session + Google OAuth

## 👥 User Roles
- **Principal**: Full access, reports, billing, analytics
- **Mess Incharge**: Attendance, inventory, menu
- **Student**: View attendance, menu, bills

## 📦 Installation
```bash
pip install -r requirements.txt
python app.py
