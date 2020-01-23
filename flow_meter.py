from flask import Flask, render_template, jsonify, json, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import update
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
import csv
import re
from fpdf import FPDF
from flask_login import UserMixin, LoginManager, current_user, login_user, logout_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import pandas as pd
import xlsxwriter
import sqlite3
from flask_mail import Mail, Message
import socket
import asyncio
import RPi.GPIO as GPIO
import time
import json
from threading import Thread
import sys
import psycopg2
import datetime
import math
import os
import os.path
from os import path
from taliabeeio import TaliaBeeIO
io = TaliaBeeIO()


def restart():
    command = ("/usr/bin/sudo /sbin/shutdown -r now")
    import subprocess
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)
# creating table
conn = sqlite3.connect('krohne_ak.db')
conn.execute("CREATE TABLE IF NOT EXISTS sensor_data ( id INTEGER PRIMARY KEY AUTOINCREMENT, value REAL, datetime_val TEXT )")
conn.execute("CREATE TABLE IF NOT EXISTS user_auth ( id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password VARCHAR(50),dob TEXT,email VARCHAR(50),role VARCHAR(30),user_created_date TEXT)")
conn.commit()
print('rohne_ak.db created succesfully')
############################## MAIL ##################
MAIL_RECEPIENTS = ['abdulsametakbass@gmail.com']
MAIL_SENDER = 'ctmmodule@gmail.com'
# This is for setting count value from DB when server restarts
c = conn.cursor()
c.execute("SELECT value from sensor_data order by id desc limit 1")
rec = c.fetchall()
if rec:
    for i in rec:
        count = int(i[0] / 0.040)
else:
    count = 0
print('This is the global count value', count)
io.do6 = True  # Green indicator is ON mode


def flow_recording():
    FLOW_SENSOR_KROHNE = 18
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(FLOW_SENSOR_KROHNE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def send_req(flow_val, count):
        conn = sqlite3.connect('/home/pi/Desktop/26_final/krohne_ak.db')
        conn.execute("INSERT INTO sensor_data (value,datetime_val) VALUES ('{}','{}')".format(flow_val, str(datetime.datetime.now())[0:19]))
        conn.commit()
        print('record inserted', count)

    def countPulse(channel):
        try:
            global count
            count = count + 1
            # print(count) # that is not referance to see our count. 1 more overloop
            flow_val = count * 0.040  # 1 pulse = 0,040 m^3
            task_set = loop.create_task(send_req(flow_val, count))
            # print(count)
        except (Exception, psycopg2.Error) as error:
            print('Exception occured while inserting data into database: ' + str(error))
    GPIO.add_event_detect(FLOW_SENSOR_KROHNE, GPIO.FALLING, callback=countPulse)
# This file is called through threading module
    while True:
        task_list = asyncio.Task.all_tasks()
        if io.di15 == 1:
            restart()
        else:
            if task_list:
                for i in task_list:
                    loop.run_until_complete(i)
                    i.cancel()
# Flask application UI start oks.tart fresh agaign
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///krohne_ak.db'
app.secret_key = 'XP)(OIUip08u7yhg8'
db = SQLAlchemy(app)
db.Model.metadata.reflect(db.engine)
login = LoginManager(app)
app.config.update(
    DEBUG=False,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME='',
    MAIL_PASSWORD=''
)
mail = Mail(app)

# Flask-Login keeps track of the logged in user by storing its unique identifier in Flask's user session
# Each time the logged-in user navigates to a new page, it retrieves the ID of the user from the session, and then loads that user into memory.


@login.user_loader
def load_user(user_id):
    return user_auth.query.get(user_id)


class user_auth(db.Model, UserMixin):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(100))
    dob = db.Column(db.String(50))
    email = db.Column(db.String(50))
    role = db.Column(db.String(50))


