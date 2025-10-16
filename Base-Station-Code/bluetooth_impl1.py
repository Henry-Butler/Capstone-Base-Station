###############################
#                             #
#      Bluetooth Module       #
#                             #
#                             #
###############################

import pprint as pp
import simplepyble
import time
import Wristband

BraceletNames = "VTL-1"
ServiceUUID = 0xa1a3b2d8e13f5f9b4b4aa822f1845a8f
CharUUID = 0x99113f5e2a7d5a8d2a4bb239b7c4e2d3
Wristband1 = Wristband("Wristband1", 0)
Wristbands = [Wristband1]
class BraceletManager:
	"""
	This class contains the
	"""
	
	def __init__(self):
		self.adapter = simplepyble.Adapter.get_adapters()

		if not self.adapter:
			raise RuntimeError("No Bluetooth device found")
		self.adapter = self.adapter[0]
		self.dev_id = 1
		self.assigned_devices = {} # address will correspond to the ID

	def assign_id(self, peripheral) -> int:
		"""
		Assigns a new ID to a Bracelet if not already assigned.

		:param peripheral:
		:return:
		"""
		addr = peripheral.address()
		if addr not in self.assigned_devices:
			# if the device is not already assigned
			self.assigned_devices[addr] = self.dev_id
			# then add one to the previous value
			self.dev_id += 1

		return self.assigned_devices[addr]

	def scan_and_connect(self):
		print("Scanning for bracelets......")
		# scan for around 10 seconds
		self.adapter.scan_for(10000)
		peripherals = self.adapter.scan_get_results()

		for p in peripherals:
            # Look for devices with the name convention we will use
			if BraceletNames in p.idenitfiers():
				Bracelet_id = self.assign_id(p)
				
				print(f"Bracelet #{Bracelet_id} deteced: {p.idenitfier()}")
				try:
					p.connect()
					print(f"Bracelet #{Bracelet_id} connected.")
					p.notify(ServiceUUID, CharUUID, Wristbands[Bracelet_id].receive_packet)
					p.disconnect()
					print(f"Bracelet #{Bracelet_id} disconnected (test complete.)")
				except Exception as e:
					print(f"Bracelet #{Bracelet_id} failed to connect.")
				
	def run(self):
		while True:
			self.scan_and_connect()
			# wait before the next scan cycle
			time.sleep(8)
	


if __name__ == "__main__":
	manager = BraceletManager()
	manager.run()