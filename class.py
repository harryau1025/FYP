import math
from scservo_sdk import *

class EyeMotor:
	def __init__(self,ID):
		SCS_ID                      = ID
		self.ID                     = ID	                # SCServo ID : 1
		self.BAUDRATE                    = 1000000           # SCServo default baudrate : 1000000
		self.DEVICENAME = DEVICENAME     = '/dev/ttyUSB3'
		self.SCS_MOVING_STATUS_THRESHOLD = 5          # SCServo moving status threshold
		self.SCS_MOVING_SPEED            = 1           # SCServo moving speed
		self.SCS_MOVING_ACC              = 1           # SCServo moving acc
		self.ADDR_SCS_TORQUE_ENABLE     = 40                     
		self.ADDR_SCS_GOAL_ACC          = 41
		self.ADDR_SCS_GOAL_POSITION     = 42
		self.ADDR_SCS_GOAL_SPEED        = 46
		self.ADDR_SCS_PRESENT_POSITION  = 56
		self.protocol_end   = protocol_end   = 1
		self.portHandler = PortHandler(DEVICENAME)
		self.packetHandler = PacketHandler(protocol_end)
	
	def get_feedback(self):
		self.portHandler.openPort()
		self.portHandler.setBaudRate(self.BAUDRATE)
		data_read, results, error = self.packetHandler.readTxRx(self.portHandler, self.ID,self.ADDR_SCS_PRESENT_POSITION , 15)
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

	def move(self,angle):
		self.portHandler.openPort()
		self.portHandler.setBaudRate(self.BAUDRATE)
		scs_comm_result, scs_error = self.packetHandler.write1ByteTxRx(self.portHandler, self.ID, self.ADDR_SCS_GOAL_ACC, self.SCS_MOVING_ACC)
		position = angle/300*1024
		scs_comm_result, scs_error = self.packetHandler.write1ByteTxRx(self.portHandler, self.ID, self.ADDR_SCS_GOAL_ACC, self.SCS_MOVING_ACC)
		if scs_comm_result != COMM_SUCCESS:
			print("%s" % self.packetHandler.getTxRxResult(scs_comm_result))
		elif scs_error != 0:
			print("%s" % self.packetHandler.getRxPacketError(scs_error))

		# Write SCServo speed
		scs_comm_result, scs_error = self.packetHandler.write2ByteTxRx(self.portHandler,self.ID, self.ADDR_SCS_GOAL_SPEED, self.SCS_MOVING_SPEED)

		if scs_comm_result != COMM_SUCCESS:
			print("%s" % self.packetHandler.getTxRxResult(scs_comm_result))
		elif scs_error != 0:
			print("%s" %self.packetHandler.getRxPacketError(scs_error))
		state,scs_comm_result,scs_error = self.get_feedback()
		scs_present_position  = state['position']   #get the motor status
		print(scs_present_position)
		#if position > scs_present_position: 
		#	goal = 0
		#else:       
		#	goal = 1024
		scs_comm_result, scs_error = self.packetHandler.write2ByteTxRx(self.portHandler, self.ID, self.ADDR_SCS_GOAL_POSITION, int(position))

		while 1:
			state,scs_comm_result,scs_error = self.get_feedback()
			scs_present_position  = state['position']   #get the motor status
			load = state['load']*1000
			print("position:",scs_present_position,"load:",load)
			if load >= 1000:
				load -= 1000
			if load >= 300 or (abs(position - scs_present_position)) < self.SCS_MOVING_STATUS_THRESHOLD:
				break 
			
if __name__ == '__main__':
	left = EyeMotor(14)
	#while True:
	#	states,result,error = left.get_feedback()
	#	print('position: ',states['position'],'load: ',states['load'])
	left.move(122)
	
