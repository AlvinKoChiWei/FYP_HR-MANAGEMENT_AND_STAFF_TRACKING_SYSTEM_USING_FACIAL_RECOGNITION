import glob
from tkinter import *
from tkinter import messagebox, ttk, Checkbutton, IntVar, END
import sqlite3
import bcrypt
import pytz
from datetime import datetime
import time
from tkcalendar import DateEntry
import cv2
import os
import numpy as np
from PIL import Image
import csv
from tkinter.filedialog import asksaveasfilename
import re
from fpdf import FPDF

WINDOW_WIDTH = 1350
WINDOW_HEIGHT = 760
WINDOW_TITLE = 'HR MANAGEMENT AND STAFF TRACKING SYSTEM USING FACIAL RECOGNITION'

LOGIN_ICON_PATH = 'images/admin_img.png'
LOCKED_ICON_PATH = 'images/locked.png'
UNLOCKED_ICON_PATH = 'images/unlocked.png'

FONT_BOLD_22 = ('Calibri', 22, 'bold')
FONT_BOLD_18 = ('Calibri', 18, 'bold')
FONT_18 = ('Calibri', 18)
FONT_BOLD_26 = ('Calibri', 26, 'bold')
FONT_BOLD_27 = ('Calibri', 27, 'bold')

BG_COLOR = '#273b7a'
FG_COLOR = 'white'


