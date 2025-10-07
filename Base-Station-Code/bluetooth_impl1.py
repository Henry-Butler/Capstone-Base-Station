###############################
#                             #
#      Bluetooth Module       #
#                             #
#                             #
###############################

import pprint as pp
import simplepyble
import time

bracletNames = "VTL-1"
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
		Assigns a new ID to a braclet if not already assigned.

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
        """
        """
        print("Scanning for bracelets......")
        # scan for around 10 seconds
        self.adapter.scan_for(10000)
        peripherals = self.adapter.scan_get_results()

        for p in peripherals:
            # Look for devices with the name convention we will use
            if bracletNames in p.idenitfiers():
                #
                braclet_id = self.assign_id(p)
                print(f"Braclet #{braclet_id} deteced: {p.idenitfier()}")

                try:
                    p.connect()
                    print(f"Braclet #{braclet_id} connected.")
                    p.disconnect()
                    print(f"Braclet #{braclet_id} disconnected (test complete.")
                except Exception as e:
                    print(f"Braclet #{braclet_id} failed to connect.")

   def run(self):
	while True:
		self.scan_and_connect()
		# wait before the next scan cycle
		time.sleep(8)

if __name__ == "__main__":
	manager = BraceletManager()
	manager.run()