###############################
#                             #
#      Bluetooth Module       #
#                             #
#                             #
###############################

import pprint as pp
import simplepyble
import struct
import time

bracelet_names = "VTL-1"


class BraceletManager:
	"""
	This class that will be the "manager" for facilitating the bracelets, and processing
	information from bracelets while worn on patients.
	"""

	def __init__(self):
		self.adapter = simplepyble.Adapter.get_adapters()

		if not self.adapter:
			raise RuntimeError("No Bluetooth device found")

		self.adapter = self.adapter[0]
		self.dev_id = 1
		self.assigned_devices = {}  # address will correspond to the ID

	def assign_id(self, peripheral) -> int:
		"""
		Assigns a new ID to a bracelet if not already assigned.

		:param peripheral:
		:return: int
		"""
		addr = peripheral.address()
		if addr not in self.assigned_devices:
			# if the device is not already assigned
			self.assigned_devices[addr] = self.dev_id
			# then add one to the previous value
			self.dev_id += 1

		return self.assigned_devices[addr]

	def scan_and_connect(self) -> None:
		"""
		This method scans the for bluetooth devices and connects to them.
		:return: None
		"""
		# TODO: this may need to be a loop that just runs until a device is found
		print("Scanning for bracelets......\n")
		# scan for around 10 seconds
		self.adapter.scan_for(10000)
		peripherals = self.adapter.scan_get_results()

		for p in peripherals:
			# Look for devices with the name convention we will use
			if bracelet_names in p.idenitfiers():
				# assign that bracelet an id
				braclet_id = self.assign_id(p)
				print(f"Bracelet #{braclet_id} detected: {p.idenitfier()}")

				try:
					p.connect()
					print(f"Bracelet #{braclet_id} connected.")

					# replace the UUIDs:
					service_uuid = p.services()
					for service in service_uuid:
						chars = p.characteristic(service)
						# if the correct characteristic for data then connect
						if 'd3e2c4b7-39b2-4b2a-8d5a-7d2a5e3f1199' in chars:
							def notify_handler(data):
								self.process_packet(data)
							p.notify(service, chars, notify_handler)
							print("Notification handler set.")

					#wait and keep the connection alive
					# TODO Test the length of the connect as i think this is in seconds
					time.sleep(90)
					p.disconnect()
					print(f"Bracelet #{braclet_id} disconnected (test complete.)")
				except Exception as e:
					print(f"Bracelet #{braclet_id} failed to connect.")


	def processPacket(self, data: bytes) -> None:
		"""
		Parses received data in packet from wristband device.

		:param self:
		:type self:
		:param data: Data received from wristband device.
		:type data: bytes
		:return:
		:rtype:
		"""
		# B - uint 8, H - uint16, I - uint32, b - int8, h - int16

		# check that het received data is 16 bytes
		if len(data) < 16:
			print("Invalid packet length")
			return

		fields = struct.unpack("<B H I B B B h h B B ", data)
		parsed = {
			"ver": fields[0],
			"seq": fields[1],
			"ts_ms": fields[2],
			"flags": fields[3],
			"hr_bpms": fields[4],
			"spo2": fields[5],
			"skin_c_x100": fields[6] / 100.0,
			"act_rms_x100": fields[7] / 100.0,
			"checksum8": fields[8],
			"rfu":fields[9],
		}
		#debug and check
		print(f"Decoded Packet: {parsed}")
		# decode and print
		print(f"Received {data.hex()} bytes from device {self.dev_id}\n")



	def run(self):
		while True:
			self.scan_and_connect()
			# wait before the next scan cycle
			time.sleep(8)


if __name__ == "__main__":
	manager = BraceletManager()
	manager.run()
