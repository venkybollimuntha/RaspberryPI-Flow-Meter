from flask import Flask, render_template ,jsonify,json,request,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import update
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
import csv
from fpdf import FPDF 
from flask_login import UserMixin, LoginManager, current_user, login_user, logout_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import pandas as pd  
import xlsxwriter 
import sqlite3
import asyncio
import RPi.GPIO as GPIO
import time
import json
from threading import *
import sys
import psycopg2
import datetime

FLOW_SENSOR_KROHNE = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(FLOW_SENSOR_KROHNE, GPIO.IN, pull_up_down=GPIO.PUD_UP)


loop = asyncio.get_event_loop()
count = 0


conn = sqlite3.connect('samet.db')
print('DB Opened')
conn.execute("CREATE TABLE IF NOT EXISTS sensor_data ( id INTEGER PRIMARY KEY AUTOINCREMENT, value REAL, datetime_val TEXT )")
conn.execute("CREATE TABLE IF NOT EXISTS user_auth ( id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password VARCHAR(50),dob TEXT,email VARCHAR(50),role VARCHAR(30),user_created_date TEXT)")
conn.commit()
print('Yes table exists')

async def send_req(flow_val,count):
    conn = sqlite3.connect('samet.db')
    conn.execute("INSERT INTO sensor_data (value,datetime_val) VALUES ('{}','{}')".format(flow_val,str(datetime.datetime.now())))
    conn.commit()
    print('record inserted',count)
   
def countPulse(channel):
    try:
        global count
        count = count + 1
        #print(count) # that is not referance to see our count. 1 more overloop
        flow_val = count * 0.01  # we need to change this value??? it is ok
        task_set = loop.create_task(send_req(flow_val,count))
        #print(count)
        
    except (Exception, psycopg2.Error) as error:
        print('Exception occured while inserting data into database: ' + str(error))

   
   
GPIO.add_event_detect(FLOW_SENSOR_KROHNE, GPIO.FALLING, callback=countPulse)


# This file is called through threading module
def samet():
    while True:
        task_list = asyncio.Task.all_tasks()
        if task_list:
            for i in task_list:
                loop.run_until_complete(i)
                i.cancel()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///samet.db'
app.secret_key = 'XP)(OIUip08u7yhg8'

db = SQLAlchemy(app)
db.Model.metadata.reflect(db.engine)
login = LoginManager(app)


# Flask-Login keeps track of the logged in user by storing its unique identifier in Flask's user session
# Each time the logged-in user navigates to a new page, it retrieves the ID of the user from the session, and then loads that user into memory.
@login.user_loader
def load_user(user_id):
    return user_auth.query.get(user_id)

class user_auth(db.Model,UserMixin):
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(50))
    dob = db.Column(db.String(50))
    email = db.Column(db.String(50))
    role = db.Column(db.String(50))

class MyModelView(ModelView):
    def is_accessible(self):
        user = user_auth.query.get(current_user.get_id())
        print(user.username)
        roles_list = ['SuperAdmin', ]
        print(user.role)
        if current_user.is_authenticated and user.role in roles_list:
            return True # if True table is visible in Admin page
        else:
            return False # if False table is not visible in Admin page

admin = Admin(app, name='RPI')
admin.add_view(MyModelView(user_auth, db.session))

@app.route('/',methods=['GET','POST'])
def landing_page():
    data = {}
    if current_user.is_authenticated:
        user = user_auth.query.get(current_user.get_id())
        data['role'] = user.role
        data['role_list'] = ['SuperAdmin', 'Engineer','Manager']
        data['user'] = current_user.is_authenticated
        return render_template('index.html', data = data)
    else:
        return render_template('login.html', data = data)

@app.route('/login',methods = ['POST', 'GET'])
def login():
    data = {}
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(username,password)
        user = user_auth.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                print(str(username)+' : successfully logged in!!')
                return redirect(url_for('landing_page'))
            else:
                data['msg'] = 'Incorrect username or password'
                return render_template('login.html',data = data)
        else:
            data['msg'] = 'Incorrect username or password'
            return render_template('login.html',data = data)


