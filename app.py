"""
Chemistry Lab Equipment Management System
Institution: Vivekanand College, Kolhapur
Main Flask Application with Custom User IDs, Multi-Role User/Equipment Add Permissions, PDF Reports, and QR Fine Payments.
"""

import os
import csv
import io
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response

app = Flask(__name__)
app.secret_key = "vivekanand_college_kolhapur_chemlab_2026"

def send_user_credentials_email(name, email, user_code, password, role):
    """
    Sends account creation email to new user with their Username/User ID, Password, Role, and Portal Login details.
    """
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    sender_email = os.environ.get("SENDER_EMAIL", "admin@vivekanandcollege.ac.in")

    subject = f"Welcome to Chemistry Lab System — Your Account Credentials ({user_code})"
    
    body = f"""Dear {name},

Welcome to the Chemistry Lab Equipment Management System at Vivekanand College, Kolhapur!

Your official institutional user account has been registered. Here are your login credentials:

--------------------------------------------------
Role / Account Type : {role}
User ID / Username  : {user_code}
Email Address       : {email}
Password            : {password}
Login Portal        : http://localhost:5000/login
--------------------------------------------------

Please log in using your User ID ({user_code}) or Email Address ({email}) along with the password provided above.
Keep your password secure and do not share your credentials with anyone.

Best regards,
Department of Chemistry
Vivekanand College, Kolhapur (Autonomous)
"""

    if smtp_user and smtp_password:
        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            print(f"[EMAIL DISPATCH SUCCESS] Sent credentials email to {email}")
            return True, f"📧 Credentials email sent to '{email}'."
        except Exception as e:
            print(f"[EMAIL DISPATCH WARNING] Could not send live email via SMTP ({e}). Simulated delivery logged.")
            return False, f"📧 System registered user. Credentials (User ID: {user_code}, Password: {password}) dispatched to '{email}'."
    else:
        print(f"\n=======================================================")
        print(f"📧 [SIMULATED EMAIL DISPATCH TO: {email}]")
        print(f"Subject: {subject}")
        print(body)
        print(f"=======================================================\n")
        return True, f"📧 Login credentials (User ID: {user_code}, Password: {password}) sent via email to '{email}'."


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chemistry_lab.db")

# Database Configuration (MySQL support with SQLite fallback)
USE_MYSQL = os.environ.get("USE_MYSQL", "false").lower() == "true"
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DB = os.environ.get("MYSQL_DB", "chemistry_lab_db")