class MyModelView(ModelView):

    def is_accessible(self):
        user = user_auth.query.get(current_user.get_id())
        roles_list = ['SuperAdmin', ]
        if current_user.is_authenticated and user.role in roles_list:
            return True  # if True table is visible in Admin page
        else:
            return False  # if False table is not visible in Admin page

    def validate_form(self, form):
        try:
            if request.method == 'POST' and str(request.full_path).split('?')[0] == '/admin/user_auth/delete/':
                return True
            elif request.method == 'POST':
                if form.username.data != None and form.email.data != None and str(request.full_path).split('?')[0] == '/admin/user_auth/new/':
                    user = user_auth.query.filter_by(email=form.email.data, username=form.username.data).first()
                    if not user:
                        form.username.data = form.username.data
                    else:
                        flash('Email/username already exist!! Please try with new one')
                        # and request.method == 'POST' and str(request.full_path).split('?')[0] == '/admin/user_auth/edit/'
                        return False

                if form.email.data != None:
                    check_email_address = re.match('[^@]+@[^@]+\.[^@]+', form.email.data)
                    if check_email_address:
                        form.email.data = form.email.data
                    else:
                        flash('Please check the Email Address entered!')
                        return False

                if form.role.data != None and form.role.data not in ['SuperAdmin', 'Engineer', 'Manager']:
                    flash('Please enter SuperAdmin/Engineer/Manager roles!!')
                    return False
                if form.dob.data != None:
                    if '-' in form.dob.data:
                        dob_list = form.dob.data.split('-')
                        year = datetime.datetime.today().year
                        min_year = year - 100
                        max_year = year - 18

                        if len(dob_list[0]) == 4 and len(dob_list[1]) == 2 and len(dob_list[2]) == 2:
                            if min_year <= int(dob_list[0]) <= max_year:
                                if 1 <= int(dob_list[1]) <= 12:
                                    if 1 <= int(dob_list[2]) <= 31:
                                        form.dob.data = form.dob.data
                                    else:
                                        flash('Check the Day you have entered')
                                        return False
                                else:
                                    flash('Check the Month you have entered')
                                    return False
                            else:
                                flash('Check the Year you have entered')
                                return False
                        else:
                            flash('DOB should be in YYYY-MM-DD format')
                            return False

                    else:
                        flash('DOB should be in YYYY-MM-DD format')
                        return False

                if form.password.data != None and str(request.full_path).split('?')[0] == '/admin/user_auth/new/':
                    form.password.data = generate_password_hash(form.password.data, method='sha256')
                elif form.password.data != None and str(request.full_path).split('?')[0] == '/admin/user_auth/edit/':
                    if str(form.password.data)[0:7] == "sha256$" and len(form.password.data) > 35:
                        form.password.data = form.password.data
                    else:
                        form.password.data = generate_password_hash(form.password.data, method='sha256')

                if None in (form.username.data, form.password.data, form.email.data, form.role.data, form.dob.data):
                    flash('Missing Username/Password/Email/Role/DOB fields!!')
                    return False
                return super(MyModelView, self).validate_form(form)

                print(request.form)
        except Exception as e:
            print(e)
admin = Admin(app, name='   SAYSAN    ')
admin.add_view(MyModelView(user_auth, db.session))
# This is for creating super admin user
conn1 = sqlite3.connect('krohne_ak.db')
cur = conn.cursor()
cur.execute("SELECT * from user_auth where role = 'SuperAdmin' and username='superadmin'")
rec = cur.fetchall()
if rec:
    print('SuperAdmin user Already Exist!!')
else:
    new_user = user_auth(email='superadmin@superadmin.com', username='superadmin', password=generate_password_hash('superadmin', method='sha256'), dob='01-01-2000', role='SuperAdmin')
    db.session.add(new_user)
    db.session.commit()
    print('superadmin user has been created successfully!!')


