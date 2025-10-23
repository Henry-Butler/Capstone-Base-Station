"""
VitalLink Main System Runner
Runs the complete system with real and/or simulated wristbands
"""

import asyncio
import aiohttp
import time
import struct
from wristband_manager import WristbandManager, WristbandType
from config_system import WristbandConfig
import sys


class VitalLinkSystem:
    """Main system orchestrator"""

    def __init__(self):
        self.manager = WristbandManager()
        self.config = WristbandConfig()
        self.backend_url = self.config.get("backend_url", "http://localhost:8000")
        self.running = False
        self.monitoring_task = None

    async def initialize(self):
        print("\n" + "=" * 80)
        print("VitalLink System Initialization")
        print("=" * 80 + "\n")

        backend_ok = await self.check_backend()
        if not backend_ok:
            print("\n⚠️  Warning: Backend not running. System will wait for backend...")

        if self.config.get("auto_scan_ble", False):
            timeout = self.config.get("scan_timeout", 10.0)
            await self.manager.scan_for_real_bands(timeout)

        for band_config in self.config.get_real_bands() or []:
            self.manager.add_real_band(
                band_config["band_id"], band_config["ble_address"]
            )

        for band_config in self.config.get_simulated_bands() or []:
            self.manager.add_simulated_band(
                band_config["band_id"], band_config.get("profile", "stable")
            )

        self.manager.print_inventory()

    async def check_backend(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/", timeout=aiohttp.ClientTimeout(total=3)
                ) as resp:
                    if resp.status == 200:
                        print(f"✓ Backend is running at {self.backend_url}")
                        return True
        except:
            print(f"❌ Backend not reachable at {self.backend_url}")
            return False

        return False

    def _decode_packet_for_display(self, packet: bytes) -> dict:
        if len(packet) != 16:
            return {}

        PKT_STRUCT = struct.Struct("<B H I B B B h H B B")
        (
            ver,
            seq,
            ts_ms,
            flags,
            hr_bpm,
            spo2,
            skin_c_x100,
            act_rms_x100,
            checksum,
            rfu,
        ) = PKT_STRUCT.unpack(packet)

        return {
            "version": ver,
            "sequence": seq,
            "timestamp_ms": ts_ms,
            "flags": {
                "raw": flags,
                "motion_artifact": bool(flags & (1 << 0)),
                "low_battery": bool(flags & (1 << 1)),
                "sensor_fault": bool(flags & (1 << 2)),
                "alert": bool(flags & (1 << 3)),
                "emergency": bool(flags & (1 << 4)),
            },
            "hr_bpm": hr_bpm,
            "spo2": spo2,
            "temperature_c": skin_c_x100 / 100.0,
            "activity": act_rms_x100 / 100.0,
            "checksum": f"0x{checksum:02X}",
            "reserved": rfu,
        }

    async def report_inventory_to_backend(self):
        try:
            inventory = {"timestamp": time.time(), "wristbands": []}

            for band_id, band in self.manager.inventory.items():
                band_info = {
                    "band_id": band.band_id,
                    "type": band.type.value,
                    "status": band.status.value,
                    "patient_id": band.patient_id,
                    "packet_count": band.packet_count,
                    "is_monitoring": band_id in self.manager.active_monitoring,
                    "last_packet": band.last_packet,
                }

                if band.type == WristbandType.SIMULATED and hasattr(
                    band, "last_raw_packet"
                ):
                    if band.last_raw_packet:
                        band_info["last_raw_packet"] = {
                            "hex": band.last_raw_packet.hex(),
                            "bytes": list(band.last_raw_packet),
                            "decoded": self._decode_packet_for_display(
                                band.last_raw_packet
                            ),
                        }

                    if hasattr(band, "packet_history"):
                        band_info["recent_packets"] = band.packet_history[-5:]

                inventory["wristbands"].append(band_info)

            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{self.backend_url}/api/wristband-details", json=inventory
                )
        except:
            pass

    async def monitor_new_patients(self):
        print("\n🔍 Monitoring for new patient check-ins...")

        known_patients = set()
        prefer_real = self.config.get("prefer_real_bands", False)

        while self.running:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.backend_url}/api/queue") as resp:
                        if resp.status == 200:
                            queue = await resp.json()

                            for patient in queue:
                                patient_id = patient["patient_id"]

                                if patient_id not in known_patients:
                                    known_patients.add(patient_id)

                                    has_active_band = any(
                                        b.patient_id == patient_id
                                        and b.band_id in self.manager.active_monitoring
                                        for b in self.manager.inventory.values()
                                    )

                                    if not has_active_band:
                                        print(
                                            f"\n🆕 New patient detected: {patient_id} ({patient['name']})"
                                        )

                                        band = self.manager.assign_band(
                                            patient_id, prefer_real=prefer_real
                                        )

                                        if band:
                                            print(
                                                f"   ✓ Assigned {band.band_id} ({band.type.value})"
                                            )
                                            await self.manager.start_monitoring(
                                                band.band_id
                                            )
                                        else:
                                            print(
                                                f"   ⚠️  No bands available, creating emergency simulated band..."
                                            )

                                            emergency_band_id = f"MOCK-EMRG{len(self.manager.inventory):02d}"
                                            band = self.manager.add_simulated_band(
                                                emergency_band_id, "stable"
                                            )
                                            band.assign_to_patient(patient_id)

                                            print(
                                                f"   ✓ Created and assigned {emergency_band_id}"
                                            )
                                            await self.manager.start_monitoring(
                                                band.band_id
                                            )
            except:
                pass

            await asyncio.sleep(2)

    async def run(self):
        self.running = True

        await self.initialize()

        print("\n" + "=" * 80)
        print("VitalLink System Running")
        print("=" * 80)
        print("\n✓ Monitoring for new patients from kiosk check-ins")
        print(
            "✓ Auto-assigning wristbands (prefer real: {})".format(
                self.config.get("prefer_real_bands", False)
            )
        )
        print("\nPress Ctrl+C to stop\n")
        print("=" * 80 + "\n")

        self.monitoring_task = asyncio.create_task(self.monitor_new_patients())

        try:
            while self.running:
                await asyncio.sleep(10)

                status = self.manager.get_status()
                available = status["status_breakdown"].get("available", 0)

                print(
                    f"[Status] Active: {status['active_monitoring']} monitoring | "
                    f"Available: {available} bands | "
                    f"Real: {status['real_bands']} | "
                    f"Sim: {status['simulated_bands']}"
                )

                await self.report_inventory_to_backend()

        except KeyboardInterrupt:
            print("\n\n⚠️  Shutting down...")
            await self.shutdown()

    async def shutdown(self):
        self.running = False

        if self.monitoring_task:
            self.monitoring_task.cancel()

        print("Stopping all wristband monitoring...")
        for band_id in list(self.manager.active_monitoring.keys()):
            await self.manager.stop_monitoring(band_id)

        print("\n✓ VitalLink system stopped")
        self.manager.print_inventory()


if __name__ == "__main__":
    try:
        system = VitalLinkSystem()
        asyncio.run(system.run())
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
