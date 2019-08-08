import RPi.GPIO as GPIO
import time
import spidev
import time
pe2a_GPIO_AI_CS3 = 25  #analog input SPI chip select
#definition SPI parameter
spi = spidev.SpiDev()
spi.open(0,0) 
#spi.open(0, pe2a_GPIO_AI_CS3) # hata verirse pas geçilebilir
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

                    #return ((((0.0166308*(val & 0x0FFF)) + 0.01422)*100 )/16) -25  # ensure we are only sending 12b
                    return (val & 0x0FFF)
def chipSelectOfAI():
        GPIO.output(pe2a_GPIO_AI_CS3, GPIO.HIGH)  # AI_Pin  is DeActive
        time.sleep(0.01)
        GPIO.output(pe2a_GPIO_AI_CS3, GPIO.LOW)  # AI_Pin  is Active
        time.sleep(0.01)
class get_val():
    def __unit__(pins:(float, int)=0,**option):
        self.pins_val1 = pins_val1
        self.pins_val2 = pins_val2
        self.pins_val3 = pins_val3
        self.pins_val4 = pins_val4
        self.read_data =read_data
        self.val=val
        self.pins = pins

    
    def rpi_dig_vol_converter(self):
        return self.val*10.0/4095.0
    #init function
    GPIO.setmode(GPIO.BCM) #bcm library
    GPIO.setup(pe2a_GPIO_AI_CS3,GPIO.OUT)
    GPIO.output(pe2a_GPIO_AI_CS3, GPIO.HIGH)  # AI_Pin  is DeActive
    time.sleep(0.25)
    GPIO.output(pe2a_GPIO_AI_CS3, GPIO.LOW)  # AI_Pin  is Active
    GPIO.setwarnings(False)
    
    
    def fGPIOUpdate(self, pins:(float, int)):
        file1 = open("myfile1.txt","a")
        file2 = open("myfile2.txt","a")
        file3 = open("myfile3.txt","a")
        file4 = open("myfile4.txt","a")

        L1=[]
        L2=[]
        L3=[]
        L4=[]

        chipSelectOfAI()
        if pins == 1:
            pins_val1= rpi_readAI(0)
            file1.write(str('%.2f' % pins_val1)+ " " + time.ctime() + "\n")
            return pins_val1
        elif pins == 2:
            pins_val2= rpi_readAI(1)
            file2.write(str('%.2f' % pins_val2) + " " + time.ctime() + "\n")
            return pins_val2
        elif pins == 3:
            pins_val3= rpi_readAI(2)
            file3.write(str('%.2f' % pins_val3) + " " + time.ctime() + "\n")
            return pins_val3
        elif pins == 4:
            pins_val4= rpi_readAI(3)
            file4.write(str('%.2f' % pins_val4) + " " + time.ctime() + "\n")
            return pins_val4
        #update every 10000ms    
        #Analog Input
        
        



