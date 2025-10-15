# this file is to be the mock wristband peripheral script
# that will be used to test the bluetooth scan/connection

#dbus python3 is giving issues with installing -> trying bumble

import asyncio
import uuid

from bumble.device import Device, Advertisement
from bumble.gatt import Service, Characteristic, GATT_CHARACTERISTIC_ATTRIBUTE_TYPE


service_UUID = "8f5a84f1-22a8-4a4b-9b5f-3fe1d8b2a3a1"
char_uuid = "d3e2c4b7-39b2-4b2a-8d5a-7d2a5e3f1199"

async def run_properties():
	device = Device()

	vitals_service = Service(service_UUID)
	vitals_char = Characteristic(char_uuid, properties=[GATT_CHARACTERISTIC_ATTRIBUTE_TYPE])
	vitals_service.characteristics.append(vitals_char)
	device.add_service(vitals_service)

	print(device.public_address)
	advertisement = Advertisement(device.public_address)
	print(advertisement.address)

	advertisement.sid = "VitalLink-MOCK"
	advertisement.is_scannable = True
	advertisement.is_connectable = True
	advertisement.is_ready = True
	advertisement.service_uuid = service_UUID

	await device.ad