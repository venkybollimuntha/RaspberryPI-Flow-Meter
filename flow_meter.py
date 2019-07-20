from flask import Flask, request,render_template, jsonify,json
import psycopg2
import datetime
import sqlite3
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


@app.route('/',methods=['GET','POST'])
def landing_page():
    return render_template('index.html')

# live endpoint 
@app.route('/live', methods=['GET', 'POST'])
def live():
    conn = sqlite3.connect('flow_meter1.db')
    cursor = conn.cursor()
    d = 'SELECT * FROM flow_meter_example order by id desc limit 1'
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

        conn = sqlite3.connect('flow_meter1.db')
        cursor = conn.cursor()
        query = f"SELECT distinct id,AVG(value),datetime_val FROM flow_meter_example where datetime_val BETWEEN '{start_date}' and '{end_date}' GROUP BY strftime('%d', datetime_val);"
        print(query)
        cursor.execute(query)
        result = cursor.fetchall()
    else:
        if selected_day:
            choosed_date = (start_date + datetime.timedelta(days=int(selected_day) - 1))

            conn = sqlite3.connect('flow_meter1.db')
            cursor = conn.cursor()
            start_date = str(choosed_date)[0:10] + ' 00:00:00'
            end_date = str(choosed_date)[0:10] + ' 23:59:59'
            query = f"SELECT distinct id,AVG(value),datetime_val FROM flow_meter_example where datetime_val BETWEEN '{start_date}' and '{end_date}' GROUP BY strftime('%H', datetime_val);"
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
def mail_pdf():
    try:
        receiver_email = ["venkybollimuntha@gmail.com"]
        sender_email = "doubts2venky@gmail.com"
        password = 'bhagi@956'
        mail_body = 'Please find the below attached file'
        subject = 'We added PDF as a attachment'
        msg = Message(subject=subject,sender=sender_email,recipients=receiver_email)
        msg.body = mail_body
        with app.open_resource("simple_demo.pdf",'rb') as fp:
            msg.attach("simple_demo.pdf","application/pdf", fp.read())
        mail.send(msg)
        print('Maiil sent successfully')
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
        print('Exception occured in mail_pdf method: '+str(e))
        return('Exception occured in mail_pdf method: '+str(e))


if __name__ == '__main__':
    app.run(debug=True)