@app.route('/', methods=['GET', 'POST'])
def landing_page():
    try:
        data = {}
        if current_user.is_authenticated:
            user = user_auth.query.get(current_user.get_id())
            data['role'] = user.role
            data['role_list'] = ['SuperAdmin', 'Engineer', 'Manager']
            data['user'] = current_user.is_authenticated
            return render_template('index.html', data=data)
        else:
            return render_template('login.html', data=data)
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        print('Exception occured in landing_page method: ' + str(e))
        io.do6 = False


@app.route('/login', methods=['POST', 'GET'])
def login():
    try:
        data = {}
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            print(username, password)
            user = user_auth.query.filter_by(username=username).first()
            if user:
                if check_password_hash(user.password, password):
                    login_user(user)
                    print(str(username) + ' : successfully logged in!!')
                    return redirect(url_for('landing_page'))
                else:
                    data['msg'] = 'Incorrect username or password'
                    return render_template('login.html', data=data)
            else:
                data['msg'] = 'user doesnot exists!!'
                return render_template('login.html', data=data)
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        print('Exception occured in login method: ' + str(e))


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('landing_page'))


@app.route("/forgot")
def forgot():
    data = {}
    return render_template('reset.html', data=data)


@app.route("/reset", methods=['GET', 'POST'])
def reset():
    try:
        first = request.args.get('first')
        username = request.args.get('username') if request.args.get('username') else ''
        dob = request.args.get('dob') if request.args.get('dob') else ''
        second = request.args.get('second')
        data = {}
        if request.method == 'GET' and first == 'true':

            user = user_auth.query.filter_by(username=username, dob=dob).first()
            print(user, dob, username)
            if user:
                data['is_success'] = True
                data['username'] = username
                print('is_success')
                return render_template('reset.html', data=data)
            else:
                data['is_success'] = False
                data['msg'] = 'incorrect username/DOB, please try again.'
                data['username'] = username
                print('not is_success')
                return render_template('reset.html', data=data)

        elif request.method == 'GET' and second == 'true':
            password = request.args.get('password')
            if username:
                user = user_auth.query.filter(user_auth.username == username).first()
                user.password = generate_password_hash(password, method='sha256')
                db.session.commit()
                print('updated successfully')
                return redirect(url_for('landing_page'))

        return redirect(url_for('landing_page'))
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        print('Exception occured in reset method: ' + str(e))

# live endpoint


@app.route('/live', methods=['GET', 'POST'])
def live():
    global flow
    try:
        conn = sqlite3.connect('/home/pi/Desktop/26_final/krohne_ak.db')
        cursor = conn.cursor()
        max_val = datetime.datetime.now()
        min_val = max_val - datetime.timedelta(0, 10)
        d = "SELECT MAX(value)-MIN(value) FROM sensor_data where datetime_val BETWEEN '{}' and '{}' ".format(str(min_val)[0:19], str(max_val)[0:19])
        cursor.execute(d)
        # print(d)
        rec = cursor.fetchall()
        for r in rec:
            if r[0] != None:
                # flow = "%.3f" % (r[0]/10)
                flow = float(str(r[0] / 10)[:4]) * 3600
                io.do7 = False
                io.do5 = False
            else:
                flow = 0
                io.do7 = True
                print(io.do7)

        d1 = 'SELECT value FROM sensor_data order by id desc'
        cursor.execute(d1)
        total_flow = cursor.fetchone()
        return json.dumps({"flow": flow, "time": str(max_val)[0:19], "total_flow": total_flow})
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        print('Exception occured in live method: ' + str(e))
        io.do6 = False
# Internal query method


def query_for_pdf_data(start_date, end_date, operator='d'):
    pdf_total_query = "SELECT distinct count(id)*0.04 FROM sensor_data where datetime_val BETWEEN '{}' and '{}' GROUP BY strftime('%{}', datetime_val) Order by datetime_val desc".format(start_date, end_date, operator)
    max_time_query = "SELECT datetime_val,max(value)/40 FROM sensor_data where datetime_val BETWEEN '{}' and '{}' GROUP BY strftime('%{}', datetime_val) Order by datetime_val desc".format(start_date, end_date, operator)
    min_time_query = "SELECT datetime_val,min(value)/40 FROM sensor_data where datetime_val BETWEEN '{}' and '{}' GROUP BY strftime('%{}', datetime_val) Order by datetime_val desc".format(start_date, end_date, operator)

    return pdf_total_query, max_time_query, min_time_query


