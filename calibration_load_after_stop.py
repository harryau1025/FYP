from typing import Counter
#import matplotlib.pyplot as plt
import os
import yaml
import time
from scservo_sdk import *  # Uses SCServo SDK library
if os.name == 'nt':
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
                   
#Control table address
ADDR_SCS_TORQUE_ENABLE     = 40
ADDR_SCS_GOAL_ACC          = 41
ADDR_SCS_GOAL_POSITION     = 42
ADDR_SCS_GOAL_SPEED        = 46
ADDR_SCS_PRESENT_POSITION  = 56
ADDR_SCS_LOAD = 60

# # Default setting
SCS_ID                      = 1                # SCServo ID : 1
BAUDRATE                    = 1000000           # SCServo default baudrate : 1000000
DEVICENAME                  = '/dev/ttyUSB3'    # Check which port is being used on your controller
                                                # ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"
SCS_MOVING_SPEED            = 100           # SCServo moving speed
SCS_MOVING_ACC              = 1           # SCServo moving acc
protocol_end                = 1           # SCServo bit end(STS/SMS=0, SCS=1)

portHandler = PortHandler(DEVICENAME)

# Initialize PacketHandler instance
# Get methods and members of Protocol
packetHandler = PacketHandler(protocol_end)

def get_feedback(SCS_ID):
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

if portHandler.openPort():
    print("Succeeded to open the port")
else:
    print("Failed to open the port")
    print("Press any key to terminate...")
    getch()
    quit()
if portHandler.setBaudRate(BAUDRATE):
    print("Succeeded to change the baudrate")
else:
    print("Failed to change the baudrate")
    print("Press any key to terminate...")
    getch()
    quit()

motor_name = 0

class motor:

    def __init__(self,ID,precision = 20,load_lim=0.30):
        
        self.ID = ID			### ID of the motor
        self.load_lim = load_lim	### set the load limit 
        self.precision = precision
        motor_name = ID

    def calibration(self,side):
        ID = self.ID
        load_lim = self.load_lim
        precision = self.precision
        state ,scs_comm_result,scs_error = get_feedback(ID)
        position  = state['position']
        goal = position
        prev_position = position
        count = 0
        #load = 0
        while True: 
            
            state ,scs_comm_result,scs_error = get_feedback(ID)
            position  = state['position']            
            #load = state['load']
            #if side == 1 or load >= 1:
            #if load > 1:
            #    load = load-1
            
            #if side == 0:
            #    goal = 419
            #elif side == 1:
            #    goal == 419

            if scs_comm_result != COMM_SUCCESS:
                continue     ### if there is a communication error get it again

            
            if abs(position - goal) <= 5:
            #if position == goal:
                state ,scs_comm_result,scs_error = get_feedback(ID)
                load = state['load']
                if side == 1 or load >= 1:
                #if load >1:
                    load = load-1
                if side == 0: 	     ###set new goal				
                    goal -= precision 
                    if goal < 0:
                        goal = 0
                elif side == 1:
                    goal += precision
                    if goal > 4000:
                       goal = 4000
            
            scs_comm_result, scs_error = packetHandler.write2ByteTxRx(portHandler, ID, ADDR_SCS_GOAL_POSITION,goal) 
            if prev_position == position:
                count += 1
                state ,scs_comm_result,scs_error = get_feedback(ID)
                load = state['load']
                if load > 1 or side == 1:
                    load = load-1
            else: 
                count = 0
                if side == 0: 
                    goal = position - precision
                else:
                    goal = position + precision

            if count > 5:
                if side == 0:
                    goal -=precision
                    if goal < 0:
                        goal = 0
                if side == 1:
                    goal += precision
                    if goal > 4000:
                        goal = 4000       
            prev_position = position
            print(' goal: ',goal,' position: ', position,  'load: ',load)
            if load >= load_lim:
                break 
            #if side == 0:
            #    scs_comm_result, scs_error = packetHandler.write2ByteTxRx(portHandler, ID, ADDR_SCS_GOAL_POSITION,0)		     ### add this line to move the motor to goal
            #if side == 1:
            #    scs_comm_result, scs_error = packetHandler.write2ByteTxRx(portHandler, ID, ADDR_SCS_GOAL_POSITION,4000)

        #if side == 0:		    ###set the limit before overload
                limit = position #+ precision
        #elif side == 1:
        #        limit = position #- precision
        state ,scs_comm_result,scs_error = get_feedback(ID)
        limit = state["position"]

        return limit


    def write(self):
        print("calibrate min")
        min = self.calibration(0)
        print("calibrate max")
        max = self.calibration(1)
		# Write to .yaml file

        fname = "feetechsmall.yaml"
        #fname = "/home/fyp/Downloads/SCServo_Python_200831/SCServo_Python/feetechsmall.yaml"
        stream = open(fname, 'r')
        data = yaml.load(stream, Loader=yaml.FullLoader)

        if self.ID == 15:
            motor_n = "EyeTurnRight"
        else:
            motor_n = "EyeTurnLeft"
        init = int((min + max) /2)
        data[motor_n]['min'] = min
        data[motor_n]['max'] = max
        data[motor_n]['init'] = init

        with open(fname, 'w') as yaml_file:
            yaml_file.write( yaml.dump(data, default_flow_style=False)) 

if __name__ == "__main__":
    '''    print('hi')
    if os.name == 'nt':
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

                    # Uses SCServo SDK library

# Control table address
    ADDR_SCS_TORQUE_ENABLE     = 40
    ADDR_SCS_GOAL_ACC          = 41
    ADDR_SCS_GOAL_POSITION     = 42
    ADDR_SCS_GOAL_SPEED        = 46
    ADDR_SCS_PRESENT_POSITION  = 56
    ADDR_SCS_LOAD = 60

    # Default setting
    #SCS_ID                      = 14                # SCServo ID : 1
    BAUDRATE                    = 1000000           # SCServo default baudrate : 1000000
    DEVICENAME                  = '/dev/ttyUSB1'    # Check which port is being used on your controller
                                                    # ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"
    SCS_MOVING_SPEED            = 10           # SCServo moving speed
    SCS_MOVING_ACC              = 0           # SCServo moving acc
    protocol_end                = 1           # SCServo bit end(STS/SMS=0, SCS=1)

    portHandler = PortHandler(DEVICENAME)

    # Initialize PacketHandler instance
    # Get methods and members of Protocol
    packetHandler = PacketHandler(protocol_end)
    if portHandler.openPort():
        print("Succeeded to open the port")
    else:
        print("Failed to open the port")
        print("Press any key to terminate...")
        getch()
        quit()
    if portHandler.setBaudRate(BAUDRATE):
        print("Succeeded to change the baudrate")
    else:
        print("Failed to change the baudrate")
        print("Press any key to terminate...")
        getch()
        quit()'''
    Leye = motor(14)
    Leye.write()
    Reye = motor(15)
    Reye.write()
    UDeye = motor(16)
    UDeye.write()
     
    #min = Leye.calibration(0)
    #time.sleep(1)
    #max = Leye.calibration(1)
    #print("min= ",min, "max= ", max)

    '''
    min = Leye.calibration(0)
    print('calibrate')
    max = Leye.calibration(1)
    print(min)
    print(max)
    init = int((min + max) /2)
    print('init = ', init)'''