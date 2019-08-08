import RPi.GPIO as GPIO
import time
import spidev

#pe2a
#spidev setup: spi ---->>>>>> ENABLE

pe2a_GPIO_AI_CS3 = 25  #analog input SPI chip select

#definition SPI parameter
spi = spidev.SpiDev()
spi.open(0,0) 
#spi.open(0, pe2a_GPIO_AI_CS3) #hata verirse pas geçilebilir
spi.max_speed_hz = 7629

#mcp3208 ADC
def rpi_readAI(ch):
		if 7 <= ch <= 0:
			raise Exception('MCP3208 channel must be 0-7: ' + str(ch))

		cmd = 128  # 1000 0000
		cmd += 64  # 1100 0000
		cmd += ((ch & 0x07) << 3)
		ret = spi.xfer2([cmd, 0x0, 0x0])

		# get the 12b out of the return
		val = (ret[0] & 0x01) << 11  # only B11 is here
		val |= ret[1] << 3           # B10:B3
		val |= ret[2] >> 5           # MSB has B2:B0 ... need to move down to LSB

		return (val & 0x0FFF)  # ensure we are only sending 12b

#converts digital number to voltage
def rpi_dig_vol_converter(val):
	return val*33.0/4095.0

#init function
GPIO.setmode(GPIO.BCM) #bcm library
GPIO.setup(pe2a_GPIO_AI_CS3,GPIO.OUT)
GPIO.output(pe2a_GPIO_AI_CS3, GPIO.HIGH)  # AI_Pin  is DeActive
time.sleep(0.25)
GPIO.output(pe2a_GPIO_AI_CS3, GPIO.LOW)  # AI_Pin  is Active
GPIO.setwarnings(False)

AI_J13_1 = 0
AI_J13_2 = 0
AI_J13_3 = 0
AI_J13_4 = 0

def chipSelectOfAI():
    GPIO.output(pe2a_GPIO_AI_CS3, GPIO.HIGH)  # AI_Pin  is DeActive
    time.sleep(0.01)
    GPIO.output(pe2a_GPIO_AI_CS3, GPIO.LOW)  # AI_Pin  is Active
    time.sleep(0.01)
    

def fGPIOUpdate():
    #update every 10000ms
    
    #Analog Input
    chipSelectOfAI()
    AI_J13_1 = rpi_readAI(0)
    strAI = ' AI_J13_1' + "------ "+str(AI_J13_1) +' ------ '+ str(round(rpi_dig_vol_converter(AI_J13_1),2)) + ' [V]' +'\n'
    #print(strAI)
    print(round(rpi_dig_vol_converter(AI_J13_1),1))
    #chipSelectOfAI()
 
    

    
       
while 1:

    fGPIOUpdate()
    time.sleep(1)