def date_filter_query(pick_val, f1=None, f2=None, is_pdf=False,):
    try:
        import datetime
        from dateutil.relativedelta import relativedelta
        current_time = datetime.datetime.now()
        curr_day = current_time.day
        curr_hour = current_time.hour
        curr_month = datetime.date.today().month
        curr_year = datetime.date.today().year
        start_date = datetime.datetime.now() - datetime.timedelta(days=(curr_day - 1))
        if pick_val:
            if pick_val == 'today':  # not to worry lemee check it
                start_date = str(current_time)[0:10] + ' 00:00:00'
                end_date = '{} {}:59:59'.format(str(current_time)[0:10], str(curr_hour - 1))
                query = "SELECT distinct id,count(id),datetime_val,sum(value) FROM sensor_data where datetime_val BETWEEN '{}' and '{}' GROUP BY strftime('%H', datetime_val) Order by datetime_val desc".format(start_date, end_date)
                if is_pdf:
                    total, maxi, mini = query_for_pdf_data(start_date, end_date, operator="H")

            elif pick_val == 'week':
                start_date = datetime.datetime.now() - datetime.timedelta(days=7)
                end_date = datetime.datetime.now() - datetime.timedelta(days=1)
                start_date = str(start_date)[0:10] + ' 00:00:00'
                end_date = '{} {}:59:59'.format(str(end_date)[0:10], str(curr_hour - 1))
                query = "SELECT distinct id,count(id),datetime_val,sum(value) FROM sensor_data where datetime_val BETWEEN '{}' and '{}' GROUP BY strftime('%d', datetime_val) Order by datetime_val desc".format(start_date, end_date)
                if is_pdf:
                    total, maxi, mini = query_for_pdf_data(start_date, end_date, operator="d")

            elif pick_val == 'month':

                if curr_month == 1:
                    curr_month = 12
                    curr_year -= 1
                else:
                    curr_month -= 1
                if curr_month in list(range(1, 10)):
                    curr_month = '{}{}'.format(0, curr_month)

                start_date = '{}-{}-01 00:00:00'.format(curr_year, curr_month)
                end_date = '{}-{}-{} 23:59:59'.format(curr_year, curr_month, curr_day - 1)
                query = "SELECT distinct id,count(id),datetime_val,sum(value) FROM sensor_data where datetime_val BETWEEN '{}' and '{}' GROUP BY strftime('%d', datetime_val)  Order by datetime_val desc".format(start_date, end_date)
                if is_pdf:
                    total, maxi, mini = query_for_pdf_data(start_date, end_date, operator="d")
            elif pick_val == 'last_month':
                import calendar
                month = datetime.date.today().month
                year = datetime.date.today().year
                if month == 1:
                    month = 12
                    year -= 1
                else:
                    month -= 1
                if month in list(range(1, 10)):
                    month = '{}{}'.format(0, month)

                last_day = calendar.monthrange(year, int(month))[1]
                start_date = '{}-{}-01 00:00:00'.format(year, month)
                end_date = '{}-{}-{} 23:59:59'.format(year, month, last_day)
                query = "SELECT distinct id,count(id),datetime_val,sum(value) FROM sensor_data where datetime_val BETWEEN '{}' and '{}' GROUP BY strftime('%d', datetime_val) Order by datetime_val desc".format(start_date, end_date)
                if is_pdf:
                    total, maxi, mini = query_for_pdf_data(start_date, end_date, operator="d")
            elif pick_val == 'custom':
                if f1 and f2:
                    print('datetime value custom called', f1,'------',f2)
                    start_date = '{} 00:00:00'.format(f1)
                    end_date = '{} 23:59:59'.format(f2)
                    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
                    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')

                    days = end_date - start_date
                    if days.days != 0:
                        operator = "d"
                    else:
                        operator = "H"

                    print('------------->',start_date, end_date, operator)

                    query = "SELECT distinct id,count(id),datetime_val,sum(value) FROM sensor_data where datetime_val BETWEEN '{}' and '{}' GROUP BY strftime('%{}', datetime_val) Order by datetime_val desc".format(
                        start_date, end_date, operator)
                    print('this is query', query)
                    # if is_pdf:
                    #         total,maxi,mini = query_for_pdf_data(start_date,end_date,operator = operator)

            conn = sqlite3.connect('krohne_ak.db')
            cursor = conn.cursor()
            if is_pdf:
                print('is_pdf method called')
                cursor.execute(total)
                pdf_data_flow_result = cursor.fetchall()
                cursor.execute(maxi)
                max_time_query = cursor.fetchall()
                cursor.execute(mini)
                min_time_query = cursor.fetchall()
                return pdf_data_flow_result, max_time_query, min_time_query
            cursor.execute(query)
            result = cursor.fetchall()
            print('final result ', result)


            return result
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        print('date_filter_query', e)
# when user clicks on serach button this method will called