@app.route('/register',methods = ['POST', 'GET'])
def register():
    data= {}
    return render_template('signup.html',data = data)


@app.route('/signup',methods = ['POST', 'GET'])
def signup():
    data = {}
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        dob = request.form['dob']
        print(username,password, email)
        user = user_auth.query.filter_by(email=email).first()
        if not user:
            print(str(username)+' : does not exist!!')
            new_user = user_auth(email=email, username=username, password=generate_password_hash(password, method='sha256'),dob=dob)
            db.session.add(new_user)
            db.session.commit()
            print(str(username)+' : successfully created!!')
            return redirect(url_for('landing_page'))
        else:
            print(str(email)+' : already exist!!')
            data['msg'] = 'Email already exist!! Please try with new one'
            return render_template('signup.html',data = data)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('landing_page'))

@app.route("/forgot")
def forgot():
    data= {}
    return render_template('reset.html',data = data)

@app.route("/reset", methods=['GET','POST'])
def reset():
    first = request.args.get('first')
    username = request.args.get('username') if request.args.get('username') else '' 
    dob = request.args.get('dob') if request.args.get('dob') else ''
    second = request.args.get('second')
    data= {}
    if request.method == 'GET' and first == 'true':

        user = user_auth.query.filter_by(username=username,dob = dob).first()
        print(user,dob,username)
        if user:
            data['is_success'] = True
            data['username']=username
            print('is_success')
            return render_template('reset.html', data = data)
        else:
            data['is_success'] = False
            data['msg'] = 'incorrect username/DOB, please try again.'
            data['username']=username
            print('not is_success')
            return render_template('reset.html',data=data)

    elif request.method == 'GET' and second == 'true':
        password = request.args.get('password')
        print('password-------------------',password)
        print('username-------------------',username)
        if username:
            user=user_auth.query.filter(user_auth.username==username).first()
            user.password = generate_password_hash(password, method='sha256')
            db.session.commit()
            print('updated successfully')
            return redirect(url_for('landing_page'))
 
    return redirect(url_for('landing_page'))

# live endpoint 
@app.route('/live', methods=['GET', 'POST'])
def live():
    conn = sqlite3.connect('samet.db')
    cursor = conn.cursor()
    d = 'SELECT * FROM sensor_data order by id desc limit 1'
    print(d)
    cursor.execute(d)
    rec= cursor.fetchall()
    for r in rec:
        print(r)
        if r:
            flow = r[1]
            time = str(r[2])

    return json.dumps({"flow":flow,"time":time})

