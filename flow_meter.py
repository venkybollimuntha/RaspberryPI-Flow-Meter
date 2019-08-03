from flask import Flask, request,render_template, jsonify,json
import psycopg2
import datetime
from fpdf import FPDF
import email, smtplib, ssl
from flask_mail import Mail, Message
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys

app = Flask(__name__)

app.config.update(
    DEBUG=False,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME='doubts2venky@gmail.com',
    MAIL_PASSWORD='bhagi@956'
)
mail = Mail(app)



conn = psycopg2.connect(user="ogpjmzmjumdfbt", password="8df63f5dd3ec150eab2a60c4ba250606b19cdb2bdf240b1c91c18cc3df52fe75", host="ec2-54-247-81-88.eu-west-1.compute.amazonaws.com", port="5432", database="d5crgts94o7lje")
cursor = conn.cursor()


@app.route('/',methods=['GET','POST'])
def landing_page():
    return render_template('index.html')


# live endpoint 
@app.route('/live', methods=['GET', 'POST'])
def live():
    cursor.execute('SELECT * FROM public.flow_meter order by id desc limit 1')
    rec = cursor.fetchall()
    if rec:
        for r in rec:
            print(r)
            if r:
                flow = r[1]
                time = str(r[2])

        return json.dumps({"flow":flow,"time":time})
    else:
        return 'No records found'

# Internal query method 
def date_filter_query(f1,f2):
    query = f"SELECT id::text, flow_rate::text, timestamp::text FROM public.flow_meter where timestamp between '{f1.replace('T', ' ')}' and '{f2.replace('T', ' ')}' order by id desc limit 10"
    cursor.execute(query)
    result = cursor.fetchall()
    return result


# when user clicks on 'Search' button this method will be called
@app.route('/filter', methods=['GET', 'POST'])
def filter():
    f1=request.args.get('f1')
    f2=request.args.get('f2')
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


#when user clicks 'Download/Send Mail' button this method will be called
@app.route('/pdf', methods=['GET','POST'])
def pdf_data():
    try:
        f1=request.args.get('f1')
        f2=request.args.get('f2')
        result = date_filter_query(f1,f2)
        get_pdf = True if request.args.get('get_pdf') == 'true' else False
        send_mail = True if request.args.get('send_mail') == 'true' else False

        if get_pdf:
            download_pdf(result)

        if send_mail:
            mail_pdf()
        return 'success'
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        print('Exception occured in pdf_data method: '+str(e))
        return('Exception occured in pdf_data method: '+str(e)) 


#this method is used to download PDF
def download_pdf(data_list):
    try:
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
            print('------------->>>>>>>>>>>>>>>>>',row,type(row))
            for item in row:
                print('--------------$$$$$$$$$$$',item,type(item))
                pdf.cell(col_width, row_height*2,txt=str(item), border=1)
            pdf.ln(row_height*2)
        pdf.output("simple_demo.pdf")
        print('PDF downloaded successfully')
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        print('Exception occured in download_pdf method: '+str(e))
        return('Exception occured in download_pdf method: '+str(e)) 

#this method is used to send PDF to mail
def mail_pdf():
    try:
        get_emails = request.args.get('receiver_email')
        email_list = get_emails.split(',')
        receiver_email=[]
        for emails in email_list:
            receiver_email.append(emails)
        print('receiver_email', receiver_email,type(receiver_email))
        sender_email = "doubts2venky@gmail.com"
        password = 'bhagi@956'
        mail_body = 'Please find the below attached file'
        subject = 'We added PDF as a attachment'
        msg = Message(subject=subject,sender=sender_email,recipients=receiver_email)
        msg.body = mail_body
        with app.open_resource("simple_demo.pdf",'rb') as fp:
            msg.attach("simple_demo.pdf","application/pdf", fp.read())
        mail.send(msg)
        print('Mail sent successfully')
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        print('Exception occured in mail_pdf method: '+str(e))
        return('Exception occured in mail_pdf method: '+str(e))


if __name__ == '__main__':
    app.run(debug=True)
