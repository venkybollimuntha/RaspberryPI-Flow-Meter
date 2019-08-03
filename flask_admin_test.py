from flask import Flask, render_template ,jsonify,json,request,redirect,url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import update
from flask_login import UserMixin, LoginManager, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import psycopg2
import datetime
import re
from fpdf import FPDF
import sys
import sqlite3
import csv
import pandas as pd
import xlsxwriter 

from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

conn = sqlite3.connect('flow_meter.db')
conn.execute("CREATE TABLE IF NOT EXISTS sensor_data ( id INTEGER PRIMARY KEY AUTOINCREMENT, value REAL, datetime_val TEXT )")
conn.execute("CREATE TABLE IF NOT EXISTS user_auth ( id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password VARCHAR(50),dob TEXT,email VARCHAR(50),role VARCHAR(30),user_created_date TEXT)")
conn.commit()

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flow_meter.db'
app.secret_key = 'XP)(OIUip08u7yhg8'

# app.config.update(
#     DEBUG=False,
#     MAIL_SERVER='smtp.gmail.com',
#     MAIL_PORT=465,
#     MAIL_USE_SSL=True,
#     MAIL_USERNAME='doubts2venky@gmail.com',
#     MAIL_PASSWORD='bhagi@956'
# )
# mail = Mail(app)
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
    password = db.Column(db.String(100))
    dob = db.Column(db.String(50))
    email = db.Column(db.String(50))
    role = db.Column(db.String(50))

class MyModelView(ModelView):
    def is_accessible(self):
        user = user_auth.query.get(current_user.get_id())
        roles_list = ['SuperAdmin', 'Engineer', 'Manager']
        if current_user.is_authenticated and user.role in roles_list:
            return True # if True table is visible in Admin page
        else:
            return True # if False table is not visible in Admin page

    def validate_form(self, form):
        if request.method == 'POST' and str(request.full_path).split('?')[0] == '/admin/user_auth/delete/':
            return True
        elif request.method == 'POST' and str(request.full_path).split('?')[0] == '/admin/user_auth/new/':
            if form.username.data != None and form.email.data != None:
                user = user_auth.query.filter_by(email=form.email.data, username = form.username.data).first()
                if not user:
                    print(str(form.username.data)+' : does not exist!!')
                else:
                    flash('Email/username already exist!! Please try with new one')
                    return False
            if form.password.data != None:
                form.password.data = generate_password_hash(form.password.data, method='sha256')
            if form.email.data != None:
                check_email_address = re.match('[^@]+@[^@]+\.[^@]+', form.email.data)
                if check_email_address:
                    print('Email Pattern is correct!')
                else:
                    flash('Please check the Email Address entered!')
                    return False

            if form.role.data != None and form.role.data not in ['SuperAdmin', 'Engineer','Manager']:
                flash('Please enter SuperAdmin/Engineer/Manager roles!!')
                return False            
            if form.username.data == None or form.password.data == None or form.email.data == None or form.role.data == None or form.dob.data == None:
                flash('Missing Username/Password/Email/Role/DOB fields!!')
                return False         
            return super(MyModelView, self).validate_form(form)            

admin = Admin(app, name='Saysan')
admin.add_view(MyModelView(user_auth, db.session))


# # creating superadmin account for initial use.
# cur = conn.cursor()
# cur.execute('select count(*) from user_auth')
# user = cur.fetchone()
# print('user', len(user))
# if len(user) <= 1:
#     new_user = user_auth(email='superadmin@superadmin.com', username='superadmin', password=generate_password_hash('superadmin', method='sha256'),dob='01-01-2000', role='SuperAdmin')
#     db.session.add(new_user)
#     db.session.commit()
#     print('superadmin user has been created successfully!!')    

# if 
# for u in user:
#     if 'SuperAdmin' in u:
#         print('-----------------------------*****************************************************')
#         pass
# else:
# new_user = user_auth(email='superadmin@superadmin.com', username='superadmin', password=generate_password_hash('superadmin', method='sha256'),dob='01-01-2000', role='SuperAdmin')
# db.session.add(new_user)
# db.session.commit()
#     conn.execute('select * from user_auth')
#     cursor = conn.cursor()
#     user = cursor.fetchall()
#     print('user', type(user), user)    

@app.route('/',methods=['GET','POST'])
def landing_page():
    data = {}
    if current_user.is_authenticated:
        user = user_auth.query.get(current_user.get_id())
        data['role'] = user.role
        data['role_list'] = ['SuperAdmin', 'Engineer','Manager']
        data['user'] = current_user.is_authenticated
        # all_users = user_auth.count()
        # print('all_users ---- ---  ---',all_users)
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
    conn = sqlite3.connect('flow_meter.db')
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
def date_filter_query(pick_val,selected_day =None):
    print()
    import datetime
    from dateutil.relativedelta import relativedelta
    current_time = datetime.datetime.utcnow()
    day = current_time.day
    start_date = datetime.datetime.utcnow() - datetime.timedelta(days=(day - 1))
    if pick_val and pick_val == 'Monthly':
    
        end_date = (start_date + relativedelta(months=+1)) - datetime.timedelta(days=1)
        start_date = str(start_date)[0:10] + ' 00:00:00'
        end_date = str(end_date)[0:10] + ' 23:59:59'

        conn = sqlite3.connect('flow_meter.db')
        cursor = conn.cursor()
        query = f"SELECT distinct id,AVG(value),datetime_val FROM sensor_data where datetime_val BETWEEN '{start_date}' and '{end_date}' GROUP BY strftime('%d', datetime_val);"
        print(query)
        cursor.execute(query)
        result = cursor.fetchall()
    else:
        if selected_day:
            choosed_date = (start_date + datetime.timedelta(days=int(selected_day) - 1))

            conn = sqlite3.connect('flow_meter.db')
            cursor = conn.cursor()
            start_date = str(choosed_date)[0:10] + ' 00:00:00'
            end_date = str(choosed_date)[0:10] + ' 23:59:59'
            query = f"SELECT distinct id,AVG(value),datetime_val FROM sensor_data where datetime_val BETWEEN '{start_date}' and '{end_date}' GROUP BY strftime('%H', datetime_val);"
            cursor.execute(query)
            result = cursor.fetchall()
    return result