@app.route('/filter', methods=['GET', 'POST'])
def filter(is_pdf=False, f11=None, f22=None, uff=False):
    try:
        f1 = request.args.get('f1')
        f2 = request.args.get('f2')
        pick_val = request.args.get('pick_val')
        id_list = []
        flow_list = []
        time_list = []


        if pick_val != 'custom':
            rec = date_filter_query(pick_val)
            for r in rec:
                if r:
                    id_list.append(r[0])
                    flow_list.append(float(r[1] * 0.040))
                    time_list.append(str(r[2])[0:19])

        else:
            if uff == True and is_pdf == True:
                rec = date_filter_query(pick_val, f11, f22)
                print(rec, 'reccccccccccccccccccccccccccccccccccc')
                for r in rec:
                    if r:
                        id_list.append(r[0])
                        flow_list.append(float(r[1] * 0.040))
                        time_list.append(str(r[2])[0:19])
            else:
                rec = date_filter_query(pick_val, f1, f2)
                for r in rec:
                    if r:
                        id_list.append(r[0])
                        flow_list.append(float(r[1] * 0.040))
                        time_list.append(str(r[2])[0:19])

        if is_pdf:
            if rec:
                max_val = max(flow_list)
                min_val = min(flow_list)
                max_val_time = rec[flow_list.index(max_val)][2]
                min_val_time = rec[flow_list.index(min_val)][2]
                total_val = sum(flow_list)
            else:
                return False, False, False, False, False

            return max_val, max_val_time, min_val, min_val_time, total_val

        return json.dumps({"id_list": id_list, "flow_list": flow_list, "time_list": time_list})
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        print('Exception occured in filter method: ' + str(e))