class InitiateDatabase:
    def __init__(self, db_file):
        self.db_file = db_file

    def create_tables(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance(
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            attendance_type TEXT NOT NULL,
            location TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees(
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            fin_nric_id TEXT NOT NULL,
            contact_number INTEGER NOT NULL,
            address CHAR(150) NOT NULL,
            email TEXT NOT NULL,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            joining_date TEXT NOT NULL,
            salary REAL NOT NULL,
            leave_entitlement REAL NOT NULL,
            sick_leave_entitlement REAL NOT NULL,
            gender TEXT NOT NULL,
            emergency_contact_name TEXT NOT NULL,
            emergency_contact_number INTEGER NOT NULL,
            relationship TEXT NOT NULL,
            marital_status TEXT NOT NULL,
            country TEXT NOT NULL,
            face_id TEXT NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT FALSE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_applications(
            leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            leave_type TEXT NOT NULL,
            apply_date TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            days REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            reason TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_balance(
            employee_id INTEGER NOT NULL,
            annual_leave_balance REAL NOT NULL,
            sick_leave_balance REAL NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payrolls(
            payroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            salary_month TEXT NOT NULL,
            salary_year TEXT NOT NULL,
            pay_date TEXT NOT NULL,
            working_days REAL NOT NULL,
            current_basic REAL NOT NULL,
            overtime_charge REAL,
            allowance REAL,
            incentives REAL,
            bonus REAL,
            advanced_pay REAL,
            advanced_deductions REAL,
            unpaid_leave_deductions REAL,
            late_deductions REAL,
            gross_pay REAL NOT NULL,
            total_deductions REAL,
            nett_pay REAL NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id) ON DELETE CASCADE,
            UNIQUE (employee_id, salary_month, salary_year)
        )
        """)

        conn.commit()
        conn.close()


class MainFrame:
    def __init__(self, root):
        self.root = root
        self.root.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')
        self.root.resizable(False, False)
        self.root.title(WINDOW_TITLE)
        self.bg_color = BG_COLOR
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.root.quit()


class LoginApp(MainFrame):
    def __init__(self, root):
        super().__init__(root)
        self.login_icon = PhotoImage(file=LOGIN_ICON_PATH)
        self.locked_icon = PhotoImage(file=LOCKED_ICON_PATH)
        self.unlocked_icon = PhotoImage(file=UNLOCKED_ICON_PATH)
        self.initialize_widgets()

    def forward_to_reset_password_page(self):
        self.login_page_fm.destroy()
        self.root.update()
        ResetPassword(self.root)

    def hash_password(self, password: str) -> bytes:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def verify_password(self, hashed_password: bytes, input_password: str) -> bool:
        return bcrypt.checkpw(input_password.encode('utf-8'), hashed_password)

    def login(self):
        employeeID = self.employeeID_entry.get()
        password = self.password_entry.get()

        if not employeeID or not password:
            messagebox.showerror('Error', 'All fields required!')
            return

        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name, password, '
                           'is_admin FROM employees WHERE employee_id = ?', (employeeID,))
            result = cursor.fetchone()

        if result:
            name, hashed_password, is_admin = result  # Correctly unpack the result
            if self.verify_password(hashed_password, password):
                messagebox.showinfo('Success', f'Welcome!\n\n{name}')  # Use the fetched name
                self.login_page_fm.destroy()
                self.root.update()
                Dashboard(self.root, employeeID, is_admin)
            else:
                messagebox.showerror('Error', 'Wrong Password!')
        else:
            messagebox.showerror('Error', 'Invalid ID!')

    def show_hide_password(self):
        if self.password_entry['show'] == '*':
            self.password_entry.config(show='')
            self.show_hide_btn.config(image=self.unlocked_icon)
        else:
            self.password_entry.config(show='*')
            self.show_hide_btn.config(image=self.locked_icon)

    def initialize_widgets(self):
        common_label_config = {'font': FONT_BOLD_18, 'fg': BG_COLOR}
        common_entry_config = {'font': FONT_18, 'justify': LEFT, 'highlightcolor': BG_COLOR,
                               'highlightbackground': 'gray', 'highlightthickness': 2}

        self.login_page_fm = Frame(self.root, highlightbackground=self.bg_color, highlightthickness=3)

        self.header_lb = Label(self.login_page_fm,
                               text='WELCOME TO HR MANAGEMENT AND '
                                    'STAFF TRACKING SYSTEM USING FACIAL RECOGNITION',
                               bg=BG_COLOR, fg=FG_COLOR, font=FONT_BOLD_22)
        self.header_lb.place(x=0, y=0, width=1340, height=50)

        self.login_icon_lb = Label(self.login_page_fm, image=self.login_icon)
        self.login_icon_lb.image = self.login_icon
        self.login_icon_lb.place(x=620, y=120)

        self.please_login_lb = Label(self.login_page_fm, text='Please Login.',
                                     **common_label_config)
        self.please_login_lb.place(x=590, y=220)

        self.employeeID_lb = Label(self.login_page_fm, text='Employee ID',
                                   **common_label_config)
        self.employeeID_lb.place(x=430, y=300)

        self.employeeID_entry = Entry(self.login_page_fm, **common_entry_config)
        self.employeeID_entry.place(x=600, y=300, width=265, height=40)

        self.password_lb = Label(self.login_page_fm, text='Password',
                                 **common_label_config)
        self.password_lb.place(x=430, y=360)

        self.password_entry = Entry(self.login_page_fm, show='*', **common_entry_config)
        self.password_entry.place(x=600, y=360, width=265, height=40)

        self.show_hide_btn = Button(self.login_page_fm, image=self.locked_icon,
                                    bd=0, command=self.show_hide_password)
        self.show_hide_btn.place(x=870, y=358)

        self.login_btn = Button(self.login_page_fm, text='Login', font=FONT_BOLD_18,
                                bg=BG_COLOR, fg=FG_COLOR, command=self.login)
        self.login_btn.place(x=470, y=430, width=370, height=50)

        self.reset_password_btn = Button(self.login_page_fm, text='Reset Password',
                                         font=FONT_BOLD_18,
                                         bg=BG_COLOR, fg=FG_COLOR,
                                         command=self.forward_to_reset_password_page)
        self.reset_password_btn.place(x=470, y=500, width=370, height=50)

        self.login_page_fm.pack(pady=40)
        self.login_page_fm.pack_propagate(False)
        self.login_page_fm.configure(width=1340, height=760)


class Dashboard(MainFrame):
    def __init__(self, root, employeeID, is_admin=False):
        super().__init__(root)
        self.employeeID = employeeID
        self.is_admin = is_admin
        self.create_dashboard_fm()
        self.widgets()

    def create_dashboard_fm(self):
        self.dashboard_fm = Frame(self.root, highlightbackground=BG_COLOR, highlightthickness=3)
        self.dashboard_fm.pack(pady=40)
        self.dashboard_fm.pack_propagate(False)
        self.dashboard_fm.configure(width=1340, height=760)

    def widgets(self):
        header_lb = Label(self.dashboard_fm,
                          text='DASHBOARD',
                          bg=BG_COLOR, fg=FG_COLOR, font=FONT_BOLD_22)
        header_lb.place(x=0, y=0, width=1340, height=50)

        app_name_lb = Label(self.dashboard_fm,
                            text='HR MANAGEMENT AND STAFF TRACKING SYSTEM USING FACIAL RECOGNITION',
                            fg=BG_COLOR, font=FONT_BOLD_27)
        app_name_lb.place(x=73, y=85)

        time_lb = Label(self.dashboard_fm, fg=BG_COLOR, font=FONT_BOLD_22)
        time_lb.place(x=430, y=170)
        self.update_time(time_lb)

        logged_as_user_lb = Label(self.dashboard_fm, fg=BG_COLOR, font=FONT_BOLD_26)
        logged_as_user_lb.pack(pady=250)
        self.get_logged_in_employee_name(logged_as_user_lb)

        attendance_btn = Button(self.dashboard_fm, text='Attendance\nManagement',
                                bg='green', fg=FG_COLOR,
                                font=FONT_BOLD_22, bd=0,
                                command=self.open_attendance_mgmt)

        employee_btn = Button(self.dashboard_fm, text='Employee\nManagement',
                              bg=BG_COLOR, fg=FG_COLOR,
                              font=FONT_BOLD_22, bd=0,
                              command=self.open_employee_mgmt)

        leave_btn = Button(self.dashboard_fm, text='Leave\nManagement',
                           bg=BG_COLOR, fg=FG_COLOR,
                           font=FONT_BOLD_22, bd=0, command=self.open_leave_mgmt)

        payroll_btn = Button(self.dashboard_fm, text='Payroll\nManagement',
                             bg=BG_COLOR, fg=FG_COLOR,
                             font=FONT_BOLD_22, bd=0,
                             command=self.open_payroll_mgmt)

        logout_btn = Button(self.dashboard_fm, text='Logout',
                            bg=BG_COLOR, fg=FG_COLOR,
                            font=FONT_BOLD_22, bd=0,
                            command=self.logout)

        exit_btn = Button(self.dashboard_fm, text='Exit',
                          bg='red', fg=FG_COLOR,
                          font=FONT_BOLD_22, bd=0,
                          command=exit)

        if self.is_admin:
            attendance_btn.place(x=50, y=400, width=180, height=160)
            employee_btn.place(x=265, y=400, width=180, height=160)
            leave_btn.place(x=475, y=400, width=180, height=160)
            payroll_btn.place(x=685, y=400, width=180, height=160)
            logout_btn.place(x=895, y=400, width=180, height=160)
            exit_btn.place(x=1105, y=400, width=180, height=160)
        else:
            attendance_btn.place(x=160, y=400, width=180, height=160)
            leave_btn.place(x=370, y=400, width=180, height=160)
            payroll_btn.place(x=580, y=400, width=180, height=160)
            logout_btn.place(x=790, y=400, width=180, height=160)
            exit_btn.place(x=1000, y=400, width=180, height=160)

    def get_logged_in_employee_name(self, frame):
        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM employees WHERE employee_id = ?', (self.employeeID,))
            result = cursor.fetchone()
            if result:
                employee_name = result[0]
                frame.config(text=f'Welcome\n{employee_name}')

    def update_time(self, frame):
        singapore = pytz.timezone('Asia/Singapore')
        current_time = datetime.now(singapore)
        formatted_time = current_time.strftime('%A, %d %B %Y, %H:%M:%S')

        frame.config(text=formatted_time)

        self.after_id = frame.after(1000, self.update_time, frame)

    def logout(self):
        response = messagebox.askyesno('Logout',
                                       'Are you sure want to logout account?')
        if response:
            self.dashboard_fm.destroy()
            self.dashboard_fm.after_cancel(self.after_id)
            self.root.update()
            LoginApp(self.root)
        else:
            pass

    def open_employee_mgmt(self):
        self.root.withdraw()
        new_root = Toplevel(self.root)
        EmployeeManagement(new_root, self.employeeID, self.is_admin)

    def open_attendance_mgmt(self):
        self.root.withdraw()
        new_root = Toplevel(self.root)
        AttendanceManagement(new_root, self.employeeID, self.is_admin)

    def open_leave_mgmt(self):
        self.root.withdraw()
        new_root = Toplevel(self.root)
        LeaveManagement(new_root, self.employeeID, self.is_admin)

    def open_payroll_mgmt(self):
        self.root.withdraw()
        new_root = Toplevel(self.root)
        PayrollManagement(new_root, self.employeeID, self.is_admin)


class PayrollManagement(MainFrame):
    def __init__(self, root, employeeID, is_admin=False):
        super().__init__(root)
        self.employeeID = employeeID
        self.is_admin = is_admin
        self.var_empID = StringVar()
        self.var_name = StringVar()
        self.var_department = StringVar()
        self.var_designation = StringVar()
        self.var_doj = StringVar()
        self.var_nationality = StringVar()
        self.var_email = StringVar()
        self.var_payroll_date = StringVar()
        self.var_salary = StringVar()
        self.var_working_days = StringVar()
        self.var_allowance = StringVar()
        self.var_bonus = StringVar()
        self.var_incentives = StringVar()
        self.var_advanced_pay = StringVar()
        self.var_overtime_hours = StringVar()
        self.var_overtime_rates = StringVar()
        self.var_advanced_pay_deductions = StringVar()
        self.var_unpaid_leave = StringVar()
        self.var_late_hours = StringVar()
        self.var_deductions = StringVar()
        self.var_gross_pay = StringVar()
        self.var_nett_pay = StringVar()
        self.var_salary_month = StringVar()
        self.var_salary_year = StringVar()
        self.var_overtime_charge = StringVar()
        self.var_unpaid_leave_deductions = StringVar()
        self.var_late_hours_charge = StringVar()
        self.var_empID.set(self.employeeID)
        self.initialize_widgets()
        self.search_employee()
        self.payroll_columns = [
            'payroll_id', 'employee_id', 'salary_month', 'salary_year', 'pay_date',
            'working_days', 'current_basic', 'overtime_charge', 'allowance',
            'incentives', 'bonus', 'advanced_pay', 'advanced_deductions',
            'unpaid_leave_deductions', 'late_deductions', 'gross_pay',
            'total_deductions', 'nett_pay'
        ]

    def initialize_widgets(self):
        self.payroll_mgmt_fm = Frame(self.root, highlightbackground=BG_COLOR,
                                     highlightthickness=3)
        self.payroll_mgmt_fm.pack(pady=40)
        self.payroll_mgmt_fm.pack_propagate(False)
        self.payroll_mgmt_fm.configure(width=1340, height=755)

        self.header_lb = Label(self.payroll_mgmt_fm,
                               text='PAYROLL MANAGEMENT',
                               bg=BG_COLOR, fg=FG_COLOR, font=FONT_BOLD_22)
        self.header_lb.place(x=0, y=0, width=1340, height=50)

        self.return_to_dashboard_btn = Button(self.payroll_mgmt_fm, text='⬅ Return to Dashboard',
                                              bg=BG_COLOR, fg=FG_COLOR,
                                              font=FONT_18,
                                              bd=0, command=self.return_to_dashboard)
        self.return_to_dashboard_btn.place(x=0, y=0)

        self.payroll_report_fm = Frame(self.payroll_mgmt_fm, highlightbackground='#008080',
                                       highlightthickness=1)
        self.employee_details_header_lb = Label(self.payroll_report_fm,
                                                text='EMPLOYEE DETAILS',
                                                bg='#008080', fg=FG_COLOR, font=FONT_BOLD_18)
        self.employee_details_header_lb.place(x=0, y=0, width=620, height=30)

        self.payroll_report_fm.place(x=20, y=105, width=620, height=560)

        self.table_lb_fm = Frame(self.payroll_report_fm, highlightbackground='#008080',
                                 highlightthickness=1)
        self.table_lb_fm.place(x=0, y=328, width=618, height=230)

        self.payroll_report_header_lb = Label(self.table_lb_fm,
                                              text='PAYROLL REPORT',
                                              bg='#008080', fg=FG_COLOR, font=FONT_BOLD_18)
        self.payroll_report_header_lb.place(x=0, y=0, width=620, height=30)

        self.table_fm = Frame(self.table_lb_fm, highlightbackground='#008080',
                              highlightthickness=1)

        self.table_fm.place(x=0, y=30, width=618, height=200)

        self.employee_id_lb = Label(self.payroll_report_fm, text='Employee ID',
                                    font=('Calibri', 15, 'bold'), fg='black')
        self.employee_id_lb.place(x=10, y=40)

        self.employee_id_entry = Entry(self.payroll_report_fm,
                                       font=('Calibri', 15),
                                       justify=LEFT, highlightcolor=BG_COLOR,
                                       highlightbackground='gray',
                                       highlightthickness=1, textvariable=self.var_empID)
        self.employee_id_entry.place(x=157, y=40, width=200, height=30)

        self.search_btn = Button(self.payroll_report_fm, text='Search', font=('Calibri', 15, 'bold'),
                                 width=14, bg=BG_COLOR, fg=FG_COLOR)

        self.name_lb = Label(self.payroll_report_fm, text='Name',
                             font=('Calibri', 15, 'bold'), fg='black')
        self.name_lb.place(x=10, y=80)

        self.show_name_lb = Label(self.payroll_report_fm, textvariable=self.var_name,
                                  font=('Calibri', 15, 'bold'), fg='black')
        self.show_name_lb.place(x=157, y=80)

        self.department_lb = Label(self.payroll_report_fm, text='Department',
                                   font=('Calibri', 15, 'bold'), fg='black')
        self.department_lb.place(x=10, y=120)

        self.show_department_lb = Label(self.payroll_report_fm, textvariable=self.var_department,
                                        font=('Calibri', 15, 'bold'), fg='black')
        self.show_department_lb.place(x=157, y=120)

        self.designation_lb = Label(self.payroll_report_fm, text='Designation',
                                    font=('Calibri', 15, 'bold'), fg='black')
        self.designation_lb.place(x=10, y=160)

        self.show_designation_lb = Label(self.payroll_report_fm, textvariable=self.var_designation,
                                         font=('Calibri', 15, 'bold'), fg='black')
        self.show_designation_lb.place(x=157, y=160)

        self.joining_date_lb = Label(self.payroll_report_fm, text='Date of Join',
                                     font=('Calibri', 15, 'bold'), fg='black')
        self.joining_date_lb.place(x=10, y=200)

        self.show_joining_date_lb = Label(self.payroll_report_fm, textvariable=self.var_doj,
                                          font=('Calibri', 15, 'bold'), fg='black')
        self.show_joining_date_lb.place(x=157, y=200)

        self.nationality_lb = Label(self.payroll_report_fm, text='Nationality',
                                    font=('Calibri', 15, 'bold'), fg='black')
        self.nationality_lb.place(x=10, y=240)

        self.show_nationality_lb = Label(self.payroll_report_fm, textvariable=self.var_nationality,
                                         font=('Calibri', 15, 'bold'), fg='black')
        self.show_nationality_lb.place(x=157, y=240)

        self.email_lb = Label(self.payroll_report_fm, text='Email',
                              font=('Calibri', 15, 'bold'), fg='black')
        self.email_lb.place(x=10, y=280)

        self.show_email_lb = Label(self.payroll_report_fm, textvariable=self.var_email,
                                   font=('Calibri', 15, 'bold'), fg='black')
        self.show_email_lb.place(x=157, y=280)

        scroll_x = ttk.Scrollbar(self.table_fm, orient=HORIZONTAL)
        scroll_y = ttk.Scrollbar(self.table_fm, orient=VERTICAL)
        self.payroll_table = ttk.Treeview(self.table_fm,
                                          column=('payroll_id', 'employee_id', 'name', 'salary_month', 'salary_year',
                                                  'pay_date', 'working_days', 'current_basic', 'overtime_charge',
                                                  'allowance', 'incentives', 'bonus', 'advanced_pay',
                                                  'advanced_deductions', 'unpaid_leave_deductions', 'late_deductions',
                                                  'gross_pay', 'total_deductions', 'nett_pay',),
                                          xscrollcommand=scroll_x.set,
                                          yscrollcommand=scroll_y.set)
        scroll_x.pack(side=BOTTOM, fill=X)
        scroll_y.pack(side=RIGHT, fill=Y)

        scroll_x.config(command=self.payroll_table.xview)
        scroll_y.config(command=self.payroll_table.yview)

        self.payroll_table.heading('payroll_id', text='Payroll ID')
        self.payroll_table.heading('employee_id', text='Employee ID')
        self.payroll_table.heading('name', text='Name')
        self.payroll_table.heading('salary_month', text='Salary Month')
        self.payroll_table.heading('salary_year', text='Salary Year')
        self.payroll_table.heading('pay_date', text='Payroll Date')
        self.payroll_table.heading('working_days', text='Working Days')
        self.payroll_table.heading('current_basic', text='Basic Pay')
        self.payroll_table.heading('overtime_charge', text='OT Charge')
        self.payroll_table.heading('allowance', text='Allowance')
        self.payroll_table.heading('incentives', text='Incentives')
        self.payroll_table.heading('bonus', text='Bonus')
        self.payroll_table.heading('advanced_pay', text='Advanced Pay')
        self.payroll_table.heading('advanced_deductions', text='Advanced Deductions')
        self.payroll_table.heading('unpaid_leave_deductions', text='Unpaid Leave Deductions')
        self.payroll_table.heading('late_deductions', text='Late Deductions')
        self.payroll_table.heading('gross_pay', text='Gross Pay')
        self.payroll_table.heading('total_deductions', text='Total Deductions')
        self.payroll_table.heading('nett_pay', text='Nett Pay')

        self.payroll_table['show'] = 'headings'

        self.payroll_table.column('payroll_id', width=50)
        self.payroll_table.column('employee_id', width=50)
        self.payroll_table.column('name', width=150)
        self.payroll_table.column('salary_month', width=50)
        self.payroll_table.column('salary_year', width=50)
        self.payroll_table.column('pay_date', width=80)
        self.payroll_table.column('working_days', width=80)
        self.payroll_table.column('current_basic', width=80)
        self.payroll_table.column('overtime_charge', width=80)
        self.payroll_table.column('allowance', width=80)
        self.payroll_table.column('incentives', width=80)
        self.payroll_table.column('bonus', width=80)
        self.payroll_table.column('advanced_pay', width=80)
        self.payroll_table.column('advanced_deductions', width=80)
        self.payroll_table.column('unpaid_leave_deductions', width=80)
        self.payroll_table.column('late_deductions', width=80)
        self.payroll_table.column('gross_pay', width=80)
        self.payroll_table.column('total_deductions', width=80)
        self.payroll_table.column('nett_pay', width=80)
        self.payroll_table.pack(fill=BOTH, expand=1)
        self.payroll_table.bind('<ButtonRelease>', self.get_cursor)
        self.load_payroll_report()

        self.employee_salary_fm = Frame(self.payroll_mgmt_fm, highlightbackground='#008080',
                                        highlightthickness=1)
        self.employee_salary_fm_header_lb = Label(self.employee_salary_fm,
                                                  text='EMPLOYEE SALARY DETAILS',
                                                  bg='#008080', fg=FG_COLOR, font=FONT_BOLD_18)

        self.payroll_date_lb = Label(self.employee_salary_fm, text='Payroll Date',
                                     font=('Calibri', 15, 'bold'), fg='black')
        self.payroll_date_lb.place(x=10, y=40)

        self.month_lb = Label(self.employee_salary_fm, text='Month',
                              font=('Calibri', 15, 'bold'), fg='black')
        self.month_lb.place(x=425, y=40)

        self.combo_month = ttk.Combobox(self.employee_salary_fm,
                                        font=('Calibri', 14),
                                        width=17, state='readonly',
                                        textvariable=self.var_salary_month)
        self.combo_month['value'] = ('Select Month', 'Jan', 'Feb', 'Mar', 'Apr', 'May',
                                     'Jun', 'Jul', 'Aug', 'Sept', 'Oct',
                                     'Nov', 'Dec')
        self.combo_month.current(0)
        self.combo_month.place(x=495, y=40, width=115, height=30)

        self.payroll_date_entry = DateEntry(self.employee_salary_fm, width=17,
                                            background='gray', foreground='black',
                                            borderwidth=1, date_pattern='dd-mm-yyyy',
                                            font=('Calibri', 16), textvariable=self.var_payroll_date)
        self.payroll_date_entry.place(x=130, y=40, width=125, height=30)

        self.year_lb = Label(self.employee_salary_fm, text='Year',
                             font=('Calibri', 15, 'bold'), fg='black')
        self.year_lb.place(x=265, y=40)

        self.combo_year = ttk.Combobox(self.employee_salary_fm,
                                       font=('Calibri', 14),
                                       width=17, state='readonly',
                                       textvariable=self.var_salary_year)
        self.combo_year['value'] = ('Select Year', '2023', '2024', '2025', '2026', '2027', '2028')
        self.combo_year.current(0)
        self.combo_year.place(x=310, y=40, width=110, height=30)

        self.earnings_lb = Label(self.employee_salary_fm, text='Earnings:',
                                 font=FONT_BOLD_22, fg='dark green')
        self.earnings_lb.place(x=10, y=80)

        self.salary_lb = Label(self.employee_salary_fm, text='Salary S$',
                               font=('Calibri', 15, 'bold'), fg='black')
        self.salary_lb.place(x=10, y=120)

        self.show_salary_lb = Label(self.employee_salary_fm, textvariable=self.var_salary,
                                    font=('Calibri', 15, 'bold'), fg='black')
        self.show_salary_lb.place(x=120, y=120)

        self.allowance_lb = Label(self.employee_salary_fm, text='Allowance',
                                  font=('Calibri', 15, 'bold'), fg='black')
        self.allowance_lb.place(x=10, y=160)

        self.allowance_entry = Entry(self.employee_salary_fm,
                                     font=('Calibri', 15),
                                     justify=LEFT, highlightcolor=BG_COLOR,
                                     highlightbackground='gray',
                                     highlightthickness=1, textvariable=self.var_allowance)
        self.allowance_entry.place(x=120, y=160, width=160, height=30)

        self.incentives_lb = Label(self.employee_salary_fm, text='Incentives',
                                   font=('Calibri', 15, 'bold'), fg='black')
        self.incentives_lb.place(x=10, y=200)

        self.incentives_entry = Entry(self.employee_salary_fm,
                                      font=('Calibri', 15),
                                      justify=LEFT, highlightcolor=BG_COLOR,
                                      highlightbackground='gray', highlightthickness=1,
                                      textvariable=self.var_incentives)
        self.incentives_entry.place(x=120, y=200, width=160, height=30)

        self.overtime_hour_lb = Label(self.employee_salary_fm, text='OT Hour(s)',
                                      font=('Calibri', 15, 'bold'), fg='black')
        self.overtime_hour_lb.place(x=10, y=240)

        self.overtime_hour_entry = Entry(self.employee_salary_fm,
                                         font=('Calibri', 15),
                                         justify=LEFT, highlightcolor=BG_COLOR,
                                         highlightbackground='gray', highlightthickness=1,
                                         textvariable=self.var_overtime_hours)
        self.overtime_hour_entry.place(x=120, y=240, width=160, height=30)

        self.overtime_earnings_lb = Label(self.employee_salary_fm, text='OT Earnings',
                                          font=('Calibri', 15, 'bold'), fg='black')
        self.overtime_earnings_lb.place(x=10, y=280)

        self.show_overtime_earnings_lb = Label(self.employee_salary_fm,
                                               textvariable=self.var_overtime_charge,
                                               font=('Calibri', 15, 'bold'), fg='black')
        self.show_overtime_earnings_lb.place(x=120, y=280)

        self.working_days_lb = Label(self.employee_salary_fm, text='Working Days',
                                     font=('Calibri', 15, 'bold'), fg='black')
        self.working_days_lb.place(x=310, y=120)

        self.working_days_entry = Entry(self.employee_salary_fm,
                                        font=('Calibri', 15),
                                        justify=LEFT, highlightcolor=BG_COLOR,
                                        highlightbackground='gray',
                                        highlightthickness=1, textvariable=self.var_working_days)
        self.working_days_entry.place(x=440, y=120, width=160, height=30)

        self.bonus_lb = Label(self.employee_salary_fm, text='Bonus',
                              font=('Calibri', 15, 'bold'), fg='black')
        self.bonus_lb.place(x=310, y=160)

        self.bonus_entry = Entry(self.employee_salary_fm,
                                 font=('Calibri', 15),
                                 justify=LEFT, highlightcolor=BG_COLOR,
                                 highlightbackground='gray', highlightthickness=1, textvariable=self.var_bonus)
        self.bonus_entry.place(x=440, y=160, width=160, height=30)

        self.advanced_pay_lb = Label(self.employee_salary_fm, text='Advanced Pay',
                                     font=('Calibri', 15, 'bold'), fg='black')
        self.advanced_pay_lb.place(x=310, y=200)

        self.advanced_pay_entry = Entry(self.employee_salary_fm,
                                        font=('Calibri', 15),
                                        justify=LEFT, highlightcolor=BG_COLOR,
                                        highlightbackground='gray', highlightthickness=1,
                                        textvariable=self.var_advanced_pay)
        self.advanced_pay_entry.place(x=440, y=200, width=160, height=30)

        self.overtime_rate_lb = Label(self.employee_salary_fm, text='OT Rates',
                                      font=('Calibri', 15, 'bold'), fg='black')
        self.overtime_rate_lb.place(x=310, y=240)

        self.show_overtime_rate_lb = Label(self.employee_salary_fm, textvariable=self.var_overtime_rates,
                                           font=('Calibri', 15, 'bold'), fg='black')
        self.show_overtime_rate_lb.place(x=440, y=240)

        self.deductions_lb = Label(self.employee_salary_fm, text='Deductions:',
                                   font=FONT_BOLD_22, fg='dark red')
        self.deductions_lb.place(x=10, y=320)

        self.advanced_pay_deductions_lb = Label(self.employee_salary_fm, text='Advanced Pay (-)',
                                                font=('Calibri', 15, 'bold'), fg='black')
        self.advanced_pay_deductions_lb.place(x=10, y=360)

        self.advanced_pay_deductions_entry = Entry(self.employee_salary_fm,
                                                   font=('Calibri', 15),
                                                   justify=LEFT, highlightcolor=BG_COLOR,
                                                   highlightbackground='gray', highlightthickness=1,
                                                   textvariable=self.var_advanced_pay_deductions)
        self.advanced_pay_deductions_entry.place(x=165, y=360, width=115, height=30)

        self.unpaid_leave_lb = Label(self.employee_salary_fm, text='Unpaid Leave',
                                     font=('Calibri', 15, 'bold'), fg='black')
        self.unpaid_leave_lb.place(x=10, y=400)

        self.unpaid_leave_entry = Entry(self.employee_salary_fm,
                                        font=('Calibri', 15),
                                        justify=LEFT, highlightcolor=BG_COLOR,
                                        highlightbackground='gray', highlightthickness=1,
                                        textvariable=self.var_unpaid_leave)
        self.unpaid_leave_entry.place(x=165, y=400, width=60, height=30)

        self.unpaid_leave_days_lb = Label(self.employee_salary_fm, text='day(s)',
                                          font=('Calibri', 15, 'bold'), fg='black')
        self.unpaid_leave_days_lb.place(x=233, y=400)

        self.late_hour_lb = Label(self.employee_salary_fm, text='Late Hour(s)',
                                  font=('Calibri', 15, 'bold'), fg='black')
        self.late_hour_lb.place(x=10, y=440)

        self.late_hour_entry = Entry(self.employee_salary_fm,
                                     font=('Calibri', 15),
                                     justify=LEFT, highlightcolor=BG_COLOR,
                                     highlightbackground='gray', highlightthickness=1,
                                     textvariable=self.var_late_hours)
        self.late_hour_entry.place(x=165, y=440, width=115, height=30)

        self.employee_salary_fm_header_lb.place(x=0, y=0, width=620, height=30)

        self.employee_salary_fm.place(x=693, y=105, width=620, height=560)

        self.summary_lb = Label(self.employee_salary_fm, text='Summary:',
                                font=FONT_BOLD_22, fg=BG_COLOR)
        self.summary_lb.place(x=310, y=320)

        self.gross_pay_lb = Label(self.employee_salary_fm, text='Gross Pay S$',
                                  font=('Calibri', 15, 'bold'), fg='black')
        self.gross_pay_lb.place(x=310, y=360)

        self.gross_pay_entry = Entry(self.employee_salary_fm,
                                     font=('Calibri', 15),
                                     justify=LEFT, highlightcolor=BG_COLOR,
                                     highlightbackground='gray',
                                     highlightthickness=1, textvariable=self.var_gross_pay)
        self.gross_pay_entry.place(x=440, y=360, width=160, height=30)

        self.total_deductions_lb = Label(self.employee_salary_fm, text='Total Deductions S$',
                                         font=('Calibri', 15, 'bold'), fg='black')
        self.total_deductions_lb.place(x=310, y=400)

        self.total_deductions_entry = Entry(self.employee_salary_fm,
                                            font=('Calibri', 15),
                                            justify=LEFT, highlightcolor=BG_COLOR,
                                            highlightbackground='gray', highlightthickness=1,
                                            textvariable=self.var_deductions)
        self.total_deductions_entry.place(x=490, y=400, width=110, height=30)

        self.nett_pay_lb = Label(self.employee_salary_fm, text='Nett Pay S$',
                                 font=('Calibri', 15, 'bold'), fg='black')
        self.nett_pay_lb.place(x=310, y=440)

        self.nett_pay_entry = Entry(self.employee_salary_fm,
                                    font=('Calibri', 15),
                                    justify=LEFT, highlightcolor=BG_COLOR,
                                    highlightbackground='gray',
                                    highlightthickness=1, textvariable=self.var_nett_pay)
        self.nett_pay_entry.place(x=440, y=440, width=160, height=30)

        save_pdf_btn = Button(self.employee_salary_fm, text='Save as PDF', font=FONT_BOLD_18,
                              bg=BG_COLOR, fg=FG_COLOR, command=self.generate_pdf)

        calculate_btn = Button(self.employee_salary_fm, text='Calculate', font=FONT_BOLD_18,
                               bg='dark green', fg=FG_COLOR, command=self.calculate_pay)

        save_btn = Button(self.employee_salary_fm, text='Save', font=FONT_BOLD_18,
                          bg=BG_COLOR, fg=FG_COLOR, command=self.save_payroll)

        clear_btn = Button(self.employee_salary_fm, text='Clear', font=FONT_BOLD_18,
                           bg=BG_COLOR, fg=FG_COLOR, command=self.clear_fields)

        if self.is_admin:
            save_pdf_btn.place(x=20, y=490, width=130, height=50)
            calculate_btn.place(x=205, y=490, width=120, height=50)
            save_btn.place(x=340, y=490, width=120, height=50)
            clear_btn.place(x=475, y=490, width=120, height=50)
            self.search_btn.place(x=375, y=40, width=90, height=30)
            self.search_btn.config(command=self.search_employee)

        else:
            save_pdf_btn.place(x=20, y=490, width=130, height=50)

        self.logged_as_user_lb = Label(self.payroll_mgmt_fm, fg=BG_COLOR, font=('Calibri', 18, 'bold'))
        self.logged_as_user_lb.place(x=8, y=50)
        self.get_logged_in_employee_name(self.logged_as_user_lb)

    def generate_pdf(self):
        selected_item = self.payroll_table.selection()

        if not selected_item:
            messagebox.showerror('Error', 'Please select a row in the table to generate a PDF.')
            return

        payroll_data = self.payroll_table.item(selected_item)['values']

        if not payroll_data:
            return

        payroll_id, employee_id, name, salary_month, salary_year, pay_date, working_days, current_basic, \
            overtime_charge, allowance, incentives, bonus, advanced_pay, advanced_deductions, unpaid_leave_deductions, \
            late_deductions, gross_pay, total_deductions, nett_pay = payroll_data

        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT fin_nric_id, department, designation, joining_date, country "
                           "FROM employees WHERE employee_id = ?", (int(employee_id),))
            employee_data = cursor.fetchone()
            fin_nric_id = employee_data[0]
            department = employee_data[1]
            designation = employee_data[2]
            joining_date = employee_data[3]
            country = employee_data[4]

        file_path = asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])

        if not file_path:
            return

        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            pdf.set_xy(0, 15)
            pdf.set_font("Arial", style="B", size=14)
            pdf.cell(0, 10, txt="      ABC Company Pte Ltd", align="C", ln=True)
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, txt="Block 123, Ubi Avenue,", align="C", ln=True)
            pdf.cell(0, 10, txt="100100 Singapore.", align="C", ln=True)
            pdf.ln(5)

            pdf.set_fill_color(0, 0, 128)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(190, 10, txt=f"PAY SLIP FOR "
                                  f"{salary_month.upper()} {salary_year}", ln=True, align='C', fill=True)
            pdf.ln(5)

            pdf.set_fill_color(192, 192, 192)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", style="B", size=14)
            pdf.cell(0, 10, txt=f"{name}", align="C", ln=True)

            pdf.set_fill_color(0, 0, 0)
            pdf.rect(10, pdf.get_y(), 190, 0.2, 'F')

            pdf.set_fill_color(192, 192, 192)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", size=12)

            pdf.rect(10, pdf.get_y(), 190, 0.2, 'F')
            pdf.ln(5)
            pdf.cell(95, 8, txt=f"Employee Number: {str(employee_id)}", ln=False)
            pdf.cell(95, 8, txt=f"FIN/NRIC No : {str(fin_nric_id)}", ln=True)
            pdf.cell(95, 8, txt=f"Department           : {str(department)}", ln=False)
            pdf.cell(95, 8, txt=f"Designation   : {str(designation)}", ln=True)
            pdf.cell(95, 8, txt=f"Date of joining       : {str(joining_date)}", ln=False)
            pdf.cell(95, 8, txt=f"Nationality     : {str(country)}", ln=True)
            pdf.cell(95, 8, txt=f"Payroll Date          : {str(pay_date)}", ln=False)
            pdf.cell(95, 8, txt=f"Days Worked: {str(working_days)}", ln=True)
            pdf.ln(10)
            pdf.set_fill_color(0, 0, 0)
            pdf.rect(10, pdf.get_y(), 190, 0.2, 'F')
            pdf.ln(10)
            table_data = [
                ("Earnings", "Amount"),
                ("Basic Salary", f"SGD {current_basic}"),
                ("Overtime Consultants", f"SGD {overtime_charge}" if overtime_charge != '0.0' else None),
                ("Fixed Allowance", f"SGD {allowance}" if allowance != '0.0' else None),
                ("Incentives", f"SGD {incentives}" if incentives != '0.0' else None),
                ("Bonus", f"SGD {bonus}" if bonus != '0.0' else None),
                ("Advanced Salary Payment", f"SGD {advanced_pay}" if advanced_pay != '0.0' else None),
                ("Total Earnings", f"SGD {gross_pay}"),
                ("Deductions", "Amount"),
                ("Advanced Salary Deductions", f"SGD {advanced_deductions}" if advanced_deductions != '0.0' else None),
                ("Unpaid Leave", f"SGD {unpaid_leave_deductions}" if unpaid_leave_deductions != '0.0' else None),
                ("Late Deductions", f"SGD {late_deductions}" if late_deductions != '0.0' else None),
                ("Total Deductions", f"SGD {total_deductions}"),
                ("Net Amount", f"SGD {nett_pay}")
            ]
            table_data = [row_data for row_data in table_data if row_data[1] is not None]
            for row_data in table_data:
                label, value = row_data
                if (label == "Earnings" or label == "Deductions" or
                        label == "Total Earnings" or label == "Net Amount" or label == "Total Deductions"):
                    pdf.set_fill_color(192, 192, 192)
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Arial", style="B", size=12)
                    pdf.cell(95, 10, txt=label, border=1, ln=False)
                    pdf.cell(95, 10, txt=value, border=1, ln=True)
                else:
                    pdf.set_fill_color(255, 255, 255)
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Arial", size=12)
                    pdf.cell(95, 10, txt=label, border=1, ln=False)
                    pdf.cell(95, 10, txt=value, border=1, ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", size=10)
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pdf.cell(0, 10, txt=f"Printed on: {current_date}", align="L")
            pdf.ln(5)
            pdf.set_fill_color(0, 0, 0)
            pdf.rect(10, pdf.get_y() + 5, 190, 0.2, 'F')
            pdf.ln(5)
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 10, txt="Computer Generated Payslip - No Signature Required", align="C")

            pdf.output(file_path)

            messagebox.showinfo('Success', f'PDF saved in {file_path}.')
        except PermissionError:
            messagebox.showerror('Error', 'The file is opened. Please close first before save.')

    def get_cursor(self, event=''):
        cursor_row = self.payroll_table.focus()
        content = self.payroll_table.item(cursor_row)
        data = content['values']
        if data:
            self.var_empID.set(data[1])
            self.var_name.set(data[2])
            self.var_salary_month.set(data[3])
            self.var_salary_year.set(data[4])
            self.var_payroll_date.set(data[5])
            self.var_working_days.set(data[6])
            self.var_salary.set(data[7])
            self.var_overtime_charge.set(f'S$ {data[8]}')
            self.var_allowance.set(data[9])
            self.var_incentives.set(data[10])
            self.var_bonus.set(data[11])
            self.var_advanced_pay.set(data[12])
            self.var_advanced_pay_deductions.set(data[13])
            self.var_unpaid_leave_deductions.set(data[14])
            self.var_late_hours_charge.set(data[15])
            self.var_gross_pay.set(data[16])
            self.var_deductions.set(data[17])
            self.var_nett_pay.set(data[18])

        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT department, designation, joining_date, country, email, salary "
                           "FROM employees WHERE employee_id = ?", (int(data[1]),))
            employee_data = cursor.fetchone()
        self.var_department.set(f'{employee_data[0]}')
        self.var_designation.set(f'{employee_data[1]}')
        self.var_doj.set(f'{employee_data[2]}')
        self.var_nationality.set(f'{employee_data[3]}')
        self.var_email.set(f'{employee_data[4]}')
        basic_salary = float(employee_data[5]) if employee_data[5] else 0
        if basic_salary <= 4500:
            hourly_basic_rate = (basic_salary * 12) / (52 * 44)
            ot_rate = hourly_basic_rate * 1.5
            formatted_rate = f"S$ {ot_rate:.2f}"
        else:
            formatted_rate = "Not entitled"
        self.show_overtime_rate_lb.config(text=formatted_rate)
        self.var_overtime_rates.set(formatted_rate)

    def calculate_pay(self):
        try:
            if not self.var_salary.get():
                messagebox.showerror("Error", "Please select one employee before do calculation.")
                return

            if not self.var_working_days.get():
                messagebox.showerror("Error", "Please input working days for salary calculation.")
                return

            monthly_basic_salary = float(self.var_salary.get() if self.var_salary.get() else 0)
            hourly_basic_rate = (monthly_basic_salary * 12) / (52 * 44)

            if monthly_basic_salary <= 4500:
                hourly_basic_rate = (monthly_basic_salary * 12) / (52 * 44)
                ot_rate = hourly_basic_rate * 1.5
                overtime_pay = ot_rate * float(self.var_overtime_hours.get() if self.var_overtime_hours.get() else 0)
            else:
                overtime_pay = 0

            advanced_pay = float(self.var_advanced_pay.get() if self.var_advanced_pay.get() else 0)
            allowance = float(self.var_allowance.get() if self.var_allowance.get() else 0)
            bonus = float(self.var_bonus.get() if self.var_bonus.get() else 0)
            advanced_pay_deduction = float(
                self.var_advanced_pay_deductions.get() if self.var_advanced_pay_deductions.get() else 0)
            incentives = float(self.var_incentives.get() if self.var_incentives.get() else 0)
            unpaid_leave = float(self.var_unpaid_leave.get() if self.var_unpaid_leave.get() else 0)
            late_hours = float(self.var_late_hours.get() if self.var_late_hours.get() else 0)

            daily_rate = float(monthly_basic_salary) / float(self.var_working_days.get())
            unpaid_leave_deduction = unpaid_leave * daily_rate
            late_hour_deduction = hourly_basic_rate * 0.5 * late_hours

            gross_pay = monthly_basic_salary + allowance + bonus + incentives + overtime_pay + advanced_pay
            total_deductions = advanced_pay_deduction + unpaid_leave_deduction + late_hour_deduction
            net_pay = gross_pay - total_deductions

            overtime_pay = round(overtime_pay, 2)
            gross_pay = round(gross_pay, 2)
            total_deductions = round(total_deductions, 2)
            net_pay = round(net_pay, 2)

            self.var_overtime_charge.set(f'S$ {str(overtime_pay)}')
            self.gross_pay_entry.delete(0, END)
            self.gross_pay_entry.insert(0, str(gross_pay))
            self.total_deductions_entry.delete(0, END)
            self.total_deductions_entry.insert(0, str(total_deductions))
            self.nett_pay_entry.delete(0, END)
            self.nett_pay_entry.insert(0, str(net_pay))
        except ValueError:
            messagebox.showerror('Error', 'Please ensure all filled fields have correct values')

    def save_payroll(self):
        employee_id = self.employee_id_entry.get()
        pay_date = self.var_payroll_date.get()
        working_days = self.var_working_days.get()
        basic = self.var_salary.get()
        salary_month = self.var_salary_month.get()
        salary_year = self.var_salary_year.get()

        if salary_month == 'Select Month' or salary_year == 'Select Year':
            messagebox.showerror('Error', 'Please select salary month and salary year before save!')
            return

        if employee_id == self.employeeID:
            messagebox.showerror('Error', 'You cannot save salary for yourself!')
            return

        bonus = self.var_bonus.get()
        if not bonus:
            bonus = 0

        allowance = self.var_allowance.get()
        if not allowance:
            allowance = 0

        incentives = self.var_incentives.get()
        if not incentives:
            incentives = 0

        overtime_hours = self.var_overtime_hours.get()
        if not overtime_hours:
            overtime_hours = 0

        advanced_pay = self.var_advanced_pay.get()
        if not advanced_pay:
            advanced_pay = 0

        advanced_pay_deductions = self.var_advanced_pay_deductions.get()
        if not advanced_pay_deductions:
            advanced_pay_deductions = 0

        unpaid_leave_deductions = self.var_unpaid_leave.get()
        if not unpaid_leave_deductions:
            unpaid_leave_deductions = 0

        late_deductions = self.var_late_hours.get()
        if not late_deductions:
            late_deductions = 0

        gross_pay = self.gross_pay_entry.get()
        total_deductions = self.total_deductions_entry.get()
        net_pay = self.nett_pay_entry.get()
        hourly_basic_rate = (float(basic) * 12) / (52 * 44)

        if not gross_pay or not total_deductions:
            messagebox.showerror('Error', 'Please calculate the payroll before saving.')
            return

        if float(basic) <= 4500.0:
            hourly_basic_rate = (float(basic) * 12) / (52 * 44)
            overtime_charge = round(hourly_basic_rate * 1.5 * float(overtime_hours), 2)
        else:
            overtime_charge = 0.0

        # Calculate unpaid leave deductions (rounded to 2 decimal places)
        daily_rate = float(basic) / float(working_days)
        unpaid_leave_deductions = round(daily_rate * float(unpaid_leave_deductions), 2)

        # Calculate late deductions (rounded to 2 decimal places)
        late_deductions = round(hourly_basic_rate * 0.5 * float(late_deductions), 2)

        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM payrolls "
                "WHERE employee_id = ? AND salary_month = ? AND salary_year = ?",
                (employee_id, salary_month, salary_year))
            count = cursor.fetchone()[0]

        if count > 0:
            messagebox.showerror('Error',
                                 'A payroll record for the selected month and year '
                                 'already exists for this employee.')
            return

        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO payrolls (employee_id, "
                    "salary_month,"
                    "salary_year,"
                    "pay_date, "
                    "working_days, "
                    "current_basic, "
                    "overtime_charge, "
                    "allowance, "
                    "incentives, "
                    "bonus, "
                    "advanced_pay, "
                    "advanced_deductions, "
                    "unpaid_leave_deductions, "
                    "late_deductions, "
                    "gross_pay, "
                    "total_deductions, "
                    "nett_pay) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (employee_id, salary_month, salary_year, pay_date, working_days,
                     basic, overtime_charge, allowance,
                     incentives, bonus, advanced_pay, advanced_pay_deductions, unpaid_leave_deductions,
                     late_deductions, gross_pay, total_deductions, net_pay))
                conn.commit()
                self.load_payroll_report()
                messagebox.showinfo('Success', 'Payroll saved successfully!')
            except sqlite3.IntegrityError:
                messagebox.showerror('Error',
                                     'A payroll record for the selected month '
                                     'and year already exists for this employee.')

    def clear_fields(self):
        fields = [self.employee_id_entry, self.allowance_entry, self.bonus_entry,
                  self.advanced_pay_deductions_entry,
                  self.unpaid_leave_entry, self.overtime_hour_entry,
                  self.gross_pay_entry, self.total_deductions_entry,
                  self.nett_pay_entry, self.working_days_entry,
                  self.late_hour_entry,
                  self.advanced_pay_entry, self.incentives_entry]
        for field in fields:
            field.delete(0, END)
        self.combo_month.current(0)
        self.combo_year.current(0)
        self.var_name.set('')
        self.var_department.set('')
        self.var_designation.set('')
        self.var_doj.set('')
        self.var_nationality.set('')
        self.var_email.set('')
        self.var_salary.set('')
        self.var_overtime_rates.set('')
        self.var_overtime_charge.set('')

    def load_payroll_report(self):
        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            if self.is_admin:
                cursor.execute("""
                SELECT p.payroll_id, p.employee_id, e.name, p.salary_month, p.salary_year,
                p.pay_date, p.working_days, p.current_basic, p.overtime_charge, p.allowance,
                p.incentives, p.bonus, p.advanced_pay, p.advanced_deductions, p.unpaid_leave_deductions,
                p.late_deductions, p.gross_pay, p.total_deductions, p.nett_pay
                FROM payrolls p
                JOIN employees e ON p.employee_id = e.employee_id
                """)
            else:
                cursor.execute("""
                            SELECT p.payroll_id, p.employee_id, e.name, p.salary_month, p.salary_year,
                            p.pay_date, p.working_days, p.current_basic, p.overtime_charge, p.allowance,
                            p.incentives, p.bonus, p.advanced_pay, p.advanced_deductions, p.unpaid_leave_deductions,
                            p.late_deductions, p.gross_pay, p.total_deductions, p.nett_pay
                            FROM payrolls p
                            JOIN employees e ON p.employee_id = e.employee_id
                            WHERE p.employee_id = ?""", (self.employeeID,))
            rows = cursor.fetchall()

            if len(rows) != 0:
                self.payroll_table.delete(*self.payroll_table.get_children())
                for row in rows:
                    self.payroll_table.insert('', 'end', values=row)

    def get_current_date(self):
        today = datetime.today()
        current_date = today.strftime('%d-%m-%Y')
        return current_date

    def search_employee(self):
        emp_id = self.employee_id_entry.get()
        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT name, department, '
                'designation, joining_date, '
                'country, email, salary FROM employees WHERE employee_id = ?',
                (emp_id,))
            result = cursor.fetchone()
        if result:
            self.var_name.set(result[0] if result[0] else "")
            self.var_department.set(result[1] if result[1] else "")
            self.var_designation.set(result[2] if result[2] else "")
            self.var_doj.set(result[3] if result[3] else "")
            self.var_nationality.set(result[4] if result[4] else "")
            self.var_email.set(result[5] if result[5] else "")
            self.var_salary.set(str(result[6]) if result[6] else "")
            basic_salary = float(result[6]) if result[6] else 0
            if basic_salary <= 4500:
                hourly_basic_rate = (basic_salary * 12) / (52 * 44)
                ot_rate = hourly_basic_rate * 1.5
                formatted_rate = f"S$ {ot_rate:.2f}"
            else:
                formatted_rate = "Not entitled"
            self.show_overtime_rate_lb.config(text=formatted_rate)
            self.var_overtime_rates.set(formatted_rate)
            self.var_overtime_charge.set('')
            self.combo_month.current(0)
            self.combo_year.current(0)
            fields = [self.allowance_entry, self.bonus_entry,
                      self.advanced_pay_deductions_entry,
                      self.unpaid_leave_entry, self.overtime_hour_entry,
                      self.gross_pay_entry, self.total_deductions_entry,
                      self.nett_pay_entry, self.working_days_entry,
                      self.late_hour_entry,
                      self.advanced_pay_entry, self.incentives_entry]
            for field in fields:
                field.delete(0, END)
        else:
            messagebox.showerror('Error', 'Employee not found')

    def get_logged_in_employee_name(self, frame):
        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM employees WHERE employee_id = ?', (self.employeeID,))
            result = cursor.fetchone()
            if result:
                employee_name = result[0]
                frame.config(text=f'Logged in User: {employee_name}')

    def return_to_dashboard(self):
        self.payroll_mgmt_fm.destroy()
        Dashboard(self.root, self.employeeID, self.is_admin)


class LeaveManagement(MainFrame):
    def __init__(self, root, employeeID, is_admin=False):
        super().__init__(root)
        self.employeeID = employeeID
        self.is_admin = is_admin
        self.var_leaveID = StringVar()
        self.var_empID = StringVar()
        self.var_name = StringVar()
        self.var_leave_type = StringVar()
        self.var_apply_date = StringVar()
        self.var_leave_balance = StringVar()
        self.var_start_date = StringVar()
        self.var_end_date = StringVar()
        self.var_status = StringVar()
        self.var_reason = StringVar()
        self.var_empID.set(self.employeeID)
        self.var_name.set(self.get_employee_name())
        self.var_apply_date.set(self.get_current_date())
        self.var_leave_balance.set(self.show_leave_balance())
        self.initialize_widgets()

    def initialize_widgets(self):
        self.leave_mgmt_fm = Frame(self.root, highlightbackground=BG_COLOR,
                                   highlightthickness=3)
        header_lb = Label(self.leave_mgmt_fm,
                          text='LEAVE MANAGEMENT',
                          bg=BG_COLOR, fg=FG_COLOR, font=FONT_BOLD_22)
        header_lb.place(x=0, y=0, width=1340, height=50)

        return_to_dashboard_btn = Button(self.leave_mgmt_fm, text='⬅ Return to Dashboard',
                                         bg=BG_COLOR, fg=FG_COLOR,
                                         font=FONT_BOLD_18,
                                         bd=0, command=self.return_to_dashboard)
        return_to_dashboard_btn.place(x=0, y=0)

        logged_as_user_lb = Label(self.leave_mgmt_fm, fg=BG_COLOR, font=FONT_BOLD_18)
        logged_as_user_lb.place(x=8, y=50)
        employee_name = self.get_employee_name()
        logged_as_user_lb.config(text=f'Logged in User: {employee_name}')

        self.leave_report_fm = Frame(self.leave_mgmt_fm, highlightbackground='#008080',
                                     highlightthickness=1)
        self.leave_report_header_lb = Label(self.leave_report_fm,
                                            text='LEAVE REPORT',
                                            bg='#008080', fg=FG_COLOR, font=FONT_BOLD_18)

        self.table_fm = Frame(self.leave_report_fm, highlightbackground='#008080',
                              highlightthickness=1)

        self.table_fm.place(x=0, y=30, width=618, height=453)

        self.search_fm = Frame(self.leave_report_fm, highlightbackground='#008080',
                               highlightthickness=1)
        self.search_fm.place(x=0, y=483, width=618, height=45)

        search_by = Label(self.search_fm, text='Search By:',
                          font=('Calibri', 13, 'bold'), bg='red', fg=FG_COLOR,
                          width=8)
        search_by.grid(row=0, column=0, sticky=W, padx=2)

        com_text_search = ttk.Combobox(self.search_fm, state='readonly',
                                       font=('Calibri', 11, 'bold'),
                                       width=14, height=40)
        com_text_search['value'] = ('Search Option', 'employee_id', 'status')
        com_text_search.current(0)
        com_text_search.grid(row=0, column=1, sticky=W, padx=5)

        txt_search_entry = ttk.Entry(self.search_fm, width=20,
                                     font=('Calibri', 11, 'bold'),
                                     justify=LEFT)
        txt_search_entry.grid(row=0, column=2, padx=5)

        search_btn = Button(self.search_fm, text='Search', font=('Calibri', 11, 'bold'),
                            width=8, bg=BG_COLOR, fg=FG_COLOR,
                            command=lambda: self.search_data(com_text_search.get(), txt_search_entry.get()))
        search_btn.grid(row=0, column=3, padx=5)

        show_all_btn = Button(self.search_fm, text='Show All', font=('Calibri', 11, 'bold'),
                              width=8, bg=BG_COLOR, fg=FG_COLOR,
                              command=self.load_leave_report)
        show_all_btn.grid(row=0, column=4, padx=5)

        self.leave_report_header_lb.place(x=0, y=0, width=620, height=30)

        self.leave_report_fm.place(x=20, y=105, width=620, height=530)

        scroll_x = ttk.Scrollbar(self.table_fm, orient=HORIZONTAL)
        scroll_y = ttk.Scrollbar(self.table_fm, orient=VERTICAL)
        self.leave_table = ttk.Treeview(self.table_fm,
                                        column=('leave_id', 'employee_id', 'name',
                                                'leave_type', 'apply_date', 'start_date',
                                                'end_date', 'reason', 'status'),
                                        xscrollcommand=scroll_x.set,
                                        yscrollcommand=scroll_y.set)
        scroll_x.pack(side=BOTTOM, fill=X)
        scroll_y.pack(side=RIGHT, fill=Y)

        scroll_x.config(command=self.leave_table.xview)
        scroll_y.config(command=self.leave_table.yview)

        self.leave_table.heading('leave_id', text='Leave ID')
        self.leave_table.heading('employee_id', text='Employee ID')
        self.leave_table.heading('name', text='Name')
        self.leave_table.heading('leave_type', text='Leave Type')
        self.leave_table.heading('apply_date', text='Apply Date')
        self.leave_table.heading('start_date', text='Start Date')
        self.leave_table.heading('end_date', text='End Date')
        self.leave_table.heading('reason', text='Reason')
        self.leave_table.heading('status', text='Status')

        self.leave_table['show'] = 'headings'

        self.leave_table.column('leave_id', width=50)
        self.leave_table.column('employee_id', width=50)
        self.leave_table.column('name', width=100)
        self.leave_table.column('leave_type', width=50)
        self.leave_table.column('apply_date', width=50)
        self.leave_table.column('start_date', width=50)
        self.leave_table.column('end_date', width=50)
        self.leave_table.column('reason', width=50)
        self.leave_table.column('status', width=50)

        self.leave_table.pack(fill=BOTH, expand=1)
        self.leave_table.bind('<ButtonRelease>', self.get_cursor)
        self.load_leave_report()

        self.leave_mgmt_fm.pack(pady=40)
        self.leave_mgmt_fm.pack_propagate(False)
        self.leave_mgmt_fm.configure(width=1340, height=755)

        self.leave_application_fm = Frame(self.leave_mgmt_fm, highlightbackground='#008080',
                                          highlightthickness=1)
        self.leave_application_header_lb = Label(self.leave_application_fm,
                                                 text='LEAVE APPLICATION',
                                                 bg='#008080', fg=FG_COLOR, font=FONT_BOLD_18)

        self.employee_id_lb = Label(self.leave_application_fm, text=('Employee ID'),
                                    font=('Calibri', 16, 'bold'), fg='black', justify=CENTER
                                    )
        self.employee_id_lb.place(x=50, y=60)

        self.employee_id_show_lb = Label(self.leave_application_fm, text=f'{self.employeeID}',
                                         font=('Calibri', 16, 'bold'), textvariable=self.var_empID,
                                         fg='black')
        self.employee_id_show_lb.place(x=230, y=60)

        self.employee_name_lb = Label(self.leave_application_fm, text='Name',
                                      font=('Calibri', 16, 'bold'), fg='black', justify=CENTER
                                      )
        self.employee_name_lb.place(x=50, y=100)

        self.employee_name_show_lb = Label(self.leave_application_fm,
                                           text=self.get_employee_name(), font=('Calibri', 16, 'bold'),
                                           fg='black', textvariable=self.var_name)
        self.employee_name_show_lb.place(x=230, y=100)

        self.current_date_lb = Label(self.leave_application_fm, text='Date',
                                     font=('Calibri', 16, 'bold'), fg='black', justify=CENTER
                                     )
        self.current_date_lb.place(x=50, y=140)
        self.current_date_show_lb = Label(self.leave_application_fm,
                                          text=self.get_current_date(), font=('Calibri', 16, 'bold'),
                                          fg='black', textvariable=self.var_apply_date)
        self.current_date_show_lb.place(x=230, y=140)

        self.leave_balance_lb = Label(self.leave_application_fm, text='Leave Balance',
                                      font=('Calibri', 16, 'bold'), fg='black', justify=CENTER
                                      )
        self.leave_balance_lb.place(x=50, y=180)

        self.show_leave_balance_lb = Label(self.leave_application_fm,
                                           font=('Calibri', 16, 'bold'), fg='black', justify=CENTER)
        self.show_leave_balance_lb.place(x=230, y=180)
        self.show_leave_balance_lb.config(text=self.show_leave_balance())

        self.leave_type_lb = Label(self.leave_application_fm, text='Types of Leave',
                                   font=('Calibri', 16, 'bold'), fg='black', justify=CENTER)
        self.leave_type_lb.place(x=50, y=220)

        self.combo_leave_type = ttk.Combobox(self.leave_application_fm,
                                             font=('Calibri', 16),
                                             width=17, state='readonly',
                                             textvariable=self.var_leave_type)
        self.combo_leave_type['value'] = ('Select Leave Type', 'Annual Leave', 'Sick Leave')
        self.combo_leave_type.current(0)
        self.combo_leave_type.place(x=230, y=220, width=310, height=30)

        self.start_date_lb = Label(self.leave_application_fm, text='Start Date',
                                   font=('Calibri', 16, 'bold'), fg='black', justify=CENTER
                                   )
        self.start_date_lb.place(x=50, y=260)

        self.start_date_entry = DateEntry(self.leave_application_fm, width=17,
                                          background='gray', foreground='black',
                                          borderwidth=1, date_pattern='dd-mm-yyyy',
                                          font=('Calibri', 16), textvariable=self.var_start_date)
        self.start_date_entry.place(x=230, y=260, width=310, height=30)

        self.end_date_lb = Label(self.leave_application_fm, text='End Date',
                                 font=('Calibri', 16, 'bold'), fg='black', justify=CENTER
                                 )
        self.end_date_lb.place(x=50, y=300)

        self.end_date_entry = DateEntry(self.leave_application_fm, width=17,
                                        background='gray', foreground='black',
                                        borderwidth=1, date_pattern='dd-mm-yyyy',
                                        font=('Calibri', 16), textvariable=self.var_end_date)
        self.end_date_entry.place(x=230, y=300, width=310, height=30)

        self.reason_lb = Label(self.leave_application_fm, text='Reason (If Any)',
                               font=('Calibri', 16, 'bold'), fg='black', justify=CENTER
                               )
        self.reason_lb.place(x=50, y=340)

        self.reason_entry = Entry(self.leave_application_fm,
                                  font=('Calibri', 15),
                                  justify=LEFT, highlightcolor=BG_COLOR,
                                  highlightbackground='gray', highlightthickness=1,
                                  textvariable=self.var_reason)
        self.reason_entry.place(x=230, y=340, width=310, height=30)

        self.status_lb = Label(self.leave_application_fm, text='Status',
                               font=('Calibri', 16, 'bold'), fg='black', justify=CENTER
                               )
        self.status_lb.place(x=50, y=380)

        self.show_status_lb = Label(self.leave_application_fm,
                                    font=('Calibri', 16, 'bold'), fg='black', justify=CENTER
                                    , textvariable=self.var_status, text='')
        self.show_status_lb.place(x=230, y=380)

        apply_btn = Button(self.leave_application_fm, text='Apply',
                           bg=BG_COLOR, fg=FG_COLOR,
                           font=('Calibri', 18, 'bold'), bd=0,
                           command=self.apply_leave)

        self.manager_action_lb = Label(self.leave_application_fm,
                                       font=('Calibri', 16, 'bold'), fg='black', justify=CENTER,
                                       text='Manager Action:')

        approve_btn = Button(self.leave_application_fm, text='Approve',
                             bg='dark green', fg=FG_COLOR,
                             font=('Calibri', 18, 'bold'), bd=0,
                             command=self.approve_leave)

        reject_btn = Button(self.leave_application_fm, text='Reject',
                            bg='dark red', fg=FG_COLOR,
                            font=('Calibri', 18, 'bold'), bd=0,
                            command=self.reject_leave)

        cancel_btn = Button(self.leave_application_fm, text='Cancel',
                            bg=BG_COLOR, fg=FG_COLOR,
                            font=('Calibri', 18, 'bold'), bd=0,
                            command=self.cancel_leave)

        clear_btn = Button(self.leave_application_fm, text='Clear',
                           bg=BG_COLOR, fg=FG_COLOR,
                           font=('Calibri', 18, 'bold'), bd=0,
                           command=self.clear_fields)

        export_btn = Button(self.search_fm, text='Export', font=('Calibri', 11, 'bold'),
                            width=8, bg='dark green', fg=FG_COLOR,
                            command=self.export_leave_data_to_csv)

        if self.is_admin:
            apply_btn.place(x=20, y=470, width=100, height=50)
            cancel_btn.place(x=130, y=470, width=100, height=50)
            clear_btn.place(x=240, y=470, width=100, height=50)
            self.manager_action_lb.place(x=395, y=435)
            approve_btn.place(x=395, y=470, width=100, height=50)
            reject_btn.place(x=505, y=470, width=100, height=50)
            export_btn.grid(row=0, column=5, padx=3)
        else:
            apply_btn.place(x=110, y=470, width=100, height=50)
            cancel_btn.place(x=260, y=470, width=100, height=50)
            clear_btn.place(x=410, y=470, width=100, height=50)

        self.leave_application_header_lb.place(x=0, y=0, width=620, height=30)

        self.leave_application_fm.place(x=693, y=105, width=620, height=530)

    def get_current_date(self):
        today = datetime.today()
        current_date = today.strftime('%d-%m-%Y')
        return current_date

    def get_cursor(self, event=''):
        cursor_row = self.leave_table.focus()
        content = self.leave_table.item(cursor_row)
        data = content['values']

        if data:
            self.var_leaveID.set(data[0])
            self.var_empID.set(data[1])
            self.var_name.set(data[2])
            self.var_leave_type.set(data[3])
            self.var_apply_date.set(data[4])
            self.var_start_date.set(data[5])
            self.var_end_date.set(data[6])
            self.var_reason.set(data[7])
            self.var_status.set(data[8])
        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            results = cursor.execute(
                'SELECT annual_leave_balance, sick_leave_balance FROM leave_balance WHERE employee_id = ?',
                (self.var_empID.get(),)).fetchone()
            if results:
                annual_leave, sick_leave = results
                formatted_result = f'AL: {annual_leave} days\tSL: {sick_leave} days'
            self.show_leave_balance_lb.config(text=formatted_result)

    def load_leave_report(self):
        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            if self.is_admin:
                cursor.execute("""
                SELECT la.leave_id, la.employee_id, e.name, la.leave_type, la.apply_date,
                la.start_date, la.end_date, la.reason, la.status
                FROM leave_applications la
                JOIN employees e ON la.employee_id = e.employee_id
                """)
            else:
                cursor.execute("""
                SELECT la.leave_id, la.employee_id, e.name, la.leave_type, la.apply_date,
                la.start_date, la.end_date, la.reason, la.status
                FROM leave_applications la
                INNER JOIN employees e ON la.employee_id = e.employee_id
                WHERE la.employee_id = ?""", (self.employeeID,))
            rows = cursor.fetchall()

            if len(rows) != 0:
                self.leave_table.delete(*self.leave_table.get_children())
                for row in rows:
                    self.leave_table.insert('', 'end', values=row)

    def get_employee_name(self):
        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM '
                           'employees WHERE employee_id = ?', (self.employeeID,))
            result = cursor.fetchone()
            if result:
                employee_name = result[0]
        return employee_name

    def show_leave_balance(self):
        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            results = cursor.execute(
                'SELECT annual_leave_balance, sick_leave_balance FROM leave_balance WHERE employee_id = ?',
                (self.employeeID,)).fetchone()
            if results:
                annual_leave, sick_leave = results
                formatted_result = f'AL: {annual_leave} days\tSL: {sick_leave} days'
        return formatted_result

    def cancel_leave(self):
        selected_item = self.leave_table.selection()
        if not selected_item:
            messagebox.showerror('Error', 'No Leave Application Selected')
            return

        leave_id = self.var_leaveID.get()
        status = self.var_status.get()
        if status == 'Approved':
            messagebox.showerror('Error',
                                 'You cannot cancel the approved leave!\nPlease check with HR!')
            return
        elif status == 'Rejected':
            messagebox.showerror('Error',
                                 'Leave is already been rejected!')
            return
        elif status == 'pending':
            response = messagebox.askyesno('Cancel Leave', 'Are you sure want to cancel leave?')
            if response:
                with sqlite3.connect('employees.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM leave_applications WHERE leave_id = ?', (leave_id,))
                    conn.commit()
                    self.load_leave_report()
                    self.clear_fields()
                    messagebox.showinfo('Cancel Success',
                                        'Leave has been cancelled successfully!')

    def search_data(self, search_by, keyword):
        if search_by == 'search options':
            messagebox.showerror('Error', 'Please select a valid search option.')
            return
        elif not keyword:
            messagebox.showerror('Error', 'Please type some keywords to search.')
            return

        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            if search_by == "employee_id":
                cursor.execute(
                    f"SELECT leave_applications.leave_id, "
                    f"employees.employee_id, employees.name, "
                    f"leave_applications.leave_type, leave_applications.apply_date, "
                    f"leave_applications.start_date, leave_applications.end_date, "
                    f"leave_applications.reason, leave_applications.status "
                    f"FROM `leave_applications`"
                    f" INNER JOIN employees ON "
                    f"leave_applications.employee_id = employees.employee_id "
                    f"WHERE leave_applications.employee_id = ?",
                    (keyword,))
            else:
                cursor.execute(
                    f"SELECT leave_applications.leave_id, "
                    f"employees.employee_id, employees.name, "
                    f"leave_applications.leave_type, leave_applications.apply_date, "
                    f"leave_applications.start_date, leave_applications.end_date, "
                    f"leave_applications.reason, leave_applications.status "
                    f"FROM `leave_applications`"
                    f" INNER JOIN employees ON "
                    f"leave_applications.employee_id = employees.employee_id "
                    f"WHERE leave_applications.status = ?",
                    (keyword,))

            rows = cursor.fetchall()
            if len(rows) != 0:
                self.leave_table.delete(*self.leave_table.get_children())
                for row in rows:
                    self.leave_table.insert('', END, values=row)
            else:
                messagebox.showinfo('No Records Found', 'No matching records found.')

    def approve_leave(self):
        selected_item = self.leave_table.selection()
        if not selected_item:
            messagebox.showerror('Error', 'No Leave Application Selected')
            return

        leave_id = self.var_leaveID.get()
        employee_id = self.var_empID.get()
        leave_type = self.var_leave_type.get()
        status = self.var_status.get()

        if employee_id == self.employeeID:
            messagebox.showerror('Error', 'Cannot approve leave for yourself!')
            return

        if status == 'Rejected':
            messagebox.showerror('Error', 'Cannot approve rejected leaves!')
            return

        if status == 'Approved':
            messagebox.showerror('Error', 'Leave has been approved!')
            return

        if status == 'pending':
            confirmation = messagebox.askyesno('Confirmation',
                                               'Are you sure you want to approve this leave?')
            if not confirmation:
                return

            with sqlite3.connect('employees.db') as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE leave_applications '
                               'SET status = ? WHERE leave_id = ?',
                               ('Approved', leave_id))
                conn.commit()

                cursor.execute('SELECT days FROM leave_applications '
                               'WHERE leave_id = ?', (leave_id,))
                days = cursor.fetchone()[0]

                if leave_type == 'Annual Leave':
                    cursor.execute(
                        'UPDATE leave_balance '
                        'SET annual_leave_balance = annual_leave_balance - ? '
                        'WHERE employee_id = ?',
                        (days, employee_id))
                elif leave_type == 'Sick Leave':
                    cursor.execute(
                        'UPDATE leave_balance '
                        'SET sick_leave_balance = sick_leave_balance - ? '
                        'WHERE employee_id = ?',
                        (days, employee_id))

                conn.commit()

                self.load_leave_report()
                self.clear_fields()
                messagebox.showinfo('Success', 'Leave Approved Successfully')

    def reject_leave(self):
        selected_item = self.leave_table.selection()
        if not selected_item:
            messagebox.showerror('Error', 'No Leave Application Selected')
            return

        leave_id = self.var_leaveID.get()
        employee_id = self.var_empID.get()
        status = self.var_status.get()

        if employee_id == self.employeeID:
            messagebox.showerror('Error', 'Cannot reject leave for yourself')
            return

        if status == 'Approved':
            messagebox.showerror('Error',
                                 'Cannot reject approved leaves!')
            return

        if status == 'pending':
            confirmation = messagebox.askyesno('Confirmation',
                                               'Are you sure you want to reject this leave?')
            if not confirmation:
                return

            with sqlite3.connect('employees.db') as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE leave_applications '
                               'SET status = ? WHERE leave_id = ?',
                               ('Rejected', leave_id))
                conn.commit()

                self.load_leave_report()
                self.clear_fields()
                messagebox.showinfo('Success', 'Leave Rejected Successfully')

    def apply_leave(self):
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        leave_type = self.combo_leave_type.get()
        reason = self.reason_entry.get()

        start_date = datetime.strptime(start_date, '%d-%m-%Y').date()
        end_date = datetime.strptime(end_date, '%d-%m-%Y').date()
        days_used = (end_date - start_date).days + 1

        start_date_formatted = start_date.strftime('%d-%m-%Y')
        end_date_formatted = end_date.strftime('%d-%m-%Y')

        if start_date > end_date:
            messagebox.showerror('Error',
                                 'Start date is greater than end date!')
            return

        if leave_type == 'Select Leave Type':
            messagebox.showerror('Error',
                                 'Please select leave type!')
            return

        today = datetime.now().date()
        if start_date < today:
            messagebox.showerror('Error',
                                 'Cannot apply for past days!')
            return

        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()

            cursor.execute(
                'SELECT * FROM leave_applications '
                'WHERE employee_id = ? AND (start_date = ? OR end_date = ?)',
                (self.employeeID, start_date_formatted, end_date_formatted))
            existing_leave_data = cursor.fetchone()

            if existing_leave_data:
                if existing_leave_data[7] == 'Rejected':
                    existing_leave_id = existing_leave_data[0]
                    cursor.execute(
                        'DELETE FROM leave_applications WHERE leave_id = ?',
                        (existing_leave_id,))
                else:
                    messagebox.showerror('Error',
                                         'You have already applied for leave on this date!')
                    return

            cursor.execute('SELECT annual_leave_balance, sick_leave_balance FROM '
                           'leave_balance WHERE employee_id = ?', (self.employeeID,))
            results = cursor.fetchone()

            if not results:
                messagebox.showerror('Error', 'Unable to fetch leave balance!')
                return

            annual_leave_balance, sick_leave_balance = results

            cursor.execute(
                'SELECT SUM(days) FROM leave_applications '
                'WHERE employee_id = ? AND leave_type = ? AND status = ?',
                (self.employeeID, leave_type, 'pending')
            )
            pending_leave_days = cursor.fetchone()[0]
            if not pending_leave_days:
                pending_leave_days = 0

            total_applied_days = pending_leave_days + days_used

            if leave_type == 'Annual Leave' and total_applied_days > annual_leave_balance:
                messagebox.showerror('Error', 'Not enough Annual Leave balance! '
                                              'Check with HR for unpaid leave.')
                return
            elif leave_type == 'Sick Leave' and total_applied_days > sick_leave_balance:
                messagebox.showerror('Error', 'Not enough Sick Leave balance! '
                                              'Check with HR for unpaid leave.')
                return

            conn.execute('INSERT INTO leave_applications'
                         '(employee_id, leave_type, apply_date, '
                         'start_date, end_date, days, reason) '
                         'VALUES (?, ?, ?, ?, ?, ?, ?)', (
                             self.employeeID,
                             leave_type,
                             self.get_current_date(),
                             start_date_formatted,
                             end_date_formatted,
                             days_used,
                             reason))
            conn.commit()
            self.load_leave_report()
            self.clear_fields()

        if leave_type == 'Annual Leave':
            messagebox.showinfo('Annual Leave',
                                'Annual leave applied successfully!'
                                '\n\nStatus: Pending Approval')
        elif leave_type == 'Sick Leave':
            messagebox.showinfo('Sick Leave',
                                'Sick leave applied successfully!'
                                '\n\nStatus: Pending Approval')

    def export_leave_data_to_csv(self):
        try:
            file_location = asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile="leave_data.csv",
                title="Choose filename and location"
            )

            if not file_location:
                return

            with sqlite3.connect('employees.db') as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT leave_applications.leave_id, employees.employee_id, employees.name,
                    leave_applications.leave_type, leave_applications.apply_date,
                    leave_applications.start_date, leave_applications.end_date,
                    leave_applications.days, leave_applications.reason, leave_applications.status
                    FROM leave_applications
                    INNER JOIN employees ON leave_applications.employee_id = employees.employee_id
                """)
                rows = cursor.fetchall()

                with open(file_location, "w", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Leave ID', 'Employee ID', 'Name', 'Leave Type', 'Apply Date',
                                     'Start Date', 'End Date', 'Days', 'Reason', 'Status'])
                    writer.writerows(rows)

            messagebox.showinfo('Data Exported',
                                f'All leave data successfully exported to {file_location}.')
        except Exception as e:
            messagebox.showerror('Error',
                                 f'Error exporting leave data to CSV: {str(e)}')

    def clear_fields(self):
        self.var_leaveID.set("")
        self.var_empID.set(self.employeeID)
        self.var_name.set(self.get_employee_name())
        self.var_leave_type.set("Select Leave Type")
        self.var_start_date.set('')
        self.var_end_date.set('')
        self.var_reason.set("")
        self.combo_leave_type.current(0)
        self.start_date_entry.delete(0, END)
        self.end_date_entry.delete(0, END)
        self.var_apply_date.set(self.get_current_date())
        self.var_status.set('')
        self.show_leave_balance_lb.config(text=self.show_leave_balance())

    def return_to_dashboard(self):
        self.leave_mgmt_fm.destroy()
        Dashboard(self.root, self.employeeID, self.is_admin)


class AttendanceManagement(MainFrame):
    def __init__(self, root, employeeID, is_admin=False):
        super().__init__(root)
        self.employeeID = employeeID
        self.is_admin = is_admin
        self.initialize_widgets()

    def initialize_widgets(self):
        self.attendance_mgmt_fm = Frame(self.root, highlightbackground=BG_COLOR,
                                        highlightthickness=3)
        self.attendance_mgmt_fm.pack(pady=40)
        self.attendance_mgmt_fm.pack_propagate(False)
        self.attendance_mgmt_fm.configure(width=1340, height=755)

        self.header_lb = Label(self.attendance_mgmt_fm,
                               text='ATTENDANCE MANAGEMENT',
                               bg=BG_COLOR, fg=FG_COLOR, font=FONT_BOLD_22)
        self.header_lb.place(x=0, y=0, width=1340, height=50)

        return_to_dashboard_btn = Button(self.attendance_mgmt_fm, text='⬅ Return to Dashboard',
                                         bg=BG_COLOR, fg=FG_COLOR,
                                         font=FONT_BOLD_18,
                                         bd=0, command=self.return_to_dashboard)
        return_to_dashboard_btn.place(x=0, y=0)

        self.logged_as_user_lb = Label(self.attendance_mgmt_fm, fg=BG_COLOR, font=FONT_BOLD_18)
        self.logged_as_user_lb.place(x=8, y=50)
        self.get_logged_in_employee_name(self.logged_as_user_lb)

        self.attendance_report_fm = Frame(self.attendance_mgmt_fm, highlightbackground='#008080',
                                          highlightthickness=1)
        self.attendance_report_header_lb = Label(self.attendance_report_fm,
                                                 text='ATTENDANCE REPORT',
                                                 bg='#008080', fg=FG_COLOR, font=FONT_BOLD_18)

        self.table_fm = Frame(self.attendance_report_fm, highlightbackground='#008080',
                              highlightthickness=1)

        self.table_fm.place(x=0, y=30, width=618, height=480)

        scroll_x = ttk.Scrollbar(self.table_fm, orient=HORIZONTAL)
        scroll_y = ttk.Scrollbar(self.table_fm, orient=VERTICAL)
        self.attendance_table = ttk.Treeview(self.table_fm,
                                             column=('attendance_id', 'employee_id', 'name',
                                                     'attendance_type', 'location', 'date', 'time',),
                                             xscrollcommand=scroll_x.set,
                                             yscrollcommand=scroll_y.set)
        scroll_x.pack(side=BOTTOM, fill=X)
        scroll_y.pack(side=RIGHT, fill=Y)

        scroll_x.config(command=self.attendance_table.xview)
        scroll_y.config(command=self.attendance_table.yview)

        self.attendance_table.heading('attendance_id', text='Attendance ID')
        self.attendance_table.heading('employee_id', text='Employee ID')
        self.attendance_table.heading('name', text='Name')
        self.attendance_table.heading('attendance_type', text='Attendance Type')
        self.attendance_table.heading('location', text='Location')
        self.attendance_table.heading('date', text='Date')
        self.attendance_table.heading('time', text='Time')

        self.attendance_table['show'] = 'headings'

        self.attendance_table.column('attendance_id', width=50)
        self.attendance_table.column('employee_id', width=50)
        self.attendance_table.column('name', width=100)
        self.attendance_table.column('attendance_type', width=50)
        self.attendance_table.column('location', width=50)
        self.attendance_table.column('date', width=50)
        self.attendance_table.column('time', width=50)

        self.attendance_table.pack(fill=BOTH, expand=1)
        self.fetch_data()

        self.search_fm = Frame(self.attendance_report_fm, highlightbackground='#008080',
                               highlightthickness=1)
        self.search_fm.place(x=0, y=510, width=618, height=48)

        self.search_by = Label(self.search_fm, text='Search By:',
                               font=('Calibri', 13, 'bold'), bg='red', fg=FG_COLOR,
                               width=8)
        self.search_by.grid(row=0, column=0, sticky=W, padx=2)

        self.com_text_search = ttk.Combobox(self.search_fm, state='readonly',
                                            font=('Calibri', 11, 'bold'),
                                            width=14, height=40)
        self.com_text_search['value'] = ('Search Option', 'employee_id', 'attendance_type')
        self.com_text_search.current(0)
        self.com_text_search.grid(row=0, column=1, sticky=W, padx=5)

        self.txt_search_entry = ttk.Entry(self.search_fm, width=20,
                                          font=('Calibri', 11, 'bold'),
                                          justify=LEFT)
        self.txt_search_entry.grid(row=0, column=2, padx=5)

        search_btn = Button(self.search_fm, text='Search', font=('Calibri', 11, 'bold'),
                            width=8, bg=BG_COLOR, fg=FG_COLOR,
                            command=lambda: self.search_data(self.com_text_search.get(),
                                                             self.txt_search_entry.get()))
        search_btn.grid(row=0, column=3, padx=5)

        show_all_btn = Button(self.search_fm, text='Show All', font=('Calibri', 11, 'bold'),
                              width=8, bg=BG_COLOR, fg=FG_COLOR,
                              command=self.fetch_data)
        show_all_btn.grid(row=0, column=4, padx=5)

        if self.is_admin:
            export_btn = Button(self.search_fm, text='Export', font=('Calibri', 11, 'bold'),
                                width=8, bg='dark green', fg=FG_COLOR,
                                command=self.export_data_to_csv)
            export_btn.grid(row=0, column=5, padx=3)

        self.attendance_report_header_lb.place(x=0, y=0, width=620, height=30)

        self.attendance_report_fm.place(x=20, y=105, width=620, height=560)

        self.attendance_portal_fm = Frame(self.attendance_mgmt_fm, highlightbackground='#008080',
                                          highlightthickness=1)
        self.attendance_portal_header_lb = Label(self.attendance_portal_fm,
                                                 text='ATTENDANCE PORTAL',
                                                 bg='#008080', fg=FG_COLOR, font=FONT_BOLD_18)

        self.mark_attendance_fm = Frame(self.attendance_portal_fm, highlightbackground='#008080',
                                        highlightthickness=0)
        self.mark_attendance_header_lb = Label(self.mark_attendance_fm,
                                               text='MARK ATTENDANCE',
                                               bg='green', fg=FG_COLOR, font=FONT_BOLD_18)

        clock_in_btn = Button(self.mark_attendance_fm, text='Clock In',
                              bg=BG_COLOR, fg=FG_COLOR,
                              font=('Calibri', 30, 'bold'), bd=0,
                              command=lambda:
                              self.capture_attendance(self.employeeID,
                                                      self.combo_location.get(),
                                                      'Clock in'))
        clock_in_btn.place(x=60, y=90, width=200, height=140)

        clock_out_btn = Button(self.mark_attendance_fm, text='Clock Out',
                               bg=BG_COLOR, fg=FG_COLOR,
                               font=('Calibri', 30, 'bold'), bd=0,
                               command=lambda:
                               self.capture_attendance(self.employeeID,
                                                       self.combo_location.get(),
                                                       'Clock Out'))
        clock_out_btn.place(x=360, y=90, width=200, height=140)

        self.mark_attendance_header_lb.place(x=0, y=0, width=618, height=30)

        self.mark_attendance_fm.place(x=0, y=280, width=618, height=268)

        self.time_lb = Label(self.attendance_portal_fm, fg='black', font=('Calibri', 16, 'bold'))
        self.time_lb.place(x=215, y=50)
        self.update_time(self.time_lb)

        self.location_lb = Label(self.attendance_portal_fm, text='Select Working Location',
                                 font=('Calibri', 16, 'bold'), fg='black', justify=CENTER
                                 )
        self.location_lb.place(x=200, y=160)

        self.combo_location = ttk.Combobox(self.attendance_portal_fm,
                                           font=('Calibri', 14),
                                           width=17, state='readonly', justify=CENTER
                                           )
        self.combo_location['value'] = ('Select Working Location', 'SGH', 'NHCS', 'NDCS', 'NCCS',
                                        'Connection One', 'EGH', 'Tampines Plaza', 'SKCH', 'SCH',
                                        'OCH', 'KKH', 'SKH', 'Bedok Polyclinic', 'Sengkang Polyclinic',
                                        'Tampines Polyclinic', 'Punggol Polyclinic', 'Outram Polyclinic',
                                        'Bukit Merah Polyclinic', 'Marine Parade Polyclinic', 'Eunos Polyclinic',
                                        'Pasir Ris Polyclinic')
        self.combo_location.current(0)
        self.combo_location.place(x=180, y=200, width=265, height=30)

        self.attendance_portal_header_lb.place(x=0, y=0, width=620, height=30)

        self.attendance_portal_fm.place(x=693, y=105, width=620, height=560)

    def capture_attendance(self, employee_id, location, attendance_type):
        if location == 'Select Working Location':
            messagebox.showerror('Location Not Selected',
                                 'Please select a working location first.')
            return

        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT face_id
                FROM employees
                WHERE employee_id = ?""",
                           (self.employeeID,))
            enrolment_status = cursor.fetchone()
            if enrolment_status and enrolment_status[0] == 'Not Enrolled':
                messagebox.showerror('Error', 'Data Missing! Please register Face ID!')
                return

        def draw_boundary(img, classifier, scaleFactor, minNeighbours, color, text, clf):
            attendance_marked = False
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray_img = cv2.equalizeHist(gray_img)
            features = classifier.detectMultiScale(gray_img, scaleFactor, minNeighbours)

            coordinate = []

            for (x, y, w, h) in features:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 3)
                id, predict = clf.predict(gray_img[y:y + h, x:x + w])
                confidence = int((100 * (1 - predict / 300)))
                conn = sqlite3.connect('employees.db')
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM employees '
                               'WHERE employee_id = ?', (id,))
                result = cursor.fetchone()
                if not result:
                    continue
                result = "+".join(result)

                if confidence > 77:
                    employee_name = result
                    cv2.putText(img, f'{result}', (x, y + h),
                                cv2.FONT_HERSHEY_COMPLEX, 0.8, (255, 255, 255),
                                3)
                    cv2.imshow("Taking Attendance", img)
                    cv2.waitKey(1000)
                    if str(id) == employee_id:
                        try:
                            cursor.execute("""
                                    INSERT INTO attendance (employee_id,
                                    attendance_type, location, date, time)
                                    VALUES (?, ?, ?, ?, ?)""",
                                           (employee_id, attendance_type,
                                            location, date, time_stamp))
                            conn.commit()
                            messagebox.showinfo('Attendance',
                                                f'Attendance for {employee_name} marked successfully!')
                            attendance_marked = True
                            self.fetch_data()
                            break
                        except Exception as e:
                            print("Error while marking attendance:", e)
                    else:
                        messagebox.showerror('Wrong Employee',
                                             'The recognized face '
                                             'does not match the current logged-in employee.')
                        return None, False
                else:
                    # count = datetime.now()
                    cv2.imshow("Taking Attendance", img)
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 3)
                    cv2.putText(img, 'Unknown', (x, y + h), cv2.FONT_HERSHEY_COMPLEX,
                                0.8, (255, 255, 255), 3)
                    cv2.imshow("Taking Attendance", img)
                coordinate = [x, y, w, h]
                conn.close()
            return coordinate, attendance_marked

        def recognize(img, clf, face_cascade):
            coordinate, marked = draw_boundary(img, face_cascade, 1.2, 5,
                                               (255, 255, 255), 'Face', clf)
            if marked or coordinate is None:
                return None
            return img

        face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
        clf = cv2.face.LBPHFaceRecognizer_create()

        exists = os.path.isfile("Classifier/Classifier.yml")

        if exists:
            clf.read("Classifier/Classifier.yml")
        else:
            messagebox.showerror('Data Missing',
                                 'Please register face ID!')
            return

        ts = time.time()
        date = datetime.fromtimestamp(ts).strftime('%d-%m-%Y')
        time_stamp = datetime.fromtimestamp(ts).strftime('%H:%M:%S')

        cam = cv2.VideoCapture(0)

        while True:
            ret, img = cam.read()
            img = recognize(img, clf, face_cascade)
            if img is None:  # Added this condition
                break
            cv2.imshow("Taking Attendance", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cam.release()
        cv2.destroyAllWindows()

    def get_logged_in_employee_name(self, frame):
        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM employees WHERE employee_id = ?', (self.employeeID,))
            result = cursor.fetchone()
            if result:
                employee_name = result[0]

    def fetch_data(self):
        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            if self.is_admin:
                cursor.execute("""
                    SELECT attendance.attendance_id, attendance.employee_id, 
                    employees.name, attendance.attendance_type, attendance.location, 
                    attendance.date, attendance.time
                    FROM attendance
                    INNER JOIN employees ON attendance.employee_id = employees.employee_id""")
            else:
                cursor.execute("""
                    SELECT attendance.attendance_id, attendance.employee_id, 
                    employees.name, attendance.attendance_type, attendance.location, 
                    attendance.date, attendance.time
                    FROM attendance
                    INNER JOIN employees ON attendance.employee_id = employees.employee_id
                    WHERE attendance.employee_id = ?""", (self.employeeID,))

            rows = cursor.fetchall()
            if len(rows) != 0:
                self.attendance_table.delete(*self.attendance_table.get_children())
                for row in rows:
                    self.attendance_table.insert('', END, values=row)

    def search_data(self, search_by, keyword):
        if search_by == 'search options':
            messagebox.showerror('Error', 'Please select a valid search option.')
            return
        elif not keyword:
            messagebox.showerror('Error', 'Please type some keywords to search.')
            return

        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            if search_by == "employee_id":
                cursor.execute(
                    f"SELECT attendance.attendance_id, "
                    f"attendance.employee_id, employees.name, "
                    f"attendance.attendance_type, attendance.location, "
                    f"attendance.date, attendance.time FROM attendance "
                    f"INNER JOIN employees ON attendance.employee_id = employees.employee_id "
                    f"WHERE attendance.employee_id LIKE '%{keyword}%'")
            else:
                cursor.execute(
                    f"SELECT attendance.attendance_id, "
                    f"attendance.employee_id, employees.name, "
                    f"attendance.attendance_type, attendance.location, "
                    f"attendance.date, attendance.time FROM attendance "
                    f"INNER JOIN employees ON attendance.employee_id = "
                    f"employees.employee_id WHERE attendance.attendance_type LIKE '%{keyword}%'")

            rows = cursor.fetchall()
            if len(rows) != 0:
                self.attendance_table.delete(*self.attendance_table.get_children())
                for row in rows:
                    self.attendance_table.insert('', END, values=row)
            else:
                messagebox.showinfo('No Records Found', 'No matching records found.')

    def export_data_to_csv(self):
        file_location = asksaveasfilename(defaultextension=".csv",
                                          filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                                          initialfile="attendance_data.csv",
                                          title="Choose filename and location")
        if not file_location:
            return

        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT attendance.attendance_id, attendance.employee_id, 
                employees.name, attendance.attendance_type, attendance.location, 
                attendance.date, attendance.time
                FROM attendance
                INNER JOIN employees ON attendance.employee_id = employees.employee_id""")
            rows = cursor.fetchall()

            with open(file_location, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Attendance ID',
                                 'Employee ID', 'Name', 'Attendance Type', 'Location', 'Date', 'Time'])
                for row in rows:
                    writer.writerow(row)

        messagebox.showinfo('Data Exported',
                            f'Attendance data successfully exported to {file_location}.')

    def update_time(self, frame):
        singapore = pytz.timezone('Asia/Singapore')
        current_time = datetime.now(singapore)
        formatted_time = current_time.strftime('%A\n%d %B %Y\n%H:%M:%S')

        frame.config(text=formatted_time)
        self.after_id = frame.after(1000, self.update_time, frame)

    def return_to_dashboard(self):
        self.attendance_mgmt_fm.destroy()
        Dashboard(self.root, self.employeeID, self.is_admin)