# Internal query method 
def date_filter_query(pick_val,f1=None,f2=None):
    try:
        import datetime
        from dateutil.relativedelta import relativedelta
        current_time = datetime.datetime.utcnow()
        curr_day = current_time.day
        curr_hour = current_time.hour
        curr_month = datetime.date.today().month 
        curr_year = datetime.date.today().year
        start_date = datetime.datetime.utcnow() - datetime.timedelta(days=(curr_day - 1))
        if pick_val:
            if pick_val == 'today':# not to worry lemee check it
                start_date = str(current_time)[0:10] + ' 00:00:00'
                end_date = '{} {}:59:59'.format(str(current_time)[0:10],str(curr_hour - 1))
                query = "SELECT distinct id,AVG(value),datetime_val FROM sensor_data where datetime_val BETWEEN '{}' and '{}' GROUP BY strftime('%H', datetime_val)".format(start_date,end_date)

            elif pick_val == 'week':
                start_date = datetime.datetime.utcnow() - datetime.timedelta(days=7)
                end_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
                start_date = str(start_date)[0:10] + ' 00:00:00'
                end_date = '{} {}:59:59'.format(str(end_date)[0:10],str(curr_hour - 1))
                query = "SELECT distinct id,AVG(value),datetime_val FROM sensor_data where datetime_val BETWEEN '{}' and '{}' GROUP BY strftime('%d', datetime_val)".format(start_date,end_date)

            elif pick_val == 'month':

                if curr_month == 1:
                    curr_month = 12
                    curr_year -=1 
                else:
                    curr_month -= 1
                if curr_month in list(range(1,10)):
                    curr_month= '{}{}'.format(0,curr_month)

                start_date =  '{}-{}-01 00:00:00'.format(curr_year,curr_month)
                end_date = '{}-{}-{} 23:59:59'.format(curr_year,curr_month,curr_day - 1)
                query = "SELECT distinct id,AVG(value),datetime_val FROM sensor_data where datetime_val BETWEEN '{}' and '{}' GROUP BY strftime('%d', datetime_val)".format(start_date,end_date)

            elif pick_val == 'last_month':
                import calendar
                month = datetime.date.today().month 
                year = datetime.date.today().year
                if month == 1:
                    month = 12
                    year -=1 
                else:
                    month -= 1
                if month in list(range(1,10)):
                    month= '{}{}'.format(0,month)

                last_day = calendar.monthrange(year,int(month))[1]
                start_date = '{}-{}-01 00:00:00'.format(year,month)
                end_date = '{}-{}-{} 23:59:59'.format(year,month,last_day)
                query = "SELECT distinct id,AVG(value),datetime_val FROM sensor_data where datetime_val BETWEEN '{}' and '{}' GROUP BY strftime('%d', datetime_val)".format(start_date,end_date)

            elif pick_val == 'custom':
                if f1 and f2:
                    print(f1,'   00000000000000000  ',f2)
                    start_date =  '{} 00:00:00'.format(f1)
                    end_date = '{} 23:59:59'.format(f2)
                    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
                    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')

                    days = end_date - start_date
                    print(days.days,'------------------------------------')

                    if days.days != 0 :
                        operator = "d"
                    else:
                        operator = "H"

                    query = "SELECT distinct id,AVG(value),datetime_val FROM sensor_data where datetime_val BETWEEN '{}' and '{}' GROUP BY strftime('%{}', datetime_val)".format(start_date,end_date,operator)
                  
            conn = sqlite3.connect('samet.db')
            cursor = conn.cursor()
            print(query)
            cursor.execute(query)
            result = cursor.fetchall()
            return result
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        # else:
        #     if selected_day:
        #         choosed_date = (start_date + datetime.timedelta(days=int(selected_day) - 1))

        #         conn = sqlite3.connect('samet.db')
        #         cursor = conn.cursor()
        #         start_date = str(choosed_date)[0:10] + ' 00:00:00'
        #         end_date = str(choosed_date)[0:10] + ' 23:59:59'
        #         query = f"SELECT distinct id,AVG(value),datetime_val FROM sensor_data where datetime_val BETWEEN '{start_date}' and '{end_date}' GROUP BY strftime('%H', datetime_val);"
        #         cursor.execute(query)
        #         result = cursor.fetchall()



# when user clicks on serach button this method will called
@app.route('/filter', methods=['GET', 'POST'])
def filter():
    f1=request.args.get('f1')
    f2=request.args.get('f2')
    pick_val = request.args.get('pick_val')
    if pick_val != 'custom':
    # print('--------------------------------',f1,f2)
        rec = date_filter_query(pick_val)
        id_list =[]
        flow_list =[]
        time_list =[]
        for r in rec:
            if r:
                id_list.append(r[0])
                flow_list.append(float(r[1]))
                time_list.append(str(r[2]))

        return json.dumps({"id_list":id_list,"flow_list":flow_list,"time_list":time_list})

    else:
        rec = date_filter_query(pick_val,f1,f2)
 
        id_list= []
        flow_list =[]
        time_list =[]
        for r in rec:
            if r:
                id_list.append(r[0])
                flow_list.append(float(r[1]))
                time_list.append(str(r[2]))

        return json.dumps({"id_list":id_list,"flow_list":flow_list,"time_list":time_list})



# @app.route('/pdf', methods=['GET','POST'])
# def pdf_data():
#     f1=request.args.get('f1')
#     f2=request.args.get('f2')
#     result = date_filter_query(f1,f2)