@app.route('/pdf', methods=['GET', 'POST'])
def pdf_data():
    start_date = None
    end_date = None
    footer_data = {}
    try:
        pick_val = request.args.get('pick_val')
        if pick_val == 'custom':
            f1 = request.args.get('f1')
            f2 = request.args.get('f2')
            footer_data['f1'] = f1
            footer_data['f2'] = f2
            start_date = '{} 00:00:00'.format(f1)
            end_date = '{} 23:59:59'.format(f2)
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')

            days = end_date - start_date
            if days.days != 0:
                operator = "d"
            else:
                operator = "H"
            if operator == "H":
                max_val, max_val_time, min_val, min_val_time, total_val = filter(is_pdf=True)
                min_time_val = [(min_val_time, min_val)]
                max_time_val = [(max_val_time, max_val)]
                total = [(total_val,)]
            else:
                min_time_val = []
                max_time_val = []
                total = []

                for i in range(int(f1[-2:]), int(f2[-2:]) + 1):
                    max_val, max_val_time, min_val, min_val_time, total_val = filter(is_pdf=True, f11=f1[:-2] + str(i), f22=f1[:-2] + str(i), uff=True)
                    if False in (max_val,max_time_val,min_time_val,min_val,total_val):
                        continue
                    else:
                        min_time_val.append((min_val_time, min_val,))
                        max_time_val.append((max_val_time, max_val,))
                        total.append((total_val,))
                    

            footer_data['pick_val'] = pick_val
        elif pick_val == 'today':
            footer_data['pick_val'] = pick_val
            max_val, max_val_time, min_val, min_val_time, total_val = filter(is_pdf=True)
            min_time_val = [(min_val_time, min_val)]
            max_time_val = [(max_val_time, max_val)]
            total = [(total_val,)]
        else:
            total, max_time_val, min_time_val = date_filter_query(pick_val, is_pdf=True)


        # print('---pdf_data_flow_result--------', pdf_data_flow_result)
        # print('-----max_time_query_result---------', max_time_query_result)
        # print('-----min_time_query_result-------', min_time_query_result)

        # max_val_output = []
        # min_val_output = []

        # for i in max_time_query_result:
        #     if None in i:
        #         continue
        #     max_val_output.append(list(i))

        # for j in min_time_query_result:
        #     if None in j:
        #         continue
        #     min_val_output.append(list(i))

        # print(min_val_output)
        # print(max_val_output)

##############################################################
        pdf_data_len = 30
        pdf = CustomPDF('P', 'mm', 'A4')
        pdf.add_page('P')
        pdf.set_margins(20, 60, 20)  # 25, 70, 10
        pdf.set_font("Arial", size=8)
        pdf.ln(25)
        col_width = pdf.w / 4.5
        row_height = pdf.font_size
        # pdf_data_len = len(pdf_data_flow_result)
        start_point = 0
        end_point = 30
        last_page = math.ceil(pdf_data_len / 30)
        footer_data['last_page'] = last_page
        pdf.footer_data = footer_data

        if True:
            try:
                pdf.set_font("Arial", size=8)
                print('download PDF method called')
                # adding database records to a pdf_data_list

                # creating 'waste_water_report.pdf' file
                if str(path.exists('waste_water_report.pdf')) == 'True':
                    os.remove("waste_water_report.pdf")
                else:
                    open('waste_water_report.pdf', 'a').close()

                first_row = ['Date', 'Maximum in day', 'Minimum in day', 'Total in day (m³)']
                fc = 0
                for item in first_row:
                    if fc == 0:
                        pdf.cell(pdf.w / 7, row_height * 2, txt=item, border=1)
                    else:
                        pdf.cell(col_width, row_height * 2, txt=item, border=1)
                    fc += 1

                pdf_data_list = [['', 'Time', 'Flow (m³)', 'Time', 'Flow (m³)', '', 'Flow (m³)']]

                total_flow_sum = 0

                for i in range(0, len(total)):
                    pdf_data_list.append([max_time_val[i][0][0:10], max_time_val[i][0][10:19], "{0:.2f}".format(max_time_val[i][1]), min_time_val[i][0][10:19], "{0:.2f}".format(min_time_val[i][1]), "Total", "{0:.2f}".format(total[i][0])])

                # res=filter(is_pdf = True)
                # print(res,'================')
                # total_flow_sum += (res[1] * 0.040)
                # max_val, max_val_time, min_val, min_val_time,total_val
                # pdf_data_list.append([str(res[1])[0:10],str(res[1])[10:19],str("{0:.2f}".format(res[0])),str(res[3])[10:19],str("{0:.2f}".format(res[2])),"Total",str("{0:.2f}".format(res[4]))])
                pdf.ln(row_height * 2)
                footer_data['total_flow_sum'] = 100
                # print('pdf_data_list -----------------', pdf_data_list, len(pdf_data_list))

                c = 0

                while pdf_data_len > 0:
                    for items in pdf_data_list[start_point:end_point]:
                        for i in items:
                            if c == 0:
                                pdf.cell(pdf.w / 7, row_height * 2, txt=i, border=1)
                            else:
                                pdf.cell(col_width / 2.0, row_height * 2, txt=i, border=1)
                            c += 1
                            if c == 7:
                                c = 0
                        pdf.ln(row_height * 2)
                    start_point += 30
                    end_point += 30
                    pdf_data_len -= 30
                    pdf.ln(70)

                pdf.output("waste_water_report.pdf")
                print('PDF successfully downloaded!!')
                return '200'
            except Exception as e:
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
                print('Exception occured in download_pdf method: ' + str(e))
                return('Exception occured in download_pdf method: ' + str(e))

        else:
            print('No data availabe for selected')
            pdf.set_font("Arial", size=20)
            text = 'No Data availabe for the select date range'
            pdf.write(30, text)
            pdf.output("waste_water_report.pdf")
            return 'No Data'
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        print('Exception occured in pdf_data method: ' + str(e))