class EmployeeManagement(MainFrame):
    def __init__(self, root, employeeID, is_admin=False):
        super().__init__(root)
        self.employeeID = employeeID
        self.is_admin = is_admin
        self.var_empID = StringVar()
        self.var_name = StringVar()
        self.var_nric = StringVar()
        self.var_contact = StringVar()
        self.var_email = StringVar()
        self.var_dept = StringVar()
        self.var_designation = StringVar()
        self.var_address = StringVar()
        self.var_join_date = StringVar()
        self.var_salary = StringVar()
        self.var_annual_leave = StringVar()
        self.var_sick_leave = StringVar()
        self.var_gender = StringVar()
        self.var_emergency_name = StringVar()
        self.var_emergency_contact = StringVar()
        self.var_relationship = StringVar()
        self.var_marital_status = StringVar()
        self.var_country = StringVar()
        self.var_com_text_search = StringVar()
        self.var_text_search = StringVar()
        self.var_is_admin = IntVar()

        self.employee_mgmt_fm = Frame(self.root, highlightbackground=BG_COLOR,
                                      highlightthickness=3)

        header_lb = Label(self.employee_mgmt_fm,
                          text='EMPLOYEE MANAGEMENT',
                          bg=BG_COLOR, fg=FG_COLOR, font=FONT_BOLD_22)
        header_lb.place(x=0, y=0, width=1340, height=50)

        return_to_dashboard_btn = Button(self.employee_mgmt_fm, text='⬅ Return to Dashboard',
                                         bg=BG_COLOR, fg=FG_COLOR,
                                         font=FONT_BOLD_18,
                                         bd=0, command=self.return_to_dashboard)
        return_to_dashboard_btn.place(x=0, y=0)

        self.employee_info_fm = LabelFrame(self.employee_mgmt_fm, bd=3, relief=RIDGE,
                                           text='Employee Information',
                                           font=('Calibri', 11, 'bold'),
                                           fg='black')
        self.employee_info_fm.place(x=3, y=53, width=1103, height=450)

        self.face_id_fm = LabelFrame(self.employee_mgmt_fm, bd=3, relief=RIDGE,
                                     text='Face ID Enrolment',
                                     font=('Calibri', 11, 'bold'),
                                     fg='black')
        self.face_id_fm.place(x=1108, y=53, width=222, height=450)

        self.table_fm = LabelFrame(self.employee_mgmt_fm, bd=3, relief=RIDGE,
                                   text='Employee Information Table',
                                   font=('Calibri', 11, 'bold'),
                                   fg='black')
        self.table_fm.place(x=3, y=503, width=1327, height=167)

        message_lb = Label(self.employee_info_fm, text='*Please fill in all details',
                           font=('Calibri', 8, 'bold', 'italic'), fg='dark red')
        message_lb.place(x=5, y=3)

        employee_id_lb = Label(self.employee_info_fm, text='Employee ID',
                               font=('Calibri', 15, 'bold'), fg='black')
        employee_id_lb.place(x=5, y=20)

        employee_id_entry = Entry(self.employee_info_fm, textvariable=self.var_empID,
                                  font=('Calibri', 15),
                                  justify=LEFT, highlightcolor=BG_COLOR,
                                  highlightbackground='gray', highlightthickness=1)
        employee_id_entry.place(x=152, y=20, width=265, height=30)

        name_lb = Label(self.employee_info_fm, text='Name',
                        font=('Calibri', 15, 'bold'), fg='black')
        name_lb.place(x=5, y=60)

        name_entry = Entry(self.employee_info_fm, textvariable=self.var_name,
                           font=('Calibri', 15),
                           justify=LEFT, highlightcolor=BG_COLOR,
                           highlightbackground='gray', highlightthickness=1)
        name_entry.place(x=152, y=60, width=265, height=30)

        fin_nric_lb = Label(self.employee_info_fm, text='IC/Passport No',
                            font=('Calibri', 15, 'bold'), fg='black')
        fin_nric_lb.place(x=5, y=100)

        fin_nric_entry = Entry(self.employee_info_fm, textvariable=self.var_nric,
                               font=('Calibri', 15),
                               justify=LEFT, highlightcolor=BG_COLOR,
                               highlightbackground='gray', highlightthickness=1)
        fin_nric_entry.place(x=152, y=100, width=265, height=30)

        contact_lb = Label(self.employee_info_fm, text='Contact No',
                           font=('Calibri', 15, 'bold'), fg='black')
        contact_lb.place(x=5, y=140)

        self.contact_entry = Entry(self.employee_info_fm, textvariable=self.var_contact,
                                   font=('Calibri', 15),
                                   justify=LEFT, highlightcolor=BG_COLOR,
                                   highlightbackground='gray', highlightthickness=1)
        self.contact_entry.place(x=152, y=140, width=265, height=30)

        email_lb = Label(self.employee_info_fm, text='Email Address',
                         font=('Calibri', 15, 'bold'), fg='black')
        email_lb.place(x=5, y=180)

        email_entry = Entry(self.employee_info_fm, textvariable=self.var_email,
                            font=('Calibri', 15),
                            justify=LEFT, highlightcolor=BG_COLOR,
                            highlightbackground='gray', highlightthickness=1)
        email_entry.place(x=152, y=180, width=265, height=30)

        department_lb = Label(self.employee_info_fm, text='Department',
                              font=('Calibri', 15, 'bold'), fg='black')
        department_lb.place(x=5, y=220)

        combo_department = ttk.Combobox(self.employee_info_fm, textvariable=self.var_dept,
                                        font=('Calibri', 15),
                                        width=17, state='readonly'
                                        )
        combo_department['value'] = ('Select Department', 'IBM_ITMO', 'IBM_IDADMIN', 'Finance',
                                     'Executive Office', 'Marketing', 'Human Resource',
                                     'IBM_CALLCTR', 'IBM_NETWORK')
        combo_department.current(0)
        combo_department.place(x=152, y=220, width=265, height=30)

        designation_lb = Label(self.employee_info_fm, text='Designation',
                               font=('Calibri', 15, 'bold'), fg='black')
        designation_lb.place(x=5, y=260)

        combo_designation = ttk.Combobox(self.employee_info_fm, textvariable=self.var_designation,
                                         font=('Calibri', 15),
                                         width=17, state='readonly'
                                         )
        combo_designation['value'] = ('Select Designation', 'Deskside Support Engineer',
                                      'Premium Support Engineer', 'Deskside Team Lead',
                                      'Deskside Assistant Team Lead', 'Assistant Site Manager',
                                      'Site Manager', 'ID Admin Lead', 'ID Admin Assistant',
                                      'Assistant Director', 'Director', 'Manager', 'Executive', 'Accountant',
                                      'Auditor', 'Clerk', 'Assistant Manager', 'Junior Executive')
        combo_designation.current(0)
        combo_designation.place(x=152, y=260, width=265, height=30)

        address_lb = Label(self.employee_info_fm, text='Address',
                           font=('Calibri', 15, 'bold'), fg='black')
        address_lb.place(x=5, y=380)

        address_entry = Entry(self.employee_info_fm, textvariable=self.var_address, font=('Calibri', 15),
                              highlightcolor=BG_COLOR,
                              highlightbackground='gray', highlightthickness=1)
        address_entry.place(x=152, y=380, width=765)

        joining_date_lb = Label(self.employee_info_fm, text='Joining Date',
                                font=('Calibri', 15, 'bold'), fg='black')
        joining_date_lb.place(x=440, y=20)

        joining_date_entry = DateEntry(self.employee_info_fm, textvariable=self.var_join_date, width=17,
                                       background='gray', foreground='black',
                                       borderwidth=1, date_pattern='dd-mm-yyyy',
                                       font=('Calibri', 15))
        joining_date_entry.place(x=650, y=20, width=265, height=30)

        salary_lb = Label(self.employee_info_fm, text='Salary (S$)',
                          font=('Calibri', 15, 'bold'), fg='black')
        salary_lb.place(x=440, y=60)

        salary_entry = Entry(self.employee_info_fm, textvariable=self.var_salary,
                             font=('Calibri', 15),
                             justify=LEFT, highlightcolor=BG_COLOR,
                             highlightbackground='gray', highlightthickness=1)
        salary_entry.place(x=650, y=60, width=265, height=30)

        leave_entitlement_lb = Label(self.employee_info_fm, text='Annual Leave',
                                     font=('Calibri', 15, 'bold'), fg='black')
        leave_entitlement_lb.place(x=440, y=100)

        leave_entry = Entry(self.employee_info_fm, textvariable=self.var_annual_leave,
                            font=('Calibri', 15),
                            justify=LEFT, highlightcolor=BG_COLOR,
                            highlightbackground='gray', highlightthickness=1)
        leave_entry.place(x=650, y=100, width=265, height=30)

        sick_leave_entitlement_lb = Label(self.employee_info_fm, text='Sick Leave',
                                          font=('Calibri', 15, 'bold'), fg='black')
        sick_leave_entitlement_lb.place(x=440, y=140)

        sick_leave_entry = Entry(self.employee_info_fm, textvariable=self.var_sick_leave,
                                 font=('Calibri', 15),
                                 justify=LEFT, highlightcolor=BG_COLOR,
                                 highlightbackground='gray', highlightthickness=1)
        sick_leave_entry.place(x=650, y=140, width=265, height=30)

        gender_lb = Label(self.employee_info_fm, text='Gender',
                          font=('Calibri', 15, 'bold'), fg='black')
        gender_lb.place(x=440, y=180)

        combo_gender = ttk.Combobox(self.employee_info_fm, textvariable=self.var_gender,
                                    font=('Calibri', 14),
                                    width=17, state='readonly'
                                    )
        combo_gender['value'] = ('Select Gender', 'Male', 'Female', 'Other')
        combo_gender.current(0)
        combo_gender.place(x=650, y=180, width=265, height=30)

        emergency_contact_name_lb = Label(self.employee_info_fm, text='Emergency Name',
                                          font=('Calibri', 15, 'bold'), fg='black')
        emergency_contact_name_lb.place(x=440, y=260)

        emergency_contact_name_entry = Entry(self.employee_info_fm, textvariable=self.var_emergency_name,
                                             font=('Calibri', 15),
                                             justify=LEFT, highlightcolor=BG_COLOR,
                                             highlightbackground='gray', highlightthickness=1)
        emergency_contact_name_entry.place(x=650, y=260, width=265, height=30)

        emergency_contact_num_lb = Label(self.employee_info_fm, text='Emergency Contact No',
                                         font=('Calibri', 15, 'bold'), fg='black')
        emergency_contact_num_lb.place(x=440, y=300)

        emergency_contact_num_entry = Entry(self.employee_info_fm, textvariable=self.var_emergency_contact,
                                            font=('Calibri', 15),
                                            justify=LEFT, highlightcolor=BG_COLOR,
                                            highlightbackground='gray', highlightthickness=1)
        emergency_contact_num_entry.place(x=650, y=300, width=265, height=30)

        relationship_lb = Label(self.employee_info_fm, text='Relationship',
                                font=('Calibri', 15, 'bold'), fg='black')
        relationship_lb.place(x=440, y=340)

        combo_relationship = ttk.Combobox(self.employee_info_fm, textvariable=self.var_relationship,
                                          font=('Calibri', 14),
                                          width=17, state='readonly'
                                          )
        combo_relationship['value'] = ('Select Relationship', 'Brother', 'Sister', 'Father',
                                       'Mother', 'Guardian', 'Sibling', 'Friend', 'Husband',
                                       'Wife', 'Other')
        combo_relationship.current(0)
        combo_relationship.place(x=650, y=340, width=265, height=30)

        marital_status_lb = Label(self.employee_info_fm, text='Marital Status',
                                  font=('Calibri', 15, 'bold'), fg='black')
        marital_status_lb.place(x=440, y=220)

        combo_marital_status = ttk.Combobox(self.employee_info_fm, textvariable=self.var_marital_status,
                                            font=('Calibri', 14),
                                            width=17, state='readonly'
                                            )
        combo_marital_status['value'] = ('Select Status', 'Married', 'Single', 'Divorced',
                                         'Widowed', 'Engaged')
        combo_marital_status.current(0)
        combo_marital_status.place(x=650, y=220, width=265, height=30)

        country_lb = Label(self.employee_info_fm, text='Country',
                           font=('Calibri', 15, 'bold'), fg='black')
        country_lb.place(x=5, y=300)

        combo_country = ttk.Combobox(self.employee_info_fm, textvariable=self.var_country,
                                     font=('Calibri', 14),
                                     width=17, state='readonly'
                                     )
        combo_country['value'] = ('Select Country', 'Singapore', 'Malaysia', 'Indonesia',
                                  'Thailand', 'China', 'Taiwan', 'Hong Kong', 'Japan',
                                  'Korea', 'United Kingdom', 'United States', 'Ireland',
                                  'Vietnam', 'India', 'Switzerland', 'Other')
        combo_country.current(0)
        combo_country.place(x=152, y=300, width=265, height=30)

        password_lb = Label(self.employee_info_fm, text='Password',
                            font=('Calibri', 15, 'bold'), fg='black')
        password_lb.place(x=5, y=340)

        self.password_entry = Entry(self.employee_info_fm,
                                    font=('Calibri', 18),
                                    justify=LEFT, highlightcolor=BG_COLOR,
                                    highlightbackground='gray', highlightthickness=2,
                                    show='*')
        self.password_entry.place(x=152, y=340, width=265, height=30)

        register_employee_detail_btn = Button(self.employee_info_fm, text='Register', font=FONT_BOLD_18,
                                              bg=BG_COLOR, fg=FG_COLOR, command=self.add_data)
        register_employee_detail_btn.place(x=950, y=40, width=120, height=50)

        update_employee_detail_btn = Button(self.employee_info_fm, text='Update', font=FONT_BOLD_18,
                                            bg=BG_COLOR, fg=FG_COLOR, command=self.update_data)
        update_employee_detail_btn.place(x=950, y=130, width=120, height=50)

        delete_employee_detail_btn = Button(self.employee_info_fm, text='Delete', font=FONT_BOLD_18,
                                            bg=BG_COLOR, fg=FG_COLOR, command=self.delete_data)
        delete_employee_detail_btn.place(x=950, y=220, width=120, height=50)

        clear_btn = Button(self.employee_info_fm, text='Clear', font=FONT_BOLD_18,
                           bg=BG_COLOR, fg=FG_COLOR, command=self.clear_entry)
        clear_btn.place(x=950, y=310, width=120, height=50)

        is_admin_entry = Checkbutton(self.employee_info_fm, text='Assign Admin?', font=('Calibri', 12, 'bold'),
                                     fg='dark red', variable=self.var_is_admin)
        is_admin_entry.place(x=948, y=380)

        self.enrolment_status_lb = Label(self.face_id_fm, text='Enrolment Status:\nNot Enrolled',
                                         font=('Calibri', 15, 'bold'), fg='black')
        self.enrolment_status_lb.place(x=30, y=20)

        start_facial_enrolment_lb = Label(self.face_id_fm, text='Step 1:\n'
                                                                'Begin Facial Enrolment',
                                          font=('Calibri', 15, 'bold'), fg='black')
        start_facial_enrolment_lb.place(x=6, y=100)

        capture_img_btn = Button(self.face_id_fm, text='Capture Image', font=FONT_BOLD_18,
                                 bg=BG_COLOR, fg=FG_COLOR, command=self.take_images)
        capture_img_btn.place(x=25, y=160, width=170, height=45)

        confirm_facial_enrolment_lb = Label(self.face_id_fm, text='Step 2:\n'
                                                                  'Confirm Enrolment',
                                            font=('Calibri', 15, 'bold'), fg='black',
                                            )
        confirm_facial_enrolment_lb.place(x=25, y=240)

        confirm_img_btn = Button(self.face_id_fm, text='Save Profile', font=FONT_BOLD_18,
                                 bg=BG_COLOR, fg=FG_COLOR, command=self.train_images)
        confirm_img_btn.place(x=25, y=300, width=170, height=45)

        self.search_fm = LabelFrame(self.table_fm, bd=3, relief=RIDGE,
                                    text='Search Employee',
                                    font=('Calibri', 10, 'bold'),
                                    fg='black')
        self.search_fm.place(x=0, y=0, width=1321, height=55)

        search_by = Label(self.search_fm, text='Search By:',
                          font=('Calibri', 11, 'bold'), bg='red', fg='white',
                          width=16)
        search_by.grid(row=0, column=0, sticky=W, padx=5)

        com_text_search = ttk.Combobox(self.search_fm, state='readonly',
                                       font=('Calibri', 11, 'bold'),
                                       width=40, height=40, textvariable=self.var_com_text_search)
        com_text_search['value'] = ('Search Option', 'employee_id', 'contact_number')
        com_text_search.current(0)
        com_text_search.grid(row=0, column=1, sticky=W, padx=5)

        txt_search_entry = ttk.Entry(self.search_fm, width=40,
                                     font=('Calibri', 11, 'bold'),
                                     justify=LEFT,
                                     textvariable=self.var_text_search)
        txt_search_entry.grid(row=0, column=2, padx=5)

        search_btn = Button(self.search_fm, text='Search', font=('Calibri', 11, 'bold'),
                            width=14, bg=BG_COLOR, fg=FG_COLOR, command=self.search_table)
        search_btn.grid(row=0, column=3, padx=5)

        show_all_btn = Button(self.search_fm, text='Show All', font=('Calibri', 11, 'bold'),
                              width=14, bg=BG_COLOR, fg=FG_COLOR, command=self.fetch_data)
        show_all_btn.grid(row=0, column=4, padx=5)

        self.employee_table_fm = Frame(self.table_fm, bd=3, relief=RIDGE)
        self.employee_table_fm.place(x=0, y=55, width=1321, height=89)

        scroll_x = ttk.Scrollbar(self.employee_table_fm, orient=HORIZONTAL)
        scroll_y = ttk.Scrollbar(self.employee_table_fm, orient=VERTICAL)
        self.employee_table = ttk.Treeview(
            self.employee_table_fm,
            column=('employee_id', 'name', 'nric_id_no', 'contact', 'email',
                    'department', 'designation', 'address', 'join_date',
                    'salary', 'annual_leave', 'sick_leave', 'gender', 'marital_status',
                    'emergency_name', 'emergency_contact', 'relationship',
                    'country',), xscrollcommand=scroll_x.set,
            yscrollcommand=scroll_y.set)
        scroll_x.pack(side=BOTTOM, fill=X)
        scroll_y.pack(side=RIGHT, fill=Y)

        scroll_x.config(command=self.employee_table.xview)
        scroll_y.config(command=self.employee_table.yview)

        self.employee_table.heading('employee_id', text='Employee ID')
        self.employee_table.heading('name', text='Name')
        self.employee_table.heading('nric_id_no', text='IC/Passport No')
        self.employee_table.heading('contact', text='Contact No')
        self.employee_table.heading('email', text='Email')
        self.employee_table.heading('department', text='Department')
        self.employee_table.heading('designation', text='Designation')
        self.employee_table.heading('address', text='Address')
        self.employee_table.heading('join_date', text='Joining Date')
        self.employee_table.heading('salary', text='Salary S$')
        self.employee_table.heading('annual_leave', text='Annual Leave')
        self.employee_table.heading('sick_leave', text='Sick Leave')
        self.employee_table.heading('gender', text='Gender')
        self.employee_table.heading('emergency_name', text='Emergency Name')
        self.employee_table.heading('emergency_contact', text='Emergency Contact')
        self.employee_table.heading('relationship', text='Relationship')
        self.employee_table.heading('marital_status', text='Marital Status')
        self.employee_table.heading('country', text='Country')

        self.employee_table['show'] = 'headings'

        self.employee_table.column('employee_id', width=50)
        self.employee_table.column('name', width=100)
        self.employee_table.column('nric_id_no', width=100)
        self.employee_table.column('contact', width=80)
        self.employee_table.column('email', width=120)
        self.employee_table.column('department', width=100)
        self.employee_table.column('designation', width=100)
        self.employee_table.column('address', width=280)
        self.employee_table.column('join_date', width=80)
        self.employee_table.column('salary', width=60)
        self.employee_table.column('annual_leave', width=80)
        self.employee_table.column('sick_leave', width=80)
        self.employee_table.column('gender', width=50)
        self.employee_table.column('marital_status', width=60)
        self.employee_table.column('emergency_name', width=100)
        self.employee_table.column('emergency_contact', width=80)
        self.employee_table.column('relationship', width=60)
        self.employee_table.column('country', width=70)

        self.employee_table.pack(fill=BOTH, expand=1)

        self.employee_table.bind('<ButtonRelease>', self.get_cursor)
        self.fetch_data()

        self.employee_mgmt_fm.pack(pady=40)
        self.employee_mgmt_fm.pack_propagate(False)
        self.employee_mgmt_fm.configure(width=1340, height=755)

    def check_invalid_email(self, email):
        pattern = "^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$"
        match = re.match(pattern=pattern, string=email)
        return bool(match)

    @staticmethod
    def assure_path_exists(path):
        if not os.path.exists(path):
            os.makedirs(path)

    def take_images(self):
        status = self.enrolment_status_lb.cget("text").split('\n')[1]
        if status.lower() == "enrolled":
            messagebox.showerror('Already Enrolled',
                                 'Staff is already enrolled!', parent=self.root)
            return
        employee_id = self.var_empID.get()
        employee_name = self.var_name.get()

        if not employee_id or not employee_name:
            messagebox.showerror('Error', 'Please select an employee first!')
            return

        face_classifier = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

        def face_cropped(img):
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_classifier.detectMultiScale(gray, 1.3, 5)
            if len(faces) > 0:
                (x, y, w, h) = faces[0]
                face_cropped = img[y:y + h, x:x + w]
                return face_cropped

        cam = cv2.VideoCapture(0)
        img_id = 0

        path = os.path.abspath("FaceData")
        self.assure_path_exists(path)

        employee_name_clean = ''.join(e for e in employee_name if e.isalnum())
        image_filename = f"{employee_name_clean}.{employee_id}"

        while True:
            ret, my_frame = cam.read()
            cropped_face = face_cropped(my_frame)
            if cropped_face is not None:
                img_id += 1
                face = cv2.resize(cropped_face, (450, 450))
                face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
                image_path = f"FaceData/{image_filename}.{img_id}.jpg"
                cv2.imwrite(image_path, face)
                cv2.putText(face, str(img_id), (50, 50),
                            cv2.FONT_HERSHEY_COMPLEX, 2,
                            (0, 255, 0), 2)

                cv2.imshow('Capturing Images', face)

            if cv2.waitKey(1) == 13 or int(img_id) == 200:
                break

        cam.release()
        cv2.destroyAllWindows()
        self.enrolment_status_lb.config(text='Enrolment Status:\nImages Captured')
        messagebox.showinfo('Result', 'Images Capture Successfully.')

    def train_images(self):
        employee_id = self.var_empID.get()
        employee_name = self.var_name.get()

        if not employee_id or not employee_name:
            messagebox.showerror('Error', 'Please select a valid employee!')
            return

        self.assure_path_exists("FaceData/")
        self.assure_path_exists("Classifier/")

        employee_name_clean = ''.join(e for e in employee_name if e.isalnum())
        image_filename = f"{employee_name_clean}.{employee_id}"
        face_data_path = os.path.join("FaceData", f"{image_filename}.*.jpg")
        if not glob.glob(face_data_path):
            messagebox.showerror('Error',
                                 'Face data for the selected employee '
                                 'is not available. Cannot proceed with training.')
            return

        data_dir = "FaceData"
        path = [os.path.join(data_dir, file) for file in os.listdir(data_dir)]
        faces = []
        ids = []

        for image in path:
            img = Image.open(image).convert('L')  # Gray Scale Image
            imageNp = np.array(img, 'uint8')
            id = int(os.path.split(image)[1].split('.')[1])
            faces.append(imageNp)
            ids.append(id)

        ids = np.array(ids)
        recognizer = cv2.face_LBPHFaceRecognizer.create()
        recognizer.train(faces, ids)
        recognizer.write("Classifier/Classifier.yml")
        cv2.destroyAllWindows()
        self.enrolment_status_lb.config(text='Enrolment Status:\nEnrolled')
        self.update_face_id_in_database(employee_id, 'Enrolled')
        messagebox.showinfo('Status', 'Successfully Enrolled.')

    def update_enrolment_status(self):
        try:
            with sqlite3.connect('employees.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT face_id FROM employees WHERE employee_id = ?'
                               , (self.var_empID.get(),))
                result = cursor.fetchone()
                if result:
                    status = result[0]
                    self.enrolment_status_lb.config(text=f'Enrolment Status:\n{status}')
        except Exception as es:
            messagebox.showerror('Error', f'Due To: {str(es)}', parent=self.root)

    def update_face_id_in_database(self, employee_id, status):
        try:
            with sqlite3.connect('employees.db') as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE employees SET face_id = ? WHERE employee_id = ?',
                               (status, employee_id))
                conn.commit()
        except Exception as es:
            messagebox.showerror('Error', f'Due To: {str(es)}', parent=self.root)

    def add_data(self):
        mandatory_fields = [
            self.var_empID.get(),
            self.var_name.get(),
            self.password_entry.get(),
            self.var_nric.get(),
            self.var_contact.get(),
            self.var_address.get(),
            self.var_email.get(),
            self.var_dept.get(),
            self.var_designation.get(),
            self.var_join_date.get(),
            self.var_salary.get(),
            self.var_annual_leave.get(),
            self.var_sick_leave.get(),
            self.var_gender.get(),
            self.var_emergency_name.get(),
            self.var_emergency_contact.get(),
            self.var_relationship.get(),
            self.var_marital_status.get(),
            self.var_country.get(),
        ]
        if any(field == '' for field in mandatory_fields):
            messagebox.showerror('Error', 'All fields are required!')
        elif not self.check_invalid_email(self.var_email.get()):
            messagebox.showerror('Invalid Email',
                                 'The email format is invalid. Please enter a valid email.')
            return
        elif self.var_dept.get() == 'Select Department':
            messagebox.showerror('Invalid Department',
                                 'Please select department!')
            return
        elif self.var_designation.get() == 'Select Designation':
            messagebox.showerror('Invalid Designation',
                                 'Please select designation!')
            return
        elif self.var_country.get() == 'Select Country':
            messagebox.showerror('Invalid Country',
                                 'Please select country!')
            return
        elif self.var_gender.get() == 'Select Gender':
            messagebox.showerror('Invalid Gender',
                                 'Please select gender!')
            return
        elif self.var_marital_status.get() == 'Select Status':
            messagebox.showerror('Invalid Status',
                                 'Please select marital status!')
            return
        elif self.var_relationship.get() == 'Select Relationship':
            messagebox.showerror('Invalid Relationship',
                                 'Please select emergency contact relationship!')
            return
        elif not self.var_empID.get().isdigit():
            messagebox.showerror('Invalid Employee ID', 'Employee ID must be a number!')
            return
        elif not self.var_contact.get().isdigit():
            messagebox.showerror('Invalid Contact', 'Contact number must be a number!')
            return
        elif not self.var_emergency_contact.get().isdigit():
            messagebox.showerror('Invalid Emergency Contact', 'Emergency contact number must be a number!')
            return
        elif not self.var_salary.get().replace(".", "", 1).isdigit():
            messagebox.showerror('Invalid Salary', 'Salary must be a number!')
            return
        elif not self.var_annual_leave.get().replace(".", "", 1).isdigit():
            messagebox.showerror('Invalid Annual Leave', 'Annual leave must be a number!')
            return
        elif not self.var_sick_leave.get().replace(".", "", 1).isdigit():
            messagebox.showerror('Invalid Sick Leave', 'Sick leave must be a number!')
            return
        elif int(self.var_sick_leave.get()) > 60:
            messagebox.showerror('Invalid Sick Leave', 'Sick leave cannot be greater than 60 days!')
            return
        elif int(self.var_annual_leave.get()) > 30:
            messagebox.showerror('Invalid Annual Leave', 'Annual leave cannot be greater than 60 days!')
            return
        else:
            try:
                if self.var_is_admin.get() == 1:
                    admin_confirmation = messagebox.askyesno('Admin Confirmation',
                                                             f'Are you sure you want to register '
                                                             f'{self.var_name.get()} as an Admin?')
                    if not admin_confirmation:
                        return
                with sqlite3.connect('employees.db') as conn:
                    cursor = conn.cursor()

                    cursor.execute('SELECT * FROM employees WHERE employee_id = ?',
                                   (self.var_empID.get(),))
                    existing_employee = cursor.fetchone()

                    if existing_employee:
                        messagebox.showerror('Error',
                                             'Employee ID already exists in the database!')
                        return

                    hashed_password = self.hash_password(self.password_entry.get())
                    default_face_id_status = 'Not Enrolled'
                    cursor.execute('INSERT INTO employees (employee_id, name, password, fin_nric_id,'
                                   'contact_number, address, email, department, designation,'
                                   'joining_date, salary, leave_entitlement, sick_leave_entitlement,'
                                   'gender, emergency_contact_name, emergency_contact_number, '
                                   'relationship, marital_status, country, face_id, is_admin)'
                                   ' VALUES (?, ?, ?, ?, ?, ?, '
                                   '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (
                                       self.var_empID.get(),
                                       self.var_name.get(),
                                       hashed_password,
                                       self.var_nric.get(),
                                       self.var_contact.get(),
                                       self.var_address.get(),
                                       self.var_email.get(),
                                       self.var_dept.get(),
                                       self.var_designation.get(),
                                       self.var_join_date.get(),
                                       self.var_salary.get(),
                                       self.var_annual_leave.get(),
                                       self.var_sick_leave.get(),
                                       self.var_gender.get(),
                                       self.var_emergency_name.get(),
                                       self.var_emergency_contact.get(),
                                       self.var_relationship.get(),
                                       self.var_marital_status.get(),
                                       self.var_country.get(),
                                       default_face_id_status,
                                       self.var_is_admin.get()
                                   ))
                    cursor.execute('INSERT INTO leave_balance (employee_id, '
                                   'annual_leave_balance, sick_leave_balance)'
                                   ' VALUES (?, ?, ?)', (
                                       self.var_empID.get(),
                                       self.var_annual_leave.get(),
                                       self.var_sick_leave.get()
                                   ))
                    conn.commit()
                    messagebox.showinfo('Success',
                                        'Employee has been registered!', parent=self.root)
                    self.fetch_data()
                conn.close()
            except Exception as es:
                messagebox.showerror('Error', f'Due To: {str(es)}', parent=self.root)

    def delete_face_data(self, employee_id, employee_name):
        employee_name_clean = ''.join(e for e in employee_name if e.isalnum())
        image_filename = f"{employee_name_clean}.{employee_id}"

        directory_path = os.path.abspath("FaceData")
        file_pattern = os.path.join(directory_path, f"{image_filename}.*.jpg")

        for file_path in glob.glob(file_pattern):
            os.remove(file_path)
            print(f"Deleted: {file_path}")

    def delete_data(self):
        if self.var_empID.get() == '':
            messagebox.showerror('Error', 'Fields are empty! Please select one.')
        elif self.var_empID.get() == self.employeeID:
            messagebox.showerror('Error', "You can't delete yourself!")
        else:
            try:
                delete = messagebox.askyesno('Delete Employee',
                                             f'Are you sure delete '
                                             f'{self.var_name.get()}?', parent=self.root)
                if delete > 0:
                    with sqlite3.connect('employees.db') as conn:
                        cursor = conn.cursor()

                        cursor.execute("SELECT name "
                                       "FROM employees "
                                       "WHERE employee_id = ?", (self.var_empID.get(),))
                        row = cursor.fetchone()
                        if row:
                            employee_name = row[0]

                            cursor.execute('DELETE FROM employees WHERE employee_id = ?',
                                           (self.var_empID.get(),))
                            cursor.execute('DELETE FROM leave_balance WHERE employee_id = ?',
                                           (self.var_empID.get(),))
                            conn.commit()

                            self.delete_face_data(self.var_empID.get(), employee_name)
                            self.fetch_data()
                            messagebox.showinfo('Delete Success',
                                                'Employee and corresponding face data have been deleted.')
                        else:
                            messagebox.showerror('Error', 'Employee not found.', parent=self.root)
                else:
                    if not delete:
                        return
            except Exception as es:
                messagebox.showerror('Error', f'Due To: {str(es)}', parent=self.root)

    # Search
    def search_table(self):
        search_option = self.var_com_text_search.get()
        search_value = self.var_text_search.get()
        if search_option == 'Search Option':
            messagebox.showerror('Error', 'Please select option.')
        elif search_value == '':
            messagebox.showerror('Error', 'Please type some keywords!')
        else:
            try:
                with sqlite3.connect('employees.db') as conn:
                    cursor = conn.cursor()
                    selected_columns = ['employee_id', 'name', 'fin_nric_id', 'contact_number', 'email',
                                        'department', 'designation', 'address', 'joining_date', 'salary',
                                        'leave_entitlement', 'sick_leave_entitlement', 'gender', 'marital_status',
                                        'emergency_contact_name', 'emergency_contact_number', 'relationship',
                                        'country']
                    query = f'SELECT {", ".join(selected_columns)} FROM employees WHERE {search_option} LIKE ?'
                    cursor.execute(query, ('%' + search_value + '%',))
                    rows = cursor.fetchall()
                    if not rows:
                        messagebox.showinfo('No Results', 'No matching records found.')
                        return
                    self.employee_table.delete(*self.employee_table.get_children())

                    for row in rows:
                        self.employee_table.insert('', 'end', values=row)
            except Exception as es:
                messagebox.showerror('Error', f'Due To: {str(es)}', parent=self.root)

    def clear_entry(self):
        self.password_entry = StringVar()
        self.var_empID.set('')
        self.var_name.set('')
        self.var_nric.set('')
        self.var_contact.set('')
        self.var_email.set('')
        self.var_dept.set('Select Department')
        self.var_designation.set('Select Designation')
        self.var_address.set('')
        self.var_join_date.set('')
        self.var_salary.set('')
        self.var_annual_leave.set('')
        self.var_sick_leave.set('')
        self.var_gender.set('Select Gender')
        self.var_emergency_name.set('')
        self.var_emergency_contact.set('')
        self.var_relationship.set('Select Relationship')
        self.var_marital_status.set('Select Status')
        self.var_country.set('Select Country')
        self.password_entry.set('')
        self.var_is_admin.set(0)

    def fetch_data(self):
        with sqlite3.connect('employees.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT employee_id, name, fin_nric_id, contact_number,'
                           'email, department, designation, address, joining_date,'
                           'salary, leave_entitlement, sick_leave_entitlement, gender, marital_status,'
                           'emergency_contact_name, emergency_contact_number, relationship,'
                           'country , is_admin FROM employees')
            data = cursor.fetchall()
            if len(data) != 0:
                self.employee_table.delete(*self.employee_table.get_children())
                for row in data:
                    self.employee_table.insert('', END, values=row)
            conn.commit()
        conn.close()

    def update_data(self):
        mandatory_fields = [
            self.var_name.get(),
            self.var_nric.get(),
            self.var_contact.get(),
            self.var_address.get(),
            self.var_email.get(),
            self.var_dept.get(),
            self.var_designation.get(),
            self.var_join_date.get(),
            self.var_salary.get(),
            self.var_annual_leave.get(),
            self.var_sick_leave.get(),
            self.var_emergency_name.get(),
            self.var_emergency_contact.get(),
            self.var_relationship.get(),
            self.var_marital_status.get(),
            self.var_country.get(),
            self.var_is_admin.get()
        ]
        if any(field == '' for field in mandatory_fields):
            messagebox.showerror('Error', 'All fields except employee ID, '
                                          'gender, and password are required!')
        elif not self.check_invalid_email(self.var_email.get()):
            messagebox.showerror('Invalid Email',
                                 'The email format is invalid. Please enter a valid email.')
            return
        elif self.var_dept.get() == 'Select Department':
            messagebox.showerror('Invalid Department',
                                 'Please select department!')
            return
        elif self.var_designation.get() == 'Select Designation':
            messagebox.showerror('Invalid Designation',
                                 'Please select designation!')
            return
        elif self.var_country.get() == 'Select Country':
            messagebox.showerror('Invalid Country',
                                 'Please select country!')
            return
        elif self.var_marital_status.get() == 'Select Status':
            messagebox.showerror('Invalid Status',
                                 'Please select marital status!')
            return
        elif self.var_relationship.get() == 'Select Relationship':
            messagebox.showerror('Invalid Relationship',
                                 'Please select emergency contact relationship!')
            return
        elif not self.var_empID.get().isdigit():
            messagebox.showerror('Invalid Employee ID', 'Employee ID must be a number!')
            return
        elif not self.var_contact.get().isdigit():
            messagebox.showerror('Invalid Contact', 'Contact number must be a number!')
            return
        elif not self.var_emergency_contact.get().isdigit():
            messagebox.showerror('Invalid Emergency Contact', 'Emergency contact number must be a number!')
            return
        elif not self.var_salary.get().replace(".", "", 1).isdigit():
            messagebox.showerror('Invalid Salary', 'Salary must be a number!')
            return
        elif not self.var_annual_leave.get().replace(".", "", 1).isdigit():
            messagebox.showerror('Invalid Annual Leave', 'Annual leave must be a number!')
            return
        elif not self.var_sick_leave.get().replace(".", "", 1).isdigit():
            messagebox.showerror('Invalid Sick Leave', 'Sick leave must be a number!')
            return
        elif int(self.var_sick_leave.get()) > 60:
            messagebox.showerror('Invalid Sick Leave', 'Sick leave cannot be greater than 60 days!')
            return
        elif int(self.var_annual_leave.get()) > 30:
            messagebox.showerror('Invalid Annual Leave', 'Annual leave cannot be greater than 60 days!')
            return
        else:
            try:
                update = messagebox.askyesno('Update Data', 'Updating Employee Data:\n'
                                                            'Are you sure want to proceed?')
                if self.var_is_admin.get() == 1:
                    admin_confirmation = messagebox.askyesno('Admin Confirmation',
                                                             f'Are you sure you want to update '
                                                             f'{self.var_name.get()} as an Admin?')
                    if not admin_confirmation:
                        return
                if update > 0:
                    with sqlite3.connect('employees.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute('UPDATE employees SET name = ?,'
                                       'fin_nric_id = ?, contact_number = ?, address = ?,'
                                       'email = ?, department = ?, designation = ?, joining_date = ?,'
                                       'salary = ?, leave_entitlement = ?, sick_leave_entitlement = ?,'
                                       'emergency_contact_name = ?, emergency_contact_number = ?,'
                                       'relationship = ?, marital_status = ?, country = ?, is_admin = ?'
                                       'WHERE employee_id = ?', (self.var_name.get(),
                                                                 self.var_nric.get(),
                                                                 self.var_contact.get(),
                                                                 self.var_address.get(),
                                                                 self.var_email.get(),
                                                                 self.var_dept.get(),
                                                                 self.var_designation.get(),
                                                                 self.var_join_date.get(),
                                                                 self.var_salary.get(),
                                                                 self.var_annual_leave.get(),
                                                                 self.var_sick_leave.get(),
                                                                 self.var_emergency_name.get(),
                                                                 self.var_emergency_contact.get(),
                                                                 self.var_relationship.get(),
                                                                 self.var_marital_status.get(),
                                                                 self.var_country.get(),
                                                                 self.var_is_admin.get(),
                                                                 self.var_empID.get()))
                        conn.commit()

                else:
                    if not update:
                        return
                self.fetch_data()
                conn.close()
                messagebox.showinfo('Success',
                                    'Employee data update successful!', parent=self.root)
            except Exception as es:
                messagebox.showerror('Error', f'Due To: {str(es)}', parent=self.root)

    def get_cursor(self, event=''):
        cursor_row = self.employee_table.focus()
        content = self.employee_table.item(cursor_row)
        data = content['values']
        self.var_empID.set(data[0])
        self.var_name.set(data[1])
        self.var_nric.set(data[2])
        self.var_contact.set(data[3])
        self.var_email.set(data[4])
        self.var_dept.set(data[5])
        self.var_designation.set(data[6])
        self.var_address.set(data[7])
        self.var_join_date.set(data[8])
        self.var_salary.set(data[9])
        annual_leave_float = float(data[10])
        self.var_annual_leave.set(
            int(annual_leave_float) if annual_leave_float == int(annual_leave_float) else annual_leave_float)
        sick_leave_float = float(data[11])
        self.var_sick_leave.set(
            int(sick_leave_float) if sick_leave_float == int(sick_leave_float) else sick_leave_float)
        self.var_gender.set(data[12])
        self.var_marital_status.set(data[13])
        self.var_emergency_name.set(data[14])
        self.var_emergency_contact.set(data[15])
        self.var_relationship.set(data[16])
        self.var_country.set(data[17])
        self.update_enrolment_status()
        self.var_is_admin.set(data[18])

    def hash_password(self, password: str) -> bytes:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password

    def return_to_dashboard(self):
        self.employee_mgmt_fm.destroy()
        Dashboard(self.root, self.employeeID, self.is_admin)


