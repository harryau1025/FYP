#Just to get load
import os
import time
if os.name == 'nt':                                                    #def getch() for interactive control 
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
        
else:
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

from scservo_sdk import *                    # Uses SCServo SDK library

# Control table address
ADDR_SCS_TORQUE_ENABLE     = 40                     
ADDR_SCS_GOAL_ACC          = 41
ADDR_SCS_GOAL_POSITION     = 42
ADDR_SCS_GOAL_SPEED        = 46
ADDR_SCS_PRESENT_POSITION  = 56
ADDR_SCS_LOAD = 60

# Default setting
SCS_ID                      = 14               # SCServo ID : 1
BAUDRATE                    = 1000000           # SCServo default baudrate : 1000000
DEVICENAME                  = '/dev/ttyUSB3'    # Check which port is being used on your controller
                                                # ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

SCS_MINIMUM_POSITION_VALUE  = 600   # SCServo will rotate between this value
SCS_MAXIMUM_POSITION_VALUE  = 600      # and this value (note that the SCServo would not move when the position value is out of movable range. Check e-manual about the range of the SCServo you use.)
SCS_MOVING_STATUS_THRESHOLD = 10          # SCServo moving status threshold
SCS_MOVING_SPEED            = 1           # SCServo moving speed
SCS_MOVING_ACC              = 1           # SCServo moving acc
protocol_end                = 10           # SCServo bit end(STS/SMS=0, SCS=1)
x_axis = []                                #define axis for ploting graph 
y_axis = []
z_axis = []
index = 0
temp_count=0
counter = 0
scs_goal_position = [SCS_MINIMUM_POSITION_VALUE, SCS_MAXIMUM_POSITION_VALUE]         # Goal position    

# Initialize PortHandler instance
# Set the port path
# Get methods and members of PortHandlerLinux or PortHandlerWindows
portHandler = PortHandler(DEVICENAME)

# Initialize PacketHandler instance
# Get methods and members of Protocol
packetHandler = PacketHandler(protocol_end)

#Provide the data in states reading from the given port 
def get_feedback():
    data_read, results, error = packetHandler.readTxRx(portHandler, SCS_ID, ADDR_SCS_PRESENT_POSITION, 15)
    if len(data_read) ==  15:
        state = {
            'time': time.time(), # Time of feedback capture
            'position': SCS_MAKEWORD(data_read[0], data_read[1]),
            'speed':  SCS_TOHOST(SCS_MAKEWORD(data_read[2], data_read[3]),15),
            'load': SCS_MAKEWORD(data_read[4], data_read[5])/1000.0,
            'voltage': data_read[6]/10.0,
            'temperature': data_read[7],
            'status': data_read[9],
            'moving': data_read[10],
            'current': SCS_MAKEWORD(data_read[13], data_read[14]),
            }
    return state,results,error
    
# Open port #To check if there is an error opening certain port e.g. the port given is not connected
if portHandler.openPort():                  
    print("Succeeded to open the port")
else:
    print("Failed to open the port")
    print("Press any key to terminate...")
    getch()
    quit()
# Set port baudrate
if portHandler.setBaudRate(BAUDRATE):
    print("Succeeded to change the baudrate")
else:
    print("Failed to change the baudrate")
    print("Press any key to terminate...")
    getch()
    quit()

	
if __name__ == '__main__':
    while True: 
        time.sleep(0.2) 
        state,scs_comm_result,scs_error = get_feedback()
        load = state['load']*1000
        position  = state['position']
        print('load: ',load)
        print('position: ',position)

# load below 100 in the original read file will be shown as 0
# Larger than 100 will shown as the same value
# Posisiton measured here might be different from the command given (might be cause by the position change after stopping the motion)