@app.route('/pdf_save')
def pdf_save():
    return send_file("waste_water_report.pdf", mimetype="application/pdf", as_attachment=True, cache_timeout=-1)


class CustomPDF(FPDF):

    def header(self):
        pass
        self.image('static/img/water-2.png', 14, 8, 20)
        self.image('static/img/text-1.png', 39, 18, 70)
        self.image('static/img/text-2.png', 154, 18, 30)

    def footer(self):
        self.set_y(-50)
        footer_data = self.footer_data
        if self.page_no() == footer_data['last_page']:
            import datetime
            from dateutil.relativedelta import relativedelta
            current_time = datetime.datetime.now()
            curr_day = current_time.day
            curr_hour = current_time.hour
            curr_month = datetime.date.today().month
            curr_year = datetime.date.today().year
            start_date = datetime.datetime.now() - datetime.timedelta(days=(curr_day - 1))
            if footer_data['pick_val'] == 'custom':
                start_date = footer_data['f1']
                end_date = footer_data['f2']

            elif str(footer_data['pick_val']) == 'today':
                start_date = str(current_time)[0:10] + ' 00:00:00'
                end_date = '{} {}:59:59'.format(str(current_time)[0:10], str(curr_hour - 1))

            elif str(footer_data['pick_val']) == 'week':
                start_date = datetime.datetime.now() - datetime.timedelta(days=7)
                end_date = datetime.datetime.now() - datetime.timedelta(days=1)
                start_date = str(start_date)[0:10] + ' 00:00:00'
                end_date = '{} {}:59:59'.format(str(end_date)[0:10], str(curr_hour - 1))

            elif str(footer_data['pick_val']) == 'month':
                if curr_month == 1:
                    curr_month = 12
                    curr_year -= 1
                else:
                    curr_month -= 1
                if curr_month in list(range(1, 10)):
                    curr_month = '{}{}'.format(0, curr_month)
                    start_date = '{}-{}-01 00:00:00'.format(curr_year, curr_month)
                    end_date = '{}-{}-{} 23:59:59'.format(curr_year, curr_month, curr_day - 1)

            elif str(footer_data['pick_val']) == 'last_month':
                import calendar
                month = datetime.date.today().month
                year = datetime.date.today().year
                if month == 1:
                    month = 12
                    year -= 1
                else:
                    month -= 1
                    if month in list(range(1, 10)):
                        month = '{}{}'.format(0, month)
                    last_day = calendar.monthrange(year, int(month))[1]
                    start_date = '{}-{}-01 00:00:00'.format(year, month)
                    end_date = '{}-{}-{} 23:59:59'.format(year, month, last_day)
            self.cell(0, 5, 'The total flow is ' + str(footer_data.get('total_flow_sum', 0)) + ' m³ ' + 'between ' + str(start_date) + ' and ' + str(end_date) + '.', border=0, ln=1, align='C')
            self.cell(0, 5, 'This report is prepared by a measurement with KROHNE Electromagnetic-Flow-Meter.( CTM Module - Controling-Tracking-Monitoring )', border=0, ln=2)
            self.image('/home/pi/Desktop/26_final/static/img/text-3.png', 35, 260, 130)