class ResetPassword(MainFrame):
    def __init__(self, root):
        super().__init__(root)

        self.reset_password_page_fm = Frame(self.root, highlightbackground=self.bg_color,
                                            highlightthickness=3)

        header_lb = Label(self.reset_password_page_fm,
                          text='RESET PASSWORD',
                          bg=self.bg_color, fg='white', font=('Calibri', 22, 'bold'))
        header_lb.place(x=0, y=0, width=1340, height=50)

        close_btn = Button(self.reset_password_page_fm, text='X',
                           bg=self.bg_color, fg='white', font=('Calibri', 18, 'bold'),
                           bd=0, command=self.close)
        close_btn.place(x=1300, y=0)

        self.employeeID_lb = Label(self.reset_password_page_fm, text='Enter employee ID',
                                   font=('Calibri', 20, 'bold'), fg=self.bg_color)
        self.employeeID_lb.place(x=350, y=260)

        self.employeeID_entry = Entry(self.reset_password_page_fm, font=('Calibri', 18),
                                      justify=LEFT, highlightcolor=self.bg_color,
                                      highlightbackground='gray', highlightthickness=2)
        self.employeeID_entry.place(x=640, y=260, width=280, height=40)

        self.new_password_lb = Label(self.reset_password_page_fm, text='Enter new password',
                                     font=('Calibri', 20, 'bold'), fg=self.bg_color)
        self.new_password_lb.place(x=350, y=330)

        self.new_password_entry = Entry(self.reset_password_page_fm, font=('Calibri', 18),
                                        justify=LEFT, highlightcolor=self.bg_color,
                                        highlightbackground='gray', highlightthickness=2,
                                        show='*')
        self.new_password_entry.place(x=640, y=330, width=280, height=40)

        self.verify_password_lb = Label(self.reset_password_page_fm, text='Verify new password',
                                        font=('Calibri', 20, 'bold'), fg=self.bg_color)
        self.verify_password_lb.place(x=350, y=400)

        self.verify_password_entry = Entry(self.reset_password_page_fm, font=('Calibri', 18),
                                           justify=LEFT, highlightcolor=self.bg_color,
                                           highlightbackground='gray', highlightthickness=2,
                                           show='*')
        self.verify_password_entry.place(x=640, y=400, width=280, height=40)

        reset_btn = Button(self.reset_password_page_fm,
                           text='Reset', font=('Calibri', 18, 'bold'),
                           bg=self.bg_color, fg='white',
                           command=self.reset_password)
        reset_btn.place(x=480, y=500, width=370, height=50)

        cancel_btn = Button(self.reset_password_page_fm,
                            text='Cancel', font=('Calibri', 18, 'bold'),
                            bg=self.bg_color, fg='white',
                            command=self.close)
        cancel_btn.place(x=480, y=580, width=370, height=50)

        self.reset_password_page_fm.pack(pady=40)
        self.reset_password_page_fm.pack_propagate(False)
        self.reset_password_page_fm.configure(width=1340, height=760)

    def close(self):
        self.reset_password_page_fm.destroy()
        self.root.update()
        LoginApp(self.root)

    def hash_password(self, password: str) -> bytes:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def reset_password(self):
        employeeID = self.employeeID_entry.get()
        new_password = self.new_password_entry.get()
        verify_password = self.verify_password_entry.get()

        if new_password == '' or verify_password == '' or employeeID == '':
            messagebox.showerror("Error", "All fields are required!")
        elif new_password != '' or verify_password != '' or employeeID != '':
            if new_password != verify_password:
                messagebox.showerror("Error", "Passwords do not match.")
            else:
                hashed_password = self.hash_password(new_password)
                with sqlite3.connect('employees.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE employees '
                                   'SET password = ? WHERE employee_id = ?',
                                   (hashed_password, employeeID))
                    conn.commit()

                if cursor.rowcount:
                    messagebox.showinfo("Success", "Password reset successfully!")
                else:
                    messagebox.showerror("Error", "Employee ID not found.")


if __name__ == "__main__":
    db_file = "employees.db"
    initiate_db = InitiateDatabase(db_file)
    initiate_db.create_tables()
    root = Tk()
    app = LoginApp(root)
    root.mainloop()
