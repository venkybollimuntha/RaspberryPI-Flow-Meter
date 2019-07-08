import RPi.GPIO as GPIO
import time
import sys
import psycopg2
import asyncio
FLOW_SENSOR_KROHNE = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(FLOW_SENSOR_KROHNE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
global count_pulses
count = 0
conn = psycopg2.connect(user="ogpjmzmjumdfbt", password="8df63f5dd3ec150eab2a60c4ba250606b19cdb2bdf240b1c91c18cc3df52fe75", host="ec2-54-247-81-88.eu-west-1.compute.amazonaws.com", port="5432", database="d5crgts94o7lje")
cursor = conn.cursor()
loop = asyncio.get_event_loop()


async def send_req(flow_val,count):
    cursor.execute("INSERT INTO public.flow_meter(flow_rate) VALUES ({})".format(flow_val))
    conn.commit()
    print('record inserted',count)
   
def countPulse(channel):
    try:
        global count
        count = count + 1
        print(count)
        flow_val = count * 0.01  # cubicmeter, each pulse is 0.01 cubicmeter
        task = loop.create_task(send_req(flow_val,count))
    except (Exception, psycopg2.Error) as error:
        print('Exception occured while inserting data into database: ' + str(error))

   
   
GPIO.add_event_detect(FLOW_SENSOR_KROHNE, GPIO.RISING, callback=countPulse)

while True:
    #print('in while',type(asyncio.Task.all_tasks()))
    task_set = asyncio.Task.all_tasks()
    if task_set:
        for i in task_set:
            loop.run_until_complete(i)
            i.cancel()
        time.sleep(0.01)
