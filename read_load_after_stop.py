#!/usr/bin/env python
#
# *********     Gen Write Example      *********
#
#
# Available SCServo model on this example : All models using Protocol SCS
# This example is tested with a SCServo(STS/SMS/SCS), and an URT
# Be sure that SCServo(STS/SMS/SCS) properties are already set as %% ID : 1 / Baudnum : 6 (Baudrate : 1000000)
#

from typing import Counter
import matplotlib.pyplot as plt
import os
import time
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

from scservo_sdk import *                    # Uses SCServo SDK library

# Control table address
ADDR_SCS_TORQUE_ENABLE     = 40
ADDR_SCS_GOAL_ACC          = 41
ADDR_SCS_GOAL_POSITION     = 42
ADDR_SCS_GOAL_SPEED        = 46
ADDR_SCS_PRESENT_POSITION  = 56
ADDR_SCS_LOAD = 60

# Default setting
SCS_ID                      = 14                # SCServo ID : 1
BAUDRATE                    = 1000000           # SCServo default baudrate : 1000000
DEVICENAME                  = '/dev/ttyUSB3'    # Check which port is being used on your controller
                                                # ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

SCS_MINIMUM_POSITION_VALUE  = 610   # SCServo will rotate between this value
SCS_MAXIMUM_POSITION_VALUE  = 650      # and this value (note that the SCServo would not move when the position value is out of movable range. Check e-manual about the range of the SCServo you use.)
SCS_MOVING_STATUS_THRESHOLD = 5          # SCServo moving status threshold
SCS_MOVING_SPEED            = 10           # SCServo moving speed
SCS_MOVING_ACC              = 1           # SCServo moving acc
protocol_end                = 1           # SCServo bit end(STS/SMS=0, SCS=1)
count = 0
prev_position = SCS_MINIMUM_POSITION_VALUE
x_axis = []
y_axis = []
z_axis = []
index = 0
temp_count=0
counter = 0
state_count = 0
scs_goal_position = SCS_MINIMUM_POSITION_VALUE#, SCS_MAXIMUM_POSITION_VALUE]         # Goal position

# Initialize PortHandler instance
# Set the port path
# Get methods and members of PortHandlerLinux or PortHandlerWindows
portHandler = PortHandler(DEVICENAME)

# Initialize PacketHandler instance
# Get methods and members of Protocol
packetHandler = PacketHandler(protocol_end)

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
    
# Open port
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

# Write SCServo acc
scs_comm_result, scs_error = packetHandler.write1ByteTxRx(portHandler, SCS_ID, ADDR_SCS_GOAL_ACC, SCS_MOVING_ACC)
if scs_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(scs_comm_result))
elif scs_error != 0:
    print("%s" % packetHandler.getRxPacketError(scs_error))

# Write SCServo speed
scs_comm_result, scs_error = packetHandler.write2ByteTxRx(portHandler, SCS_ID, ADDR_SCS_GOAL_SPEED, SCS_MOVING_SPEED)
if scs_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(scs_comm_result))
elif scs_error != 0:
    print("%s" % packetHandler.getRxPacketError(scs_error))
state,scs_comm_result,scs_error = get_feedback()
SCS_MINIMUM_POSITION_VALUE = scs_present_position = scs_goal_position = state['position']
while 1:

    #print("Press any key to continue! (or press ESC to quit!)")
    #if getch() == chr(0x1b):
    #    break

    # Write SCServo goal position
    scs_comm_result, scs_error = packetHandler.write2ByteTxRx(portHandler, SCS_ID, ADDR_SCS_GOAL_POSITION, scs_goal_position)
    if scs_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(scs_comm_result))
        
    elif scs_error != 0:
        print("%s" % packetHandler.getRxPacketError(scs_error))
        """ state,scs_comm_result,scs_error = get_feedback()
        scs_present_position  = state['position']
        scs_present_speed = state['speed']
        load = state['load']
        z_axis.append(load)
        x_axis.append(temp_count)
        y_axis.append(scs_present_position) """
    while 1:
        temp_count+=1
        # Read SCServo present position
        state,scs_comm_result,scs_error = get_feedback()

        if scs_comm_result != COMM_SUCCESS:
            print(packetHandler.getTxRxResult(scs_comm_result))
        elif scs_error != 0:
            print(packetHandler.getRxPacketError(scs_error))
        scs_present_position  = state['position']
        """ 
        scs_present_speed = state['speed']
        load = state['load']
        load = load*1000
        z_axis.append(load)
        x_axis.append(temp_count)
        y_axis.append(scs_present_position)
        
        print("[ID:%03d] GoalPos:%03d PresPos:%03d LOAD:%03d PresSpd:%03d" 
                % (SCS_ID, scs_goal_position, scs_present_position, load, SCS_TOHOST(scs_present_speed, 15)))
        print("position difference", abs(scs_goal_position - scs_present_position)) """

        if (abs(scs_goal_position - scs_present_position) < SCS_MOVING_STATUS_THRESHOLD) or scs_error or temp_count == 500:# or temp_count == 3000:
            break
    temp_count = 0
    time.sleep(1)       # Add a stop before measuring anyvalue
    while state_count<20:
        state,scs_comm_result,scs_error = get_feedback()
        scs_present_position  = state['position']
        load = state['load']
        scs_present_speed = state['speed']
        load = load*1000
        print("position: ",scs_present_position,"load:",load)
        state_count += 1
    
    state_count = 0
    
    if load >= 1000:
       load -=1000
    
    if load >= 300:
        break
    #if load >= 1300: 
    #    break
    print("[ID:%03d] GoalPos:%03d PresPos:%03d LOAD:%03d PresSpd:%03d" 
        % (SCS_ID, scs_goal_position, scs_present_position, load, SCS_TOHOST(scs_present_speed, 15)))
    print("position difference", abs(scs_goal_position - scs_present_position))
    z_axis.append(load)
    #x_axis.append(temp_count)
    y_axis.append(scs_present_position)

    if scs_present_position == prev_position:
        count = count+1
    if count >= 10:    
        scs_goal_position = scs_goal_position+10
    prev_position = scs_present_position
    if abs(scs_present_position - scs_goal_position) <= SCS_MOVING_STATUS_THRESHOLD:         
        scs_goal_position = scs_goal_position+10
        


scs_comm_result, scs_error = packetHandler.write1ByteTxRx(portHandler, SCS_ID, ADDR_SCS_TORQUE_ENABLE, 0)
if scs_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(scs_comm_result))
elif scs_error != 0:
    print("%s" % packetHandler.getRxPacketError(scs_error))
# Close port
portHandler.closePort()
fig, axs = plt.subplots(2)
#fig.suptitle('Vertically stacked subplots')
#axs[0].plot(x_axis, y_axis)
#axs[1].plot(x_axis, z_axis)
axs[0].plot(y_axis,z_axis)
plt.show()
