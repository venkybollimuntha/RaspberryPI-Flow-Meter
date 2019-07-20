from flask import Flask, render_template ,jsonify,json,request,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import psycopg2
import datetime
from fpdf import FPDF
# import email, smtplib, ssl
# from flask_mail import Mail, Message
# from email import encoders
# from email.mime.base import MIMEBase
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
import sys

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rpi.db'
app.secret_key = 'XAB5665RTsdfsde4545'

db = SQLAlchemy(app)
db.Model.metadata.reflect(db.engine)
login = LoginManager(app)

# Flask-Login keeps track of the logged in user by storing its unique identifier in Flask's user session
# Each time the logged-in user navigates to a new page, it retrieves the ID of the user from the session, and then loads that user into memory.
@login.user_loader
def load_user(user_id):
	return User.query.get(user_id)

class User(db.Model,UserMixin):
	__table_args__ = {'extend_existing': True}

	id = db.Column(db.Integer, primary_key = True)
	username = db.Column(db.String(50))
	password = db.Column(db.String(50))
	email = db.Column(db.String(50))
	role = db.Column(db.String(50))

class MyModelView(ModelView):
	def is_accessible(self):
		user = User.query.get(current_user.get_id())
		roles_list = ['SuperAdmin', 'Engineer', 'Manager']
		if current_user.is_authenticated and user.role in roles_list:
			return True # if True table is visible in Admin page
		else:
			return False # if False table is not visible in Admin page

admin = Admin(app, name='RPI')
admin.add_view(MyModelView(User, db.session))


@app.route('/login',methods = ['POST', 'GET'])
def login():
	data = {}
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		print(username,password)
		user = User.query.filter_by(username=username).first()
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
		print(username,password, email)
		user = User.query.filter_by(email=email).first()
		if not user:
			print(str(username)+' : does not exist!!')
			new_user = User(email=email, username=username, password=generate_password_hash(password, method='sha256'))
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

conn = psycopg2.connect(user="ogpjmzmjumdfbt", password="8df63f5dd3ec150eab2a60c4ba250606b19cdb2bdf240b1c91c18cc3df52fe75", host="ec2-54-247-81-88.eu-west-1.compute.amazonaws.com", port="5432", database="d5crgts94o7lje")
cursor = conn.cursor()


@app.route('/',methods=['GET','POST'])
def landing_page():
	data = {}
	if current_user.is_authenticated:
		user = User.query.get(current_user.get_id())
		data['role'] = user.role
		data['role_list'] = ['SuperAdmin', 'Engineer','Manager']
		return render_template('index.html', data = data)
	else:
		return render_template('login.html', data = data)

# live endpoint 
@app.route('/live', methods=['GET', 'POST'])
def live():
    cursor.execute('SELECT * FROM public.flow_meter order by id desc limit 1')
    rec = cursor.fetchall()
    for r in rec:
        print(r)
        if r:
            flow = r[1]
            time = str(r[2])

    return json.dumps({"flow":flow,"time":time})

# Internal query method 
def date_filter_query(f1,f2):
    query = f"SELECT id::text, flow_rate::text, timestamp::text FROM public.flow_meter where timestamp between '{f1.replace('T', ' ')}' and '{f2.replace('T', ' ')}' order by id desc limit 10"
    cursor.execute(query)
    result= cursor.fetchall()
    # print('----------------',result)

    return result

# when user clicks on serach button this method will called
@app.route('/filter', methods=['GET', 'POST'])
def filter():
    f1=request.args.get('f1')
    f2=request.args.get('f2')
    # print('--------------------------------',f1,f2)
    rec = date_filter_query(f1,f2)    
    id_list =[]
    flow_list =[]
    time_list =[]
    for r in rec:
        if r:
            id_list.append(r[0])
            flow_list.append(float(r[1]))
            time_list.append(str(r[2]))


    return json.dumps({"id_list":id_list,"flow_list":flow_list,"time_list":time_list})


@app.route('/pdf', methods=['GET','POST'])
def pdf_data():
    f1=request.args.get('f1')
    f2=request.args.get('f2')
    result = date_filter_query(f1,f2)

    print(',,----------------,,',result)
    get_pdf = True if request.args.get('get_pdf') == 'true' else False
    send_mail = True if request.args.get('send_mail') == 'true' else False
    print('get_pdf',get_pdf,'send_mail',send_mail)

    if get_pdf:
        download_pdf(result)

    if send_mail:
        mail_pdf()
    return 'called'

# When user click on the download button this method is called
def download_pdf(data_list):
    try:
        print('download PDF method called')
        # adding database records to a pdf_data_list
        pdf_data_list = [['ID', 'Flow Rate', 'Timestamp']]
        for rec in data_list:
            res = list(rec)
            pdf_data_list.append(res)

        # adding data to PDF file
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        col_width = pdf.w / 4.0
        row_height = pdf.font_size
        for row in pdf_data_list:
            for item in row:
                pdf.cell(col_width, row_height*2,txt=item, border=1)
            pdf.ln(row_height*2)
        pdf.output("simple_demo.pdf")
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        print('Exception occured in download_pdf method: '+str(e))
        return('Exception occured in download_pdf method: '+str(e)) 


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





if __name__ == '__main__':
   app.run(debug = True)