#     print(',,----------------,,',result)
#     get_pdf = True if request.args.get('get_pdf') == 'true' else False
#     send_mail = True if request.args.get('send_mail') == 'true' else False
#     print('get_pdf',get_pdf,'send_mail',send_mail)

#     if get_pdf:
#         download_pdf(result)

#     if send_mail:
#         mail_pdf()
#     return 'called'

# # When user click on the download button this method is called
# def download_pdf():
#     try:
#         print('download PDF method called')
#         # adding database records to a pdf_data_list
#         pdf_data_list = [['ID', 'Flow Rate', 'Timestamp']]
#         for rec in data_list:
#             res = list(rec)
#             pdf_data_list.append(res)

#         # adding data to PDF file
#         pdf = FPDF()
#         pdf.add_page()
#         pdf.set_font("Arial", size=10)
#         col_width = pdf.w / 4.0
#         row_height = pdf.font_size
#         for row in pdf_data_list:
#             for item in row:
#                 pdf.cell(col_width, row_height*2,txt=item, border=1)
#             pdf.ln(row_height*2)
#         pdf.output("simple_demo.pdf")
#     except Exception as e:
#         print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
#         print('Exception occured in download_pdf method: '+str(e))
#         return('Exception occured in download_pdf method: '+str(e)) 


# sending attachment as pdf to the user
# def mail_pdf():
#     try:
#         receiver_email = ["venkybollimuntha@gmail.com"]
#         sender_email = "doubts2venky@gmail.com"
#         password = 'bhagi@956'
#         mail_body = 'Please find the below attached file'
#         subject = 'We added PDF as a attachment'
#         msg = Message(subject=subject,sender=sender_email,recipients=receiver_email)
#         msg.body = mail_body
#         with app.open_resource("simple_demo.pdf",'rb') as fp:
#             msg.attach("simple_demo.pdf","application/pdf", fp.read())
#         mail.send(msg)
#         print('Maiil sent successfully')
#     except Exception as e:
#         print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
#         print('Exception occured in mail_pdf method: '+str(e))
#         return('Exception occured in mail_pdf method: '+str(e))



def download_file():
    print('called')
    import calendar
    import datetime
    month = 8#datetime.date.today().month 
    year = 2019#datetime.date.today().year
    if month == 1:
        month = 12
        year -=1 
    else:
        month -= 1
    if month in list(range(1,10)):
        month= '{}{}'.format(0,month)

    last_day = calendar.monthrange(year,int(month))[1]
    start_date = '{}-{}-01 00:00:00'.format(year,month)
    end_date = '{}-{}-{} 23:59:59'.format(year,month,last_day)
    conn = sqlite3.connect('samet.db')
    cursor = conn.cursor()
    query = "SELECT * FROM sensor_data where datetime_val BETWEEN '{}' and '{}'".format(start_date,end_date)
    cursor.execute(query)
    result = cursor.fetchall()
    #print(result)
    dataFrame = {'Id': [], 'Value': [], 'Date': []}
    
    for row in cursor.execute(query):

        dataFrame['Id'].append(row[0])
        dataFrame['Value'].append(row[1])
        dataFrame['Date'].append(row[2])
    
    sheet_name = datetime.datetime.utcnow().strftime('%B - %Y') 
    dataExport = pd.DataFrame(dataFrame)
    dataToExcel = pd.ExcelWriter('{}.xlsx'.format(sheet_name), engine='xlsxwriter')
    dataExport.to_excel(dataToExcel, sheet_name=sheet_name, columns=['Id', 'Value', 'Date'])
    dataToExcel.save()
    print('written data successfully')


    


if __name__ == '__main__':
    thread = Thread(target = samet)
    thread.daemon = True
    thread.start()
    # scheduler = BackgroundScheduler()
    # scheduler.add_job(download_file, 'cron', month='1-12', day=24, hour=18,minute=45)
    # scheduler.start()
    app.run(port='7866')