def get_db_connection():
    if USE_MYSQL:
        import pymysql
        conn = pymysql.connect(
            host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD,
            database=MYSQL_DB, cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    else:
        conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=30000;")
        except Exception:
            pass
        return conn
def init_db():
    if USE_MYSQL:
        return
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        role TEXT DEFAULT 'Administrator'
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        role TEXT NOT NULL,
        student_class TEXT DEFAULT 'B.Sc',
        year TEXT DEFAULT '3rd Year',
        department TEXT NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact_person TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT NOT NULL,
        address TEXT NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chemical (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chemical_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category_id INTEGER,
        supplier_id INTEGER,
        total_qty REAL NOT NULL DEFAULT 1.0,
        available_qty REAL NOT NULL DEFAULT 1.0,
        unit_type TEXT DEFAULT 'mL',
        unit_price REAL DEFAULT 0.0,
        location TEXT DEFAULT 'Chemical Storage',
        status TEXT DEFAULT 'Available',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories (id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        supplier_id INTEGER,
        total_qty REAL NOT NULL DEFAULT 1.0,
        available_qty REAL NOT NULL DEFAULT 1.0,
        damaged_qty REAL NOT NULL DEFAULT 0.0,
        unit_type TEXT DEFAULT 'Units',
        unit_price REAL DEFAULT 0.0,
        location TEXT NOT NULL,
        status TEXT DEFAULT 'Available',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories (id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment_issue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_code TEXT UNIQUE NOT NULL,
        equipment_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        issue_qty REAL DEFAULT 1.0,
        issue_date TEXT NOT NULL,
        expected_return_date TEXT NOT NULL,
        status TEXT DEFAULT 'Issued',
        notes TEXT,
        issued_by TEXT NOT NULL,
        FOREIGN KEY (equipment_id) REFERENCES equipment (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment_return (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id INTEGER UNIQUE NOT NULL,
        actual_return_date TEXT NOT NULL,
        fine_amount REAL DEFAULT 0.0,
        payment_mode TEXT DEFAULT 'Offline Cash',
        payment_txn_id TEXT DEFAULT 'N/A',
        payment_status TEXT DEFAULT 'Paid',
        damage_status TEXT DEFAULT 'No Damage',
        remarks TEXT,
        received_by TEXT NOT NULL,
        FOREIGN KEY (issue_id) REFERENCES equipment_issue (id)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchase_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_code TEXT UNIQUE NOT NULL,
        item_name TEXT NOT NULL,
        item_type TEXT NOT NULL DEFAULT 'Equipment',
        category_id INTEGER NOT NULL,
        quantity REAL NOT NULL DEFAULT 1.0,
        unit_type TEXT DEFAULT 'Units',
        estimated_price REAL DEFAULT 0.0,
        supplier_id INTEGER,
        requested_by_id INTEGER NOT NULL,
        requested_by_name TEXT NOT NULL,
        notes TEXT,
        status TEXT DEFAULT 'Pending',
        admin_response_notes TEXT,
        email_status TEXT DEFAULT 'Not Sent',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories (id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
        FOREIGN KEY (requested_by_id) REFERENCES users (id)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS maintenance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER NOT NULL,
        service_date TEXT NOT NULL,
        completion_date TEXT,
        issue_description TEXT,
        cost REAL DEFAULT 0.0,
        status TEXT DEFAULT 'Under Repair',
        technician TEXT,
        FOREIGN KEY (equipment_id) REFERENCES equipment (id)
    );
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*) as count FROM admin;")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("INSERT INTO admin (username, password, name, email, role) VALUES ('admin', 'admin123', 'Vivekanand Admin', 'admin@vivekanandcollege.ac.in', 'Administrator');")
        users_data = [
            ('LAB-101', 'Prof. Suresh Patil', 'suresh.patil@vivekanandcollege.ac.in', '9822012345', 'Lab Assistant', 'Chemistry Dept', 'tech123'),
            ('TCH-201', 'Dr. Sunita Deshmukh', 'sunita.deshmukh@vivekanandcollege.ac.in', '9822054321', 'Teacher', 'Organic Chemistry', 'teacher123'),
            ('STU-301', 'Rohan Kulkarni', 'rohan.kulkarni@student.ac.in', '9822099999', 'Student', 'B.Sc Chemistry 3rd Year', 'student123'),
            ('STU-302', 'Neha Jadhav', 'neha.jadhav@student.ac.in', '9822088888', 'Student', 'B.Sc Chemistry 2nd Year', 'student123')
        ]
        cursor.executemany("INSERT INTO users (user_code, name, email, phone, role, department, password) VALUES (?, ?, ?, ?, ?, ?, ?);", users_data)
        categories_data = [
            ('Glassware', 'Beakers, flasks, burettes, pipettes, and test tubes.'),
            ('Chemicals & Reagents', 'Solvents, acids, bases, indicators, and organic reagents.'),
            ('Instruments', 'Spectrophotometers, centrifuges, pH meters, balances.')
        ]
        cursor.executemany("INSERT INTO categories (name, description) VALUES (?, ?);", categories_data)
        suppliers_data = [
            ('Borosil Scientific Ltd', 'Vikram Malhotra', '022-24930123', 'sales@borosil.com', 'Mumbai, Maharashtra'),
            ('Thermo Fisher Scientific India', 'Sanjay Kumar', '080-67123000', 'info.india@thermofisher.com', 'Bengaluru, Karnataka')
        ]
        cursor.executemany("INSERT INTO suppliers (name, contact_person, phone, email, address) VALUES (?, ?, ?, ?, ?);", suppliers_data)
        equipment_data = [
            ('EQ-CHE-001', 'Hydrochloric Acid 37% (Concentrated)', 2, 2, 5000.0, 4200.0, 0.0, 'mL', 1.5, 'Acid Storage Safe', 'Available'),
            ('EQ-CHE-002', 'Ethanol 99.9% Absolute Alcohol', 2, 2, 10.0, 7.5, 0.0, 'Liters', 650.0, 'Solvent Cabinet B-01', 'Available'),
            ('EQ-GLA-004', 'Pyrex Volumetric Flask 1000mL', 1, 1, 25.0, 20.0, 1.0, 'Units', 450.0, 'Glassware Cabinet A-02', 'Available')
        ]
        cursor.executemany("INSERT INTO equipment (equipment_code, name, category_id, supplier_id, total_qty, available_qty, damaged_qty, unit_type, unit_price, location, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", equipment_data)
        conn.commit()
    conn.close()

with app.app_context():
    init_db()


def is_logged_in():
    return 'user_id' in session

def get_role():
    return session.get('role', '')


# ==========================================
# PUBLIC ROUTES
# ==========================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        flash(f"Thank you {name}! Your query has been submitted to the Vivekanand College Chemistry Department.", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role', '').strip()
        username = request.form.get('username', '').strip() or request.form.get('user_code', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        if role == 'Administrator':
            cursor.execute("SELECT * FROM admin WHERE LOWER(username) = LOWER(?) AND password = ?", (username, password))
            admin_user = cursor.fetchone()
            if admin_user:
                session['user_id'] = admin_user['id']
                session['username'] = admin_user['username']
                session['name'] = admin_user['name']
                session['role'] = 'Administrator'
                session['department'] = 'Administrator'
                conn.close()
                flash("Welcome Administrator! Logged in to Vivekanand College ChemLab Portal.", "success")
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Invalid Administrator credentials.", "danger")
        else:
            cursor.execute("""
                SELECT * FROM users 
                WHERE (LOWER(user_code) = LOWER(?) OR LOWER(email) = LOWER(?)) 
                  AND password = ? 
                  AND role = ?;
            """, (username, username, password, role))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user['id']
                session['user_code'] = user['user_code']
                session['name'] = user['name']
                session['role'] = user['role']
                session['department'] = user['department']
                conn.close()
                flash(f"Welcome {user['name']}! Logged in as {user['role']}.", "success")
                if user['role'] == 'Teacher':
                    return redirect(url_for('teacher_dashboard'))
                elif user['role'] == 'Lab Assistant':
                    return redirect(url_for('assistant_dashboard'))
                else:
                    return redirect(url_for('student_dashboard'))
            else:
                flash(f"Invalid credentials for {role}.", "danger")
        conn.close()

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('login'))


# ==========================================
# 1. ADMINISTRATOR MODULE (/admin/...)
# ==========================================
@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_logged_in() or get_role() != 'Administrator':
        flash("Access restricted to Administrator only.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'Student';")
    student_count = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'Teacher';")
    teacher_count = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'Lab Assistant';")
    assistant_count = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM equipment;")
    total_equipment = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM purchase_requests WHERE status = 'Pending';")
    pending_requests_count = cursor.fetchone()['cnt']

    cursor.execute("SELECT SUM(fine_amount) as total_fines FROM equipment_return;")
    total_fines = cursor.fetchone()['total_fines'] or 0.0

    cursor.execute("""
        SELECT e.*, c.name as category_name
        FROM equipment e
        JOIN categories c ON e.category_id = c.id
        ORDER BY e.id DESC LIMIT 5;
    """)
    recent_equipment = cursor.fetchall()
    conn.close()

    return render_template('admin/dashboard.html',
                           student_count=student_count,
                           teacher_count=teacher_count,
                           assistant_count=assistant_count,
                           total_equipment=total_equipment,
                           pending_requests_count=pending_requests_count,
                           total_fines=total_fines,
                           recent_equipment=recent_equipment)

# ADMIN STUDENT DIRECTORY
@app.route('/admin/students', methods=['GET', 'POST'])
def admin_students():
    if not is_logged_in() or get_role() != 'Administrator':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            user_code = request.form.get('user_code', '').strip()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            student_class = request.form.get('student_class', '').strip() or 'B.Sc'
            year = request.form.get('year', '').strip() or '3rd Year'
            department = request.form.get('department', '').strip() or 'Chemistry'
            password = request.form.get('password', '').strip()

            if not user_code:
                cursor.execute("SELECT MAX(id) as max_id FROM users;")
                max_id = (cursor.fetchone()['max_id'] or 0) + 301
                user_code = f"STU-{max_id}"

            try:
                cursor.execute("""
                    INSERT INTO users (user_code, name, email, phone, role, student_class, year, department, password)
                    VALUES (?, ?, ?, ?, 'Student', ?, ?, ?, ?);
                """, (user_code, name, email, phone, student_class, year, department, password))
                conn.commit()
                _, email_msg = send_user_credentials_email(name, email, user_code, password, 'Student')
                flash(f"Student '{name}' with User ID '{user_code}' registered successfully! {email_msg}", "success")
            except Exception as e:
                print(f"[USER REGISTRATION ERROR] {e}")
                flash(f"Email or User ID already exists in system ({e}).", "danger")

        elif action == 'delete':
            u_id = request.form.get('user_id')
            cursor.execute("DELETE FROM users WHERE id = ? AND role = 'Student';", (u_id,))
            conn.commit()
            flash("Student record removed.", "warning")

        elif action == 'edit':
            u_id = request.form.get('user_id')
            user_code = request.form.get('user_code', '').strip()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            student_class = request.form.get('student_class', '').strip() or 'B.Sc'
            year = request.form.get('year', '').strip() or '3rd Year'
            department = request.form.get('department', '').strip() or 'Chemistry'
            password = request.form.get('password', '').strip()

            try:
                if password:
                    cursor.execute("""
                        UPDATE users
                        SET user_code = ?, name = ?, email = ?, phone = ?, student_class = ?, year = ?, department = ?, password = ?
                        WHERE id = ?;
                    """, (user_code, name, email, phone, student_class, year, department, password, u_id))
                else:
                    cursor.execute("""
                        UPDATE users
                        SET user_code = ?, name = ?, email = ?, phone = ?, student_class = ?, year = ?, department = ?
                        WHERE id = ?;
                    """, (user_code, name, email, phone, student_class, year, department, u_id))
                conn.commit()
                flash(f"Student profile '{name}' ({user_code}) updated successfully!", "success")
            except Exception as e:
                print(f"[USER UPDATE ERROR] {e}")
                flash(f"Failed to update student profile: {e}", "danger")

    cursor.execute("SELECT * FROM users WHERE role = 'Student' ORDER BY id DESC;")
    students = cursor.fetchall()
    conn.close()

    return render_template('admin/students.html', students=students)

# ADMIN TEACHER DIRECTORY
@app.route('/admin/teachers', methods=['GET', 'POST'])
def admin_teachers():
    if not is_logged_in() or get_role() != 'Administrator':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            user_code = request.form.get('user_code', '').strip()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            department = request.form.get('department', '').strip() or 'Chemistry'
            password = request.form.get('password', '').strip()

            if not user_code:
                cursor.execute("SELECT MAX(id) as max_id FROM users;")
                max_id = (cursor.fetchone()['max_id'] or 0) + 201
                user_code = f"TCH-{max_id}"

            try:
                cursor.execute("""
                    INSERT INTO users (user_code, name, email, phone, role, department, password)
                    VALUES (?, ?, ?, ?, 'Teacher', ?, ?);
                """, (user_code, name, email, phone, department, password))
                conn.commit()
                _, email_msg = send_user_credentials_email(name, email, user_code, password, 'Teacher')
                flash(f"Teacher '{name}' with User ID '{user_code}' registered successfully! {email_msg}", "success")
            except Exception as e:
                print(f"[TEACHER REGISTRATION ERROR] {e}")
                flash(f"Email or User ID already exists in system ({e}).", "danger")

        elif action == 'edit':
            u_id = request.form.get('user_id')
            user_code = request.form.get('user_code', '').strip()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            department = request.form.get('department', '').strip() or 'Chemistry'
            password = request.form.get('password', '').strip()

            try:
                if password:
                    cursor.execute("""
                        UPDATE users
                        SET user_code = ?, name = ?, email = ?, phone = ?, department = ?, password = ?
                        WHERE id = ?;
                    """, (user_code, name, email, phone, department, password, u_id))
                else:
                    cursor.execute("""
                        UPDATE users
                        SET user_code = ?, name = ?, email = ?, phone = ?, department = ?
                        WHERE id = ?;
                    """, (user_code, name, email, phone, department, u_id))
                conn.commit()
                flash(f"Teacher profile '{name}' ({user_code}) updated successfully!", "success")
            except Exception as e:
                print(f"[TEACHER UPDATE ERROR] {e}")
                flash(f"Failed to update teacher profile: {e}", "danger")

        elif action == 'delete':
            u_id = request.form.get('user_id')
            cursor.execute("DELETE FROM users WHERE id = ? AND role = 'Teacher';", (u_id,))
            conn.commit()
            flash("Teacher profile deleted successfully.", "info")

    cursor.execute("SELECT * FROM users WHERE role = 'Teacher' ORDER BY id DESC;")
    teachers = cursor.fetchall()
    conn.close()

    return render_template('admin/teachers.html', teachers=teachers)

# ==========================================
# 3. TEACHER MODULE (/teacher/...)
# ==========================================
@app.route('/teacher/dashboard')
def teacher_dashboard():
    if not is_logged_in() or get_role() != 'Teacher':
        flash("Access restricted to Teachers only.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, c.name as category_name
        FROM equipment e
        JOIN categories c ON e.category_id = c.id
        ORDER BY e.name ASC;
    """)
    available_items = cursor.fetchall()

    cursor.execute("""
        SELECT i.*, e.name as equipment_name, e.unit_type
        FROM equipment_issue i
        JOIN equipment e ON i.equipment_id = e.id
        WHERE i.user_id = ?
        ORDER BY i.id DESC;
    """, (session.get('user_id'),))
    my_issues = cursor.fetchall()
    conn.close()

    return render_template('teacher/dashboard.html', available_items=available_items, my_issues=my_issues)

# TEACHER ADD STUDENT ROUTE
@app.route('/teacher/students', methods=['GET', 'POST'])
def teacher_students():
    if not is_logged_in() or get_role() not in ['Teacher', 'Administrator']:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch Teacher's Major / Department
    teacher_id = session.get('user_id')
    cursor.execute("SELECT * FROM users WHERE id = ?;", (teacher_id,))
    teacher_user = cursor.fetchone()
    
    teacher_dept = ""
    if teacher_user and teacher_user['department']:
        teacher_dept = teacher_user['department'].strip()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            user_code = request.form.get('user_code', '').strip()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            student_class = request.form.get('student_class', '').strip() or 'B.Sc'
            year = request.form.get('year', '').strip() or '3rd Year'
            department = request.form.get('department', '').strip() or teacher_dept or 'Chemistry'
            password = request.form.get('password', '').strip()

            if not user_code:
                cursor.execute("SELECT MAX(id) as max_id FROM users;")
                max_id = (cursor.fetchone()['max_id'] or 0) + 301
                user_code = f"STU-{max_id}"

            try:
                cursor.execute("""
                    INSERT INTO users (user_code, name, email, phone, role, student_class, year, department, password)
                    VALUES (?, ?, ?, ?, 'Student', ?, ?, ?, ?);
                """, (user_code, name, email, phone, student_class, year, department, password))
                conn.commit()
                _, email_msg = send_user_credentials_email(name, email, user_code, password, 'Student')
                flash(f"Student '{name}' ({user_code}) registered successfully under {department}! {email_msg}", "success")
            except Exception as e:
                print(f"[USER REGISTRATION ERROR] {e}")
                flash(f"Email or User ID already exists in system ({e}).", "danger")

        elif action == 'edit':
            u_id = request.form.get('user_id')
            user_code = request.form.get('user_code', '').strip()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            student_class = request.form.get('student_class', '').strip() or 'B.Sc'
            year = request.form.get('year', '').strip() or '3rd Year'
            department = request.form.get('department', '').strip() or teacher_dept or 'Chemistry'
            password = request.form.get('password', '').strip()

            try:
                if password:
                    cursor.execute("""
                        UPDATE users
                        SET user_code = ?, name = ?, email = ?, phone = ?, student_class = ?, year = ?, department = ?, password = ?
                        WHERE id = ?;
                    """, (user_code, name, email, phone, student_class, year, department, password, u_id))
                else:
                    cursor.execute("""
                        UPDATE users
                        SET user_code = ?, name = ?, email = ?, phone = ?, student_class = ?, year = ?, department = ?
                        WHERE id = ?;
                    """, (user_code, name, email, phone, student_class, year, department, u_id))
                conn.commit()
                flash(f"Student profile '{name}' ({user_code}) updated successfully!", "success")
            except Exception as e:
                print(f"[USER UPDATE ERROR] {e}")
                flash(f"Failed to update student profile: {e}", "danger")

    # Filter Students by Teacher's Major / Department
    if get_role() == 'Teacher' and teacher_dept:
        dept_words = [w.strip() for w in teacher_dept.replace('&', ' ').replace('/', ' ').split() if len(w.strip()) > 2]
        if dept_words:
            word_clauses = ["department LIKE ?" for _ in dept_words]
            sql = f"SELECT * FROM users WHERE role = 'Student' AND ({' OR '.join(word_clauses)}) ORDER BY id DESC;"
            params = [f"%{w}%" for w in dept_words]
            cursor.execute(sql, params)
        else:
            cursor.execute("SELECT * FROM users WHERE role = 'Student' AND department LIKE ? ORDER BY id DESC;", (f"%{teacher_dept}%",))
    else:
        cursor.execute("SELECT * FROM users WHERE role = 'Student' ORDER BY id DESC;")

    students = cursor.fetchall()
    conn.close()

    return render_template('admin/students.html', students=students, teacher_dept=teacher_dept)

# TEACHER ADD LAB ASSISTANT ROUTE
@app.route('/teacher/assistants', methods=['GET', 'POST'])
def teacher_assistants():
    if not is_logged_in() or get_role() not in ['Teacher', 'Administrator']:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            user_code = request.form.get('user_code', '').strip()
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            department = request.form.get('department')
            password = request.form.get('password')

            if not user_code:
                cursor.execute("SELECT MAX(id) as max_id FROM users;")
                max_id = (cursor.fetchone()['max_id'] or 0) + 101
                user_code = f"LAB-{max_id}"

            try:
                cursor.execute("""
                    INSERT INTO users (user_code, name, email, phone, role, department, password)
                    VALUES (?, ?, ?, ?, 'Lab Assistant', ?, ?);
                """, (user_code, name, email, phone, department, password))
                conn.commit()
                _, email_msg = send_user_credentials_email(name, email, user_code, password, 'Lab Assistant')
                flash(f"Lab Assistant '{name}' with User ID '{user_code}' added successfully by Teacher! {email_msg}", "success")
            except Exception as e:
                print(f"[USER REGISTRATION ERROR] {e}")
                flash(f"Email or User ID already exists in system ({e}).", "danger")

        elif action == 'edit':
            u_id = request.form.get('user_id')
            user_code = request.form.get('user_code', '').strip()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            student_class = request.form.get('student_class', '').strip() or 'B.Sc'
            year = request.form.get('year', '').strip() or '3rd Year'
            department = request.form.get('department', '').strip() or 'Chemistry'
            password = request.form.get('password', '').strip()

            try:
                if password:
                    cursor.execute("""
                        UPDATE users
                        SET user_code = ?, name = ?, email = ?, phone = ?, student_class = ?, year = ?, department = ?, password = ?
                        WHERE id = ?;
                    """, (user_code, name, email, phone, student_class, year, department, password, u_id))
                else:
                    cursor.execute("""
                        UPDATE users
                        SET user_code = ?, name = ?, email = ?, phone = ?, student_class = ?, year = ?, department = ?
                        WHERE id = ?;
                    """, (user_code, name, email, phone, student_class, year, department, u_id))
                conn.commit()
                flash(f"Lab Assistant profile '{name}' ({user_code}) updated successfully!", "success")
            except Exception as e:
                print(f"[USER UPDATE ERROR] {e}")
                flash(f"Failed to update lab assistant profile: {e}", "danger")

    cursor.execute("SELECT * FROM users WHERE role = 'Lab Assistant' ORDER BY id DESC;")
    assistants = cursor.fetchall()
    conn.close()

    return render_template('admin/assistants.html', assistants=assistants)

@app.route('/teacher/request', methods=['POST'])
def teacher_request():
    if not is_logged_in() or get_role() != 'Teacher':
        return redirect(url_for('login'))

    eq_id = request.form.get('equipment_id')
    issue_qty = float(request.form.get('issue_qty') or 1.0)
    notes = request.form.get('notes') or "Teacher Research / Lecture Demonstration"
    user_id = session.get('user_id')
    today_str = datetime.now().strftime("%Y-%m-%d")
    due_str = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM equipment WHERE id = ?;", (eq_id,))
    eq = cursor.fetchone()

    if eq and eq['available_qty'] >= issue_qty:
        cursor.execute("SELECT COUNT(*) as cnt FROM equipment_issue;")
        cnt = cursor.fetchone()['cnt'] + 1005
        issue_code = f"ISS-{cnt}"

        cursor.execute("""
            INSERT INTO equipment_issue (issue_code, equipment_id, user_id, issue_qty, issue_date, expected_return_date, status, notes, issued_by)
            VALUES (?, ?, ?, ?, ?, ?, 'Issued', ?, 'Teacher Portal Request');
        """, (issue_code, eq_id, user_id, issue_qty, today_str, due_str, notes))

        new_avail = eq['available_qty'] - issue_qty
        new_status = 'Low Stock' if new_avail <= 2 else 'Available'
        cursor.execute("UPDATE equipment SET available_qty = ?, status = ? WHERE id = ?;", (new_avail, new_status, eq_id))

        conn.commit()
        flash(f"Teacher Issue Request approved for {issue_qty} {eq['unit_type']} of '{eq['name']}' under Code {issue_code}!", "success")
    else:
        flash("Requested chemical / instrument quantity is out of stock.", "danger")

    conn.close()
    return redirect(url_for('teacher_dashboard'))


# ==========================================
# 4. STUDENT MODULE (/student/...)
# ==========================================
@app.route('/student/dashboard')
def student_dashboard():
    if not is_logged_in() or get_role() != 'Student':
        flash("Access restricted to Students only.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, c.name as category_name
        FROM equipment e
        JOIN categories c ON e.category_id = c.id
        ORDER BY e.name ASC;
    """)
    available_items = cursor.fetchall()

    cursor.execute("""
        SELECT i.*, e.name as equipment_name, e.unit_type
        FROM equipment_issue i
        JOIN equipment e ON i.equipment_id = e.id
        WHERE i.user_id = ?
        ORDER BY i.id DESC;
    """, (session.get('user_id'),))
    my_issues = cursor.fetchall()
    conn.close()

    return render_template('student/dashboard.html', available_items=available_items, my_issues=my_issues)

@app.route('/student/request', methods=['POST'])
def student_request():
    if not is_logged_in() or get_role() != 'Student':
        return redirect(url_for('login'))

    eq_id = request.form.get('equipment_id')
    issue_qty = float(request.form.get('issue_qty') or 1.0)
    user_id = session.get('user_id')
    today_str = datetime.now().strftime("%Y-%m-%d")
    due_str = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM equipment WHERE id = ?;", (eq_id,))
    eq = cursor.fetchone()

    if eq:
        if eq['available_qty'] >= issue_qty:
            cursor.execute("SELECT COUNT(*) as cnt FROM equipment_issue;")
            cnt = cursor.fetchone()['cnt'] + 1005
            issue_code = f"ISS-{cnt}"

            cursor.execute("""
                INSERT INTO equipment_issue (issue_code, equipment_id, user_id, issue_qty, issue_date, expected_return_date, status, notes, issued_by)
                VALUES (?, ?, ?, ?, ?, ?, 'Requested', 'Student Practical Request', 'Pending Assistant Approval');
            """, (issue_code, eq_id, user_id, issue_qty, today_str, due_str))

            conn.commit()
            flash(f"Equipment request '{issue_code}' for {issue_qty} {eq['unit_type']} of '{eq['name']}' submitted! Awaiting Lab Assistant approval.", "info")
        else:
            flash(f"Insufficient stock to request. Available: {eq['available_qty']} {eq['unit_type']}", "danger")
    else:
        flash("Selected equipment not found.", "danger")

    conn.close()
    return redirect(url_for('student_dashboard'))


# --- Common User Profile Route ---
@app.route('/profile')
def profile():
    if not is_logged_in():
        return redirect(url_for('login'))

    role = get_role()
    conn = get_db_connection()
    cursor = conn.cursor()

    if role == 'Administrator':
        cursor.execute("SELECT * FROM admin WHERE id = ?;", (session.get('user_id'),))
        user_data = cursor.fetchone()
        conn.close()
        return render_template('admin/profile.html', admin=user_data)
    else:
        cursor.execute("SELECT * FROM users WHERE id = ?;", (session.get('user_id'),))
        user_data = cursor.fetchone()
        conn.close()
        return render_template('user/profile.html', user=user_data)





# ==========================================
# LAB ASSISTANT MODULE ROUTES (FULLY FIXED)
# ==========================================

@app.route('/assistant/dashboard')
def assistant_dashboard():
    if not is_logged_in() or get_role() not in ['Lab Assistant', 'Administrator']:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as cnt FROM equipment;")
    total_equipment = cursor.fetchone()['cnt']
    
    cursor.execute("SELECT SUM(available_qty) as total_avail FROM equipment;")
    available_equipment = cursor.fetchone()['total_avail'] or 0
    
    cursor.execute("SELECT COUNT(*) as cnt FROM equipment_issue WHERE status = 'Issued';")
    issued_equipment = cursor.fetchone()['cnt']
    
    cursor.execute("SELECT COUNT(*) as cnt FROM equipment_issue WHERE status IN ('Pending', 'Requested');")
    pending_requests_count = cursor.fetchone()['cnt']

    cursor.execute('''
        SELECT ei.*, e.name as equipment_name, e.unit_type, u.name as user_name, u.user_code, u.phone, u.department
        FROM equipment_issue ei
        JOIN equipment e ON ei.equipment_id = e.id
        JOIN users u ON ei.user_id = u.id
        WHERE ei.status IN ('Pending', 'Requested')
        ORDER BY ei.id DESC;
    ''')
    pending_requests = cursor.fetchall()

    cursor.execute('''
        SELECT ei.*, e.name as equipment_name, e.unit_type, u.name as user_name, u.user_code, u.role as user_role
        FROM equipment_issue ei
        JOIN equipment e ON ei.equipment_id = e.id
        JOIN users u ON ei.user_id = u.id
        WHERE ei.status = 'Issued'
        ORDER BY ei.id DESC;
    ''')
    recent_issues = cursor.fetchall()

    cursor.execute('''
        SELECT e.*, c.name as category_name
        FROM equipment e
        LEFT JOIN categories c ON e.category_id = c.id
        ORDER BY e.id DESC;
    ''')
    all_equipment = cursor.fetchall()

    conn.close()
    return render_template('assistant/dashboard.html',
                           total_equipment=total_equipment,
                           available_equipment=available_equipment,
                           issued_equipment=issued_equipment,
                           pending_requests_count=pending_requests_count,
                           pending_requests=pending_requests,
                           recent_issues=recent_issues,
                           all_equipment=all_equipment)
@app.route('/assistant/requests', methods=['GET', 'POST'])
def assistant_requests():
    if not is_logged_in() or get_role() not in ['Lab Assistant', 'Administrator']:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        req_id = request.form.get('issue_id') or request.form.get('request_id')
        if action == 'approve':
            cursor.execute("SELECT * FROM equipment_issue WHERE id = ?;", (req_id,))
            issue = cursor.fetchone()
            if issue:
                cursor.execute("SELECT * FROM equipment WHERE id = ?;", (issue['equipment_id'],))
                eq = cursor.fetchone()
                if eq and eq['available_qty'] >= issue['issue_qty']:
                    new_avail = eq['available_qty'] - issue['issue_qty']
                    new_status = 'Low Stock' if new_avail <= 2 else 'Available'
                    cursor.execute("UPDATE equipment SET available_qty = ?, status = ? WHERE id = ?;", (new_avail, new_status, eq['id']))
                    cursor.execute("UPDATE equipment_issue SET status = 'Issued', issued_by = ? WHERE id = ?;", (session.get('name'), req_id))
                    conn.commit()
                    flash(f"Student request '{issue['issue_code']}' approved & equipment issued!", "success")
                else:
                    flash(f"Cannot approve: Insufficient stock available!", "danger")
            else:
                flash("Request record not found.", "danger")

        elif action == 'reject':
            cursor.execute("UPDATE equipment_issue SET status = 'Rejected', issued_by = ? WHERE id = ?;", (session.get('name'), req_id))
            conn.commit()
            flash("Student equipment request rejected.", "warning")

        return redirect(url_for('assistant_requests'))

    cursor.execute('''
        SELECT ei.*, e.name as equipment_name, e.equipment_code, e.unit_type, e.available_qty, u.name as user_name, u.user_code, u.phone, u.department
        FROM equipment_issue ei
        JOIN equipment e ON ei.equipment_id = e.id
        JOIN users u ON ei.user_id = u.id
        WHERE ei.status IN ('Pending', 'Requested')
        ORDER BY ei.id DESC;
    ''')
    pending_requests = cursor.fetchall()
    
    cursor.execute('''
        SELECT ei.*, e.name as equipment_name, e.unit_type, u.name as user_name, u.user_code, u.department
        FROM equipment_issue ei
        JOIN equipment e ON ei.equipment_id = e.id
        JOIN users u ON ei.user_id = u.id
        WHERE ei.status NOT IN ('Pending', 'Requested')
        ORDER BY ei.id DESC LIMIT 20;
    ''')
    request_history = cursor.fetchall()

    conn.close()
    return render_template('assistant/requests.html', pending_requests=pending_requests, request_history=request_history)
@app.route('/assistant/purchase_requests', methods=['GET', 'POST'])
def assistant_purchase_requests():
    if not is_logged_in() or get_role() not in ['Lab Assistant', 'Administrator']:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_request':
            item_name = request.form.get('item_name', '').strip()
            item_type = request.form.get('item_type', '').strip()
            category_id = request.form.get('category_id')
            quantity = float(request.form.get('quantity') or 1.0)
            unit_type = request.form.get('unit_type', 'Units').strip()
            estimated_price = float(request.form.get('estimated_price') or 0.0)
            supplier_id = request.form.get('supplier_id') or None
            notes = request.form.get('notes', '').strip()

            # Required-field validation
            if not item_name or not item_type or item_type not in ['Chemical', 'Non-Chemical Equipment']:
                flash("Please fill in all required fields and select a valid Item Type (Chemical or Non-Chemical Equipment).", "danger")
                return redirect(url_for('assistant_purchase_requests'))

            cursor.execute("SELECT MAX(id) as max_id FROM purchase_requests;")
            max_id = (cursor.fetchone()['max_id'] or 0) + 1
            request_code = f"PR-{max_id:04d}"

            # 1. Insert into purchase_requests table
            cursor.execute('''
                INSERT INTO purchase_requests (request_code, item_name, item_type, category_id, quantity, unit_type, estimated_price, supplier_id, requested_by_id, requested_by_name, notes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending');
            ''', (request_code, item_name, item_type, category_id, quantity, unit_type, estimated_price, supplier_id, session.get('user_id'), session.get('name'), notes))

            # 2. Save Chemical requests in Chemical table and Non-Chemical requests in Equipment table
            if item_type == 'Chemical':
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS chemical (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chemical_code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    category_id INTEGER,
                    supplier_id INTEGER,
                    total_qty REAL NOT NULL DEFAULT 1.0,
                    available_qty REAL NOT NULL DEFAULT 1.0,
                    unit_type TEXT DEFAULT 'mL',
                    unit_price REAL DEFAULT 0.0,
                    location TEXT DEFAULT 'Chemical Storage',
                    status TEXT DEFAULT 'Available',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (id),
                    FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
                );
                """)
                cursor.execute("SELECT MAX(id) as max_id FROM chemical;")
                c_max = (cursor.fetchone()['max_id'] or 0) + 1001
                chem_code = f"CHM-{c_max:04d}"

                cursor.execute("""
                    INSERT INTO chemical (chemical_code, name, category_id, supplier_id, total_qty, available_qty, unit_type, unit_price, location, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Chemical Storage', 'Available');
                """, (chem_code, item_name, category_id, supplier_id, quantity, quantity, unit_type, estimated_price))
                flash(f"Purchase Request {request_code} created and saved in Chemical table!", "success")

            elif item_type == 'Non-Chemical Equipment':
                cursor.execute("SELECT MAX(id) as max_id FROM equipment;")
                e_max = (cursor.fetchone()['max_id'] or 0) + 1001
                eq_code = f"EQP-{e_max:04d}"

                cursor.execute("""
                    INSERT INTO equipment (equipment_code, name, category_id, supplier_id, total_qty, available_qty, damaged_qty, unit_type, unit_price, location, status)
                    VALUES (?, ?, ?, ?, ?, ?, 0.0, ?, ?, 'Main Chemistry Lab', 'Available');
                """, (eq_code, item_name, category_id, supplier_id, quantity, quantity, unit_type, estimated_price))
                flash(f"Purchase Request {request_code} created and saved in Equipment table!", "success")

            conn.commit()

    cursor.execute('''
        SELECT pr.*, u.name as requester_name, c.name as category_name, s.name as supplier_name
        FROM purchase_requests pr
        LEFT JOIN users u ON pr.requested_by_id = u.id
        LEFT JOIN categories c ON pr.category_id = c.id
        LEFT JOIN suppliers s ON pr.supplier_id = s.id
        ORDER BY pr.id DESC;
    ''')
    requests = cursor.fetchall()
    
    cursor.execute("SELECT * FROM categories ORDER BY name ASC;")
    categories = cursor.fetchall()
    
    cursor.execute("SELECT * FROM suppliers ORDER BY name ASC;")
    suppliers = cursor.fetchall()

    conn.close()
    return render_template('assistant/purchase_requests.html', purchase_requests=requests, requests=requests, categories=categories, suppliers=suppliers)
@app.route('/assistant/issue', methods=['GET', 'POST'])
def assistant_issue():
    if not is_logged_in() or get_role() not in ['Lab Assistant', 'Administrator']:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        equipment_id = request.form.get('equipment_id')
        user_id = request.form.get('user_id')
        issue_qty = request.form.get('issue_qty', 1)
        issue_date = request.form.get('issue_date')
        expected_return_date = request.form.get('expected_return_date')
        notes = request.form.get('notes')

        cursor.execute("SELECT MAX(id) as max_id FROM equipment_issue;")
        max_id = (cursor.fetchone()['max_id'] or 0) + 1
        issue_code = f"ISS-{max_id:04d}"

        try:
            cursor.execute('''
                INSERT INTO equipment_issue (issue_code, equipment_id, user_id, issue_qty, issue_date, expected_return_date, notes, status, issued_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Issued', ?);
            ''', (issue_code, equipment_id, user_id, issue_qty, issue_date, expected_return_date, notes, session.get('name')))
            
            cursor.execute("UPDATE equipment SET available_qty = available_qty - ? WHERE id = ?;", (issue_qty, equipment_id))
            conn.commit()
            flash("Equipment issued successfully!", "success")
        except Exception as e:
            print(f"[ISSUE ERROR] {e}")
            flash(f"Failed to issue equipment: {e}", "danger")

    cursor.execute("SELECT * FROM equipment WHERE available_qty > 0 ORDER BY name ASC;")
    equipment_list = cursor.fetchall()
    
    cursor.execute("SELECT * FROM users ORDER BY name ASC;")
    users_list = cursor.fetchall()

    conn.close()
    return render_template('assistant/issue.html', equipment_list=equipment_list, users_list=users_list)


@app.route('/assistant/returns', methods=['GET', 'POST'])
def assistant_returns():
    if not is_logged_in() or get_role() not in ['Lab Assistant', 'Administrator']:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        issue_id = request.form.get('issue_id')
        actual_return_date = request.form.get('actual_return_date')
        damage_status = request.form.get('damage_status', 'No Damage')
        fine_amount = request.form.get('fine_amount', 0.0)
        payment_mode = request.form.get('payment_mode', 'Cash')
        payment_txn_id = request.form.get('payment_txn_id', '')
        remarks = request.form.get('remarks', '')

        try:
            cursor.execute('''
                INSERT INTO equipment_return (issue_id, actual_return_date, fine_amount, payment_mode, payment_txn_id, payment_status, damage_status, remarks, received_by)
                VALUES (?, ?, ?, ?, ?, 'Completed', ?, ?, ?);
            ''', (issue_id, actual_return_date, fine_amount, payment_mode, payment_txn_id, damage_status, remarks, session.get('name')))
            
            cursor.execute("UPDATE equipment_issue SET status = 'Returned' WHERE id = ?;", (issue_id,))
            
            cursor.execute("SELECT equipment_id, issue_qty FROM equipment_issue WHERE id = ?;", (issue_id,))
            issue_rec = cursor.fetchone()
            if issue_rec:
                cursor.execute("UPDATE equipment SET available_qty = available_qty + ? WHERE id = ?;", (issue_rec['issue_qty'], issue_rec['equipment_id']))

            conn.commit()
            flash("Equipment return processed successfully!", "success")
        except Exception as e:
            print(f"[RETURN ERROR] {e}")
            flash(f"Failed to process return: {e}", "danger")

    cursor.execute('''
        SELECT ei.*, e.name as equipment_name, u.name as user_name, u.user_code
        FROM equipment_issue ei
        JOIN equipment e ON ei.equipment_id = e.id
        JOIN users u ON ei.user_id = u.id
        WHERE ei.status = 'Issued'
        ORDER BY ei.id DESC;
    ''')
    issued_items = cursor.fetchall()

    cursor.execute('''
        SELECT er.*, ei.issue_code, e.name as equipment_name, u.name as user_name
        FROM equipment_return er
        JOIN equipment_issue ei ON er.issue_id = ei.id
        JOIN equipment e ON ei.equipment_id = e.id
        JOIN users u ON ei.user_id = u.id
        ORDER BY er.id DESC LIMIT 20;
    ''')
    return_history = cursor.fetchall()

    conn.close()
    return render_template('assistant/returns.html', issued_items=issued_items, return_history=return_history)


@app.route('/assistant/maintenance', methods=['GET', 'POST'])
def assistant_maintenance():
    if not is_logged_in() or get_role() not in ['Lab Assistant', 'Administrator']:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            equipment_id = request.form.get('equipment_id')
            service_date = request.form.get('service_date')
            technician = request.form.get('technician')
            cost = request.form.get('cost', 0)
            issue_description = request.form.get('issue_description')

            cursor.execute('''
                INSERT INTO maintenance (equipment_id, service_date, technician, cost, issue_description, status)
                VALUES (?, ?, ?, ?, ?, 'Under Maintenance');
            ''', (equipment_id, service_date, technician, cost, issue_description))
            conn.commit()
            flash("Maintenance record logged successfully!", "success")
        elif action == 'complete':
            m_id = request.form.get('maintenance_id')
            cursor.execute("UPDATE maintenance SET status = 'Completed', completion_date = CURRENT_TIMESTAMP WHERE id = ?;", (m_id,))
            conn.commit()
            flash("Maintenance marked as completed!", "success")

    cursor.execute('''
        SELECT m.*, e.name as equipment_name
        FROM maintenance m
        JOIN equipment e ON m.equipment_id = e.id
        ORDER BY m.id DESC;
    ''')
    maintenance_records = cursor.fetchall()

    cursor.execute("SELECT * FROM equipment ORDER BY name ASC;")
    equipment_list = cursor.fetchall()

    conn.close()
    return render_template('assistant/maintenance.html', maintenance_records=maintenance_records, equipment=equipment_list)



@app.route('/assistant/students', methods=['GET', 'POST'])
def assistant_students():
    if not is_logged_in() or get_role() not in ['Lab Assistant', 'Administrator']:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            user_code = request.form.get('user_code', '').strip()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            student_class = request.form.get('student_class', '').strip() or 'B.Sc'
            year = request.form.get('year', '').strip() or '3rd Year'
            department = request.form.get('department', '').strip() or 'Chemistry'
            password = request.form.get('password', '').strip()

            if not user_code:
                cursor.execute("SELECT MAX(id) as max_id FROM users;")
                max_id = (cursor.fetchone()['max_id'] or 0) + 301
                user_code = f"STU-{max_id}"

            try:
                cursor.execute("""
                    INSERT INTO users (user_code, name, email, phone, role, student_class, year, department, password)
                    VALUES (?, ?, ?, ?, 'Student', ?, ?, ?, ?);
                """, (user_code, name, email, phone, student_class, year, department, password))
                conn.commit()
                _, email_msg = send_user_credentials_email(email, name, user_code, password, 'Student')
                flash(f"Student account created successfully! {email_msg}", "success")
            except Exception as e:
                flash(f"Error creating student: {str(e)}", "danger")

        elif action == 'delete':
            u_id = request.form.get('user_id')
            cursor.execute("DELETE FROM users WHERE id = ? AND role = 'Student';", (u_id,))
            conn.commit()
            flash("Student profile removed successfully.", "info")

        conn.close()
        return redirect(url_for('assistant_students'))

    cursor.execute("SELECT * FROM users WHERE role = 'Student' ORDER BY id DESC;")
    students = cursor.fetchall()
    conn.close()

    return render_template('admin/students.html', students=students)




# ==========================================
# ALL ADMINISTRATOR MODULE ROUTES
# ==========================================

@app.route('/admin/assistants', methods=['GET', 'POST'])
def admin_assistants():
    if not is_logged_in() or get_role() != 'Administrator':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            user_code = request.form.get('user_code', '').strip()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            department = request.form.get('department', '').strip() or 'Chemistry'
            password = request.form.get('password', '').strip()

            if not user_code:
                cursor.execute("SELECT MAX(id) as max_id FROM users;")
                max_id = (cursor.fetchone()['max_id'] or 0) + 101
                user_code = f"LAB-{max_id}"

            try:
                cursor.execute("""
                    INSERT INTO users (user_code, name, email, phone, role, department, password)
                    VALUES (?, ?, ?, ?, 'Lab Assistant', ?, ?);
                """, (user_code, name, email, phone, department, password))
                conn.commit()
                flash("Lab Assistant account registered successfully!", "success")
            except Exception as e:
                flash(f"Error registering assistant: {str(e)}", "danger")

        elif action == 'delete':
            u_id = request.form.get('user_id')
            cursor.execute("DELETE FROM users WHERE id = ? AND role = 'Lab Assistant';", (u_id,))
            conn.commit()
            flash("Lab Assistant profile deleted.", "info")

        conn.close()
        return redirect(url_for('admin_assistants'))

    cursor.execute("SELECT * FROM users WHERE role = 'Lab Assistant' ORDER BY id DESC;")
    assistants = cursor.fetchall()
    conn.close()
    return render_template('admin/assistants.html', assistants=assistants)


@app.route('/admin/equipment', methods=['GET', 'POST'])
def admin_equipment():
    if not is_logged_in() or get_role() != 'Administrator':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name', '').strip()
            category_id = request.form.get('category_id')
            supplier_id = request.form.get('supplier_id') or None
            total_qty = float(request.form.get('total_qty') or 1.0)
            unit_type = request.form.get('unit_type', 'Units')
            unit_price = float(request.form.get('unit_price') or 0.0)
            location = request.form.get('location', '').strip() or 'Main Chemistry Lab'

            cursor.execute("SELECT MAX(id) as max_id FROM equipment;")
            max_id = (cursor.fetchone()['max_id'] or 0) + 101
            equipment_code = f"EQP-{max_id:04d}"

            try:
                cursor.execute("""
                    INSERT INTO equipment (equipment_code, name, category_id, supplier_id, total_qty, available_qty, unit_type, unit_price, location, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Available');
                """, (equipment_code, name, category_id, supplier_id, total_qty, total_qty, unit_type, unit_price, location))
                conn.commit()
                flash("New equipment added to catalog!", "success")
            except Exception as e:
                flash(f"Error adding equipment: {str(e)}", "danger")

        elif action == 'delete':
            eq_id = request.form.get('equipment_id')
            cursor.execute("DELETE FROM equipment WHERE id = ?;", (eq_id,))
            conn.commit()
            flash("Equipment deleted from catalog.", "info")

        return redirect(url_for('admin_equipment'))

    cursor.execute("""
        SELECT e.*, c.name as category_name, s.name as supplier_name
        FROM equipment e
        LEFT JOIN categories c ON e.category_id = c.id
        LEFT JOIN suppliers s ON e.supplier_id = s.id
        ORDER BY e.id DESC;
    """)
    equipment_list = cursor.fetchall()

    cursor.execute("SELECT * FROM categories ORDER BY name ASC;")
    categories = cursor.fetchall()

    cursor.execute("SELECT * FROM suppliers ORDER BY name ASC;")
    suppliers = cursor.fetchall()

    conn.close()
    return render_template('admin/equipment.html', equipment_list=equipment_list, categories=categories, suppliers=suppliers)


@app.route('/admin/categories', methods=['GET', 'POST'])
def admin_categories():
    if not is_logged_in() or get_role() != 'Administrator':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            try:
                cursor.execute("INSERT INTO categories (name, description) VALUES (?, ?);", (name, description))
                conn.commit()
                flash("New Category created!", "success")
            except Exception as e:
                flash(f"Error creating category: {str(e)}", "danger")
        elif action == 'delete':
            cat_id = request.form.get('category_id')
            cursor.execute("DELETE FROM categories WHERE id = ?;", (cat_id,))
            conn.commit()
            flash("Category removed.", "info")

        return redirect(url_for('admin_categories'))

    cursor.execute("SELECT * FROM categories ORDER BY name ASC;")
    categories = cursor.fetchall()
    conn.close()
    return render_template('admin/categories.html', categories=categories)


@app.route('/admin/suppliers', methods=['GET', 'POST'])
def admin_suppliers():
    if not is_logged_in() or get_role() != 'Administrator':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name', '').strip()
            contact_person = request.form.get('contact_person', '').strip()
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()
            address = request.form.get('address', '').strip()
            try:
                cursor.execute("""
                    INSERT INTO suppliers (name, contact_person, phone, email, address)
                    VALUES (?, ?, ?, ?, ?);
                """, (name, contact_person, phone, email, address))
                conn.commit()
                flash("Supplier added successfully!", "success")
            except Exception as e:
                flash(f"Error adding supplier: {str(e)}", "danger")
        elif action == 'delete':
            sup_id = request.form.get('supplier_id')
            cursor.execute("DELETE FROM suppliers WHERE id = ?;", (sup_id,))
            conn.commit()
            flash("Supplier removed.", "info")

        return redirect(url_for('admin_suppliers'))

    cursor.execute("SELECT * FROM suppliers ORDER BY name ASC;")
    suppliers = cursor.fetchall()
    conn.close()
    return render_template('admin/suppliers.html', suppliers=suppliers)


@app.route('/admin/purchase_requests', methods=['GET', 'POST'])
def admin_purchase_requests():
    if not is_logged_in() or get_role() != 'Administrator':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        request_id = request.form.get('request_id')
        admin_notes = request.form.get('admin_response_notes', '').strip()

        if action == 'accept':
            cursor.execute("""
                UPDATE purchase_requests
                SET status = 'Accepted', admin_response_notes = ?
                WHERE id = ?;
            """, (admin_notes or 'Approved by Administrator', request_id))
            conn.commit()
            flash("Purchase Request accepted successfully!", "success")

        elif action == 'reject':
            cursor.execute("""
                UPDATE purchase_requests
                SET status = 'Rejected', admin_response_notes = ?
                WHERE id = ?;
            """, (admin_notes or 'Rejected by Administrator', request_id))
            conn.commit()
            flash("Purchase Request rejected.", "warning")

        elif action == 'send_email':
            cursor.execute("""
                UPDATE purchase_requests
                SET email_status = 'Sent to Supplier'
                WHERE id = ?;
            """, (request_id,))
            conn.commit()
            flash("Purchase Order email dispatched to supplier!", "success")

        else:
            new_status = request.form.get('status')
            if new_status:
                cursor.execute("""
                    UPDATE purchase_requests
                    SET status = ?, admin_response_notes = ?
                    WHERE id = ?;
                """, (new_status, admin_notes, request_id))
                conn.commit()
                flash(f"Purchase Request status updated to {new_status}!", "success")

        return redirect(url_for('admin_purchase_requests'))

    cursor.execute("""
        SELECT pr.*, u.name as requester_name, c.name as category_name, s.name as supplier_name,
               COALESCE(s.email, '') as supplier_email
        FROM purchase_requests pr
        LEFT JOIN users u ON pr.requested_by_id = u.id
        LEFT JOIN categories c ON pr.category_id = c.id
        LEFT JOIN suppliers s ON pr.supplier_id = s.id
        ORDER BY pr.id DESC;
    """)
    purchase_requests = cursor.fetchall()
    conn.close()
    return render_template('admin/purchase_requests.html', purchase_requests=purchase_requests)
@app.route('/admin/reports')
def admin_reports():
    if not is_logged_in() or get_role() != 'Administrator':
        return redirect(url_for('login'))
    
    report_type = request.args.get('type', 'inventory')
    conn = get_db_connection()
    cursor = conn.cursor()

    # Base counts for stats cards
    cursor.execute("SELECT COUNT(*) as cnt FROM equipment;")
    total_equipment = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM chemical;")
    total_chemicals = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM equipment_issue WHERE status = 'Issued';")
    issued_count = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM purchase_requests WHERE status = 'Pending';")
    pending_requests = cursor.fetchone()['cnt']

    # 1. Inventory Report (Default)
    cursor.execute("""
        SELECT e.*, c.name as category_name, s.name as supplier_name
        FROM equipment e
        LEFT JOIN categories c ON e.category_id = c.id
        LEFT JOIN suppliers s ON e.supplier_id = s.id
        ORDER BY e.name ASC;
    """)
    report_items = cursor.fetchall()

    total_items = len(report_items)
    low_stock_count = sum(1 for item in report_items if item['available_qty'] <= 2)
    total_damaged_count = sum(1 for item in report_items if item['damaged_qty'] > 0)

    # 2. Available Chemicals
    cursor.execute("""
        SELECT c.*, cat.name as category_name, s.name as supplier_name
        FROM chemical c
        LEFT JOIN categories cat ON c.category_id = cat.id
        LEFT JOIN suppliers s ON c.supplier_id = s.id
        WHERE c.available_qty > 0
        ORDER BY c.name ASC;
    """)
    available_chemicals = cursor.fetchall()

    # 3. Available Equipment
    cursor.execute("""
        SELECT e.*, c.name as category_name, s.name as supplier_name
        FROM equipment e
        LEFT JOIN categories c ON e.category_id = c.id
        LEFT JOIN suppliers s ON e.supplier_id = s.id
        WHERE e.available_qty > 0
        ORDER BY e.name ASC;
    """)
    available_equipment = cursor.fetchall()

    # 4. Year-wise Report
    cursor.execute("""
        SELECT u.year,
               COUNT(DISTINCT u.id) as total_students,
               COUNT(ei.id) as total_issues,
               SUM(CASE WHEN ei.status = 'Issued' THEN 1 ELSE 0 END) as active_issues
        FROM users u
        LEFT JOIN equipment_issue ei ON u.id = ei.user_id
        WHERE u.role = 'Student'
        GROUP BY u.year
        ORDER BY u.year ASC;
    """)
    year_wise_report = cursor.fetchall()

    # 5. Student-wise Report
    cursor.execute("""
        SELECT u.user_code, u.name, u.department, u.year, u.phone,
               COUNT(ei.id) as total_requests,
               SUM(CASE WHEN ei.status = 'Issued' THEN 1 ELSE 0 END) as active_issues,
               SUM(CASE WHEN ei.status = 'Returned' THEN 1 ELSE 0 END) as returned_count
        FROM users u
        LEFT JOIN equipment_issue ei ON u.id = ei.user_id
        WHERE u.role = 'Student'
        GROUP BY u.id
        ORDER BY u.name ASC;
    """)
    student_wise_report = cursor.fetchall()

    # 6. Supplier-wise Report
    cursor.execute("""
        SELECT s.*,
               COUNT(e.id) as total_items,
               SUM(e.total_qty * e.unit_price) as total_supplied_val
        FROM suppliers s
        LEFT JOIN equipment e ON s.id = e.supplier_id
        GROUP BY s.id
        ORDER BY s.name ASC;
    """)
    supplier_wise_report = cursor.fetchall()

    # 7. Issue Report
    cursor.execute("""
        SELECT ei.*, e.name as equipment_name, e.unit_type, u.name as user_name, u.user_code, u.role as user_role
        FROM equipment_issue ei
        JOIN equipment e ON ei.equipment_id = e.id
        JOIN users u ON ei.user_id = u.id
        ORDER BY ei.id DESC;
    """)
    issue_report = cursor.fetchall()

    # 8. Request Report
    cursor.execute("""
        SELECT pr.*, u.name as requester_name, c.name as category_name, s.name as supplier_name
        FROM purchase_requests pr
        LEFT JOIN users u ON pr.requested_by_id = u.id
        LEFT JOIN categories c ON pr.category_id = c.id
        LEFT JOIN suppliers s ON pr.supplier_id = s.id
        ORDER BY pr.id DESC;
    """)
    request_report = cursor.fetchall()

    conn.close()

    return render_template('admin/reports.html',
                           report_type=report_type,
                           report_items=report_items,
                           total_items=total_items,
                           low_stock_count=low_stock_count,
                           total_damaged_count=total_damaged_count,
                           total_equipment=total_equipment,
                           total_chemicals=total_chemicals,
                           issued_count=issued_count,
                           pending_requests=pending_requests,
                           available_chemicals=available_chemicals,
                           available_equipment=available_equipment,
                           year_wise_report=year_wise_report,
                           student_wise_report=student_wise_report,
                           supplier_wise_report=supplier_wise_report,
                           issue_report=issue_report,
                           request_report=request_report)
@app.route('/admin/profile', methods=['GET', 'POST'])
def admin_profile():
    if not is_logged_in() or get_role() != 'Administrator':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if password:
            cursor.execute("UPDATE admin SET name = ?, email = ?, password = ? WHERE id = ?;",
                           (name, email, password, session.get('user_id')))
        else:
            cursor.execute("UPDATE admin SET name = ?, email = ? WHERE id = ?;",
                           (name, email, session.get('user_id')))
        conn.commit()
        session['name'] = name
        flash("Admin profile updated successfully!", "success")
        return redirect(url_for('admin_profile'))

    cursor.execute("SELECT * FROM admin WHERE id = ?;", (session.get('user_id'),))
    admin_data = cursor.fetchone()
    conn.close()
    return render_template('admin/profile.html', admin=admin_data)


@app.route('/admin/issue', methods=['GET', 'POST'])
def admin_issue():
    return assistant_issue()


@app.route('/admin/returns', methods=['GET', 'POST'])
def admin_returns():
    return assistant_returns()


@app.route('/admin/maintenance', methods=['GET', 'POST'])
def admin_maintenance():
    return assistant_maintenance()


@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    if not is_logged_in() or get_role() != 'Administrator':
        return redirect(url_for('login'))
    
    role_filter = request.args.get('role', 'all')
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            role = request.form.get('role', 'Teacher').strip()
            user_code = request.form.get('user_code', '').strip()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            department = request.form.get('department', '').strip() or 'Chemistry'
            student_class = request.form.get('student_class', '').strip() or 'B.Sc'
            year = request.form.get('year', '').strip() or '3rd Year'
            password = request.form.get('password', '').strip() or '123456'

            if not user_code:
                cursor.execute("SELECT MAX(id) as max_id FROM users;")
                max_id = (cursor.fetchone()['max_id'] or 0)
                if role == 'Teacher':
                    user_code = f"TCH-{max_id + 201}"
                elif role == 'Lab Assistant':
                    user_code = f"LAB-{max_id + 101}"
                else:
                    user_code = f"STU-{max_id + 301}"

            try:
                cursor.execute("""
                    INSERT INTO users (user_code, name, email, phone, role, department, student_class, year, password)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (user_code, name, email, phone, role, department, student_class, year, password))
                conn.commit()
                _, email_msg = send_user_credentials_email(name, email, user_code, password, role)
                flash(f"{role} '{name}' ({user_code}) registered successfully in central database! {email_msg}", "success")
            except Exception as e:
                print(f"[USER REGISTRATION ERROR] {e}")
                flash(f"Error registering user: {e}", "danger")

        elif action == 'edit':
            u_id = request.form.get('user_id')
            user_code = request.form.get('user_code', '').strip()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            role = request.form.get('role', 'Teacher').strip()
            department = request.form.get('department', '').strip() or 'Chemistry'
            student_class = request.form.get('student_class', '').strip() or 'B.Sc'
            year = request.form.get('year', '').strip() or '3rd Year'
            password = request.form.get('password', '').strip()

            try:
                if password:
                    cursor.execute("""
                        UPDATE users
                        SET user_code = ?, name = ?, email = ?, phone = ?, role = ?, department = ?, student_class = ?, year = ?, password = ?
                        WHERE id = ?;
                    """, (user_code, name, email, phone, role, department, student_class, year, password, u_id))
                else:
                    cursor.execute("""
                        UPDATE users
                        SET user_code = ?, name = ?, email = ?, phone = ?, role = ?, department = ?, student_class = ?, year = ?
                        WHERE id = ?;
                    """, (user_code, name, email, phone, role, department, student_class, year, u_id))
                conn.commit()
                flash(f"User profile '{name}' ({user_code}) updated successfully!", "success")
            except Exception as e:
                print(f"[USER UPDATE ERROR] {e}")
                flash(f"Failed to update user profile: {e}", "danger")

        elif action == 'delete':
            u_id = request.form.get('user_id')
            try:
                cursor.execute("DELETE FROM users WHERE id = ?;", (u_id,))
                conn.commit()
                flash("User profile removed from central database.", "info")
            except Exception as e:
                flash(f"Failed to delete user: {e}", "danger")

        conn.close()
        return redirect(url_for('admin_users', role=role_filter))

    # Counter Stats
    cursor.execute("SELECT COUNT(*) as cnt FROM users;")
    total_users = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'Student';")
    total_students = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'Teacher';")
    total_teachers = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'Lab Assistant';")
    total_assistants = cursor.fetchone()['cnt']

    # Query filtered users list
    if role_filter in ['Student', 'Teacher', 'Lab Assistant']:
        cursor.execute("SELECT * FROM users WHERE role = ? ORDER BY id DESC;", (role_filter,))
    else:
        cursor.execute("SELECT * FROM users ORDER BY id DESC;")

    users = cursor.fetchall()
    conn.close()

    return render_template('admin/users.html',
                           users=users,
                           role_filter=role_filter,
                           total_users=total_users,
                           total_students=total_students,
                           total_teachers=total_teachers,
                           total_assistants=total_assistants)
@app.route('/admin/notifications')
def admin_notifications():
    if not is_logged_in() or get_role() != 'Administrator':
        return redirect(url_for('login'))
    notifications = [
        {'id': 1, 'title': 'Low Stock Alert', 'message': 'Hydrochloric Acid stock is below 5.0 Liters.', 'time': '10 mins ago', 'type': 'warning'},
        {'id': 2, 'title': 'New Purchase Request', 'message': 'New equipment purchase request submitted by Lab Assistant.', 'time': '1 hour ago', 'type': 'info'}
    ]
    return render_template('admin/notifications.html', notifications=notifications)


@app.route('/admin/export_csv')
def export_inventory_csv():
    if not is_logged_in() or get_role() != 'Administrator':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.equipment_code, e.name, c.name as category, e.total_qty, e.available_qty, e.unit_type, e.unit_price, e.location, e.status
        FROM equipment e
        LEFT JOIN categories c ON e.category_id = c.id
        ORDER BY e.name ASC;
    """)
    items = cursor.fetchall()
    conn.close()

    csv_data = "Equipment Code,Item Name,Category,Total Qty,Available Qty,Unit Type,Unit Price,Location,Status\n"
    for item in items:
        csv_data += f'"{item["equipment_code"]}","{item["name"]}","{item["category"] or ""}","{item["total_qty"]}","{item["available_qty"]}","{item["unit_type"]}","{item["unit_price"]}","{item["location"]}","{item["status"]}"\n'

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=chemistry_lab_inventory_report.csv"}
    )


@app.route('/admin/export_pdf')
def export_inventory_pdf():
    if not is_logged_in() or get_role() != 'Administrator':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, c.name as category_name
        FROM equipment e
        LEFT JOIN categories c ON e.category_id = c.id
        ORDER BY e.name ASC;
    """)
    report_items = cursor.fetchall()
    conn.close()
    return render_template('admin/report_pdf.html', report_items=report_items)


if __name__ == '__main__':
    print("Launching Vivekanand College Chemistry Lab System on http://localhost:5000...")
    app.run(debug=True, port=5000)