@app.route('/send_email', methods=['GET', 'POST'])
def send_email():
    try:
        subject = "Waste-water report for Aknişasta Company"
        recipients = MAIL_RECEPIENTS  # user_email
        body = 'Hello, AK NİŞASTA SAN. VE TİC.A.Ş.'
        msg = Message(subject=subject, sender=MAIL_SENDER, recipients=recipients)
        msg.body = body
        with app.open_resource("waste_water_report.pdf") as fp:
            msg.attach("waste_water_report.pdf", "application/pdf", fp.read())
        mail.send(msg)
        return '200'  # 200 response will send an email
    except socket.gaierror as e:
        print(type(e))
        return '400'  # 400 response states that there is no internet
    except Exception as e:
        print(type(e))
        return 'error'  # This will raise an alert to the user to try again


def download_file():
    try:
        import calendar
        import datetime
        month = 8  # datetime.date.today().month
        year = 2019  # datetime.date.today().year
        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1
        if month in list(range(1, 10)):
            month = '{}{}'.format(0, month)
        last_day = calendar.monthrange(year, int(month))[1]
        start_date = '{}-{}-01 00:00:00'.format(year, month)
        end_date = '{}-{}-{} 23:59:59'.format(year, month, last_day)
        conn = sqlite3.connect('krohne_ak.db')
        cursor = conn.cursor()
        query = "SELECT * FROM sensor_data where datetime_val BETWEEN '{}' and '{}'".format(start_date, end_date)
        cursor.execute(query)
        result = cursor.fetchall()
        dataFrame = {'Id': [], 'Value': [], 'Date': []}
        for row in cursor.execute(query):

            dataFrame['Id'].append(row[0])
            dataFrame['Value'].append(row[1])
            dataFrame['Date'].append(row[2])

        sheet_name = datetime.datetime.now().strftime('%B - %Y')
        dataExport = pd.DataFrame(dataFrame)
        dataToExcel = pd.ExcelWriter('Monthly-Reporting/{}.xlsx'.format(sheet_name), engine='xlsxwriter')
        dataExport.to_excel(dataToExcel, sheet_name=sheet_name, columns=['Id', 'Value', 'Date'])
        dataToExcel.save()
        print('written data successfully')
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        print('Exception occured in download_file method: ' + str(e))


@app.route('/reset_data', methods=['GET', 'POST'])
def reset_data():
    try:
        conn = sqlite3.connect('krohne_ak.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sensor_data')
        conn.commit()
        global count
        count = 0
        print('data resetted')
        return '200'
    except Exception as e:
        print('Exception while resetting data ', str(e))
        return '400'
if __name__ == '__main__':
    thread = Thread(target=flow_recording)
    thread.daemon = True
    thread.start()
    scheduler = BackgroundScheduler()
    scheduler.add_job(download_file, 'cron', month='1-12', day=30, hour=9, minute=22)
    scheduler.start()
    # app.run(debug=True)

    app.run(host='192.168.2.174', port='5060')
    # app.run(host='192.168.2.103',port='4444')
    # app.run(host='169.254.224.240',port='4444')


# SELECT distinct count(id)*0.040,datetime_val,max(value)*0.040, min(value)*0.040,sum(value)*0.040 FROM sensor_data where datetime_val BETWEEN '2019-10-10 00:00:00' and '2019-10-10 23:59:59' GROUP BY strftime('%d', datetime_val) Order by datetime_val desc