# when user clicks on serach button this method will called
@app.route('/filter', methods=['GET', 'POST'])
def filter():
    # f1=request.args.get('f1')
    # f2=request.args.get('f2')
    pick_val = request.args.get('pick_val')
    selected_day = request.args.get('choose_day')
    if pick_val == 'Monthly':
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
        if selected_day:
            rec = date_filter_query(pick_val,selected_day)
     
            id_list= []
            flow_list =[]
            time_list =[]
            for r in rec:
                if r:
                    id_list.append(r[0])
                    flow_list.append(float(r[1]))
                    time_list.append(str(r[2]))

            return json.dumps({"id_list":id_list,"flow_list":flow_list,"time_list":time_list})


def download_file():
    print('venkybollimuntha')


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

class CustomPDF(FPDF):
 
    def header(self):
        # Set up a logo
        self.image('static/img/water-2.png', 10, 8, 20)
        self.image('static/img/text-1.png', 35, 24, 70)
        self.image('static/img/text-2.png', 150, 24, 30)
        # self.set_font('Arial', 'B', 50)
        pass
        # self.cell(100)
        # self.cell(0, 50, 'Lüleburgaz/Kırklareli', ln=1)

 
        # # Line break
        # self.ln(20)
 
    def footer(self):
        # self.cell(20)
        self.set_y(-115)
        # self.set_font('Arial', '', 10)
        # self.cell(0, 5, 'Any Town, USA', ln=1)
        page = 'no:'
        self.cell(0, 10, page, 0, 0, 'C')
        self.cell(0, 5, 'This report is prepared by base on a measurement of KROHNE mass-flow-meter at a pipe where', ln=1)
        self.cell(0, 5, 'our waste water flows. ( Error : xxx )', ln=1)
        self.image('static/img/text-3.png', 35, 200, 130)
    	# self.set_font('Arial', 'I', 50)
 
        # # Add a page number
        # page = 'Page ' + str(self.page_no()) + '/{nb}'
        # self.cell(0, 10, page, 0, 0, 'C')

# # When user click on the download button this method is called
@app.route('/test')
def download_pdf():
    try:
        print('download PDF method called')
        # adding database records to a pdf_data_list
        data_list = [[1,2,3],[4,5,6],[7,8,9],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],[10,11,12],]
        pdf_data_list = [['ID', 'Flow Rate', 'Timestamp']]
        for rec in data_list:
            res = list(rec)
            pdf_data_list.append(res)

        # adding data to PDF file
        pdf = CustomPDF('P', 'mm', 'A4')
        pdf.add_page('P')
        pdf.set_margins(25, 70, 10)
        pdf.set_font("Arial", size=10)
        pdf.ln(25)
        col_width = pdf.w / 4.0
        row_height = pdf.font_size
        pdf_data_len = len(pdf_data_list)
        # pdf_data_list_range = range(pdf_data_len)
        start_point = 0
        end_point = 10
        while pdf_data_len > 0:
            for row in pdf_data_list[start_point:end_point]:
                print('============= row ==================',row)
                for item in row:
                    # print('============= item ==================',item)
                    pdf.cell(col_width, row_height*2,txt=str(item), border=1)
                pdf.ln(row_height*2)
            print('----------------------------------------------------------------')
            pdf.output("act_doc - Copy.pdf")
            start_point += 10
            end_point += 10
            pdf_data_len -= 10
        # for row in pdf_data_list:
        #     for item in row:
        #         count+=1
        #         pdf.cell(col_width, row_height*2,txt=str(item), border=1)
    
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        print('Exception occured in download_pdf method: '+str(e))
        return('Exception occured in download_pdf method: '+str(e)) 
    return 'success'



@app.route('/db')
def db_update():
    user=user_auth.query.filter(user_auth.username=='samet').first()
    user.role='SuperAdmin'
    db.session.commit()
    print('role updated successfully!')
    return 'suces'

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
        month= f'{0}{month}'

    last_day = calendar.monthrange(year,int(month))[1]
    conn = sqlite3.connect('flow_meter.db')
    cursor = conn.cursor()
    start_date = f'{year}-{month}-01 00:00:00'
    end_date = f'{year}-{month}-{last_day} 23:59:59'
    query = f"SELECT * FROM sensor_data where datetime_val BETWEEN '{start_date}' and '{end_date}'"
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
    dataToExcel = pd.ExcelWriter(f'{sheet_name}.xlsx', engine='xlsxwriter')
    dataExport.to_excel(dataToExcel, sheet_name=sheet_name, columns=['Id', 'Value', 'Date'])
    dataToExcel.save()
    print('written data successfully')


def v():
    print('sdfghjsdfghjdfghj')


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(download_file, 'cron', month='1-12', day=24, hour=18,minute=45)
    scheduler.start()
    app.run(debug=True)
 