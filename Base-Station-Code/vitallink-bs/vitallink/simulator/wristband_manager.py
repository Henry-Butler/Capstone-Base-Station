"""
VitalLink Wristband Management System
Unified system for managing real and simulated wristbands
"""

import asyncio
import struct
import random
import time
import aiohttp
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

# Try to import BLE library (for real hardware)
try:
    from bleak import BleakScanner, BleakClient

    BLE_AVAILABLE = True
except ImportError:
    BLE_AVAILABLE = False
    print(
        "⚠️  Bleak not installed. Real wristbands disabled. Install with: pip install bleak"
    )

# ============================================================================
# CONFIGURATION
# ============================================================================

SERVICE_UUID = "8f5a84f1-22a8-4a4b-9b5f-3fe1d8b2a3a1"
CHAR_UUID = "d3e2c4b7-39b2-4b2a-8d5a-7d2a5e3f1199"
BACKEND_URL = "http://localhost:8000"

PKT_STRUCT = struct.Struct("<B H I B B B h H B B")


class WristbandType(Enum):
    REAL = "real"
    SIMULATED = "simulated"


class WristbandStatus(Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    IN_USE = "in_use"
    CHARGING = "charging"
    MAINTENANCE = "maintenance"


# ============================================================================
# PACKET DECODER
# ============================================================================


class PacketDecoder:
    """Decodes BLE packets from real wristbands according to spec"""

    @staticmethod
    def decode(data: bytes) -> Optional[dict]:
        """Decode 16-byte packet from wristband"""
        if len(data) != 16:
            return None

        checksum_calc = sum(data[0:14]) & 0xFF
        if checksum_calc != data[14]:
            print(f"⚠️  Checksum failed: expected {data[14]}, got {checksum_calc}")
            return None

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
        ) = PKT_STRUCT.unpack(data)

        tier = "NORMAL"
        if flags & (1 << 4):
            tier = "EMERGENCY"
        elif flags & (1 << 3):
            tier = "ALERT"

        return {
            "ver": ver,
            "seq": seq,
            "ts_ms": ts_ms,
            "tier": tier,
            "hr_bpm": hr_bpm,
            "spo2": spo2,
            "temp_c": skin_c_x100 / 100.0,
            "activity": act_rms_x100 / 100.0,
            "flags": flags,
            "checksum": f"0x{checksum:02X}",
        }


# ============================================================================
# ABSTRACT WRISTBAND INTERFACE
# ============================================================================


class BaseWristband(ABC):
    """Abstract base class for all wristbands"""

    def __init__(self, band_id: str, wristband_type: WristbandType):
        self.band_id = band_id
        self.type = wristband_type
        self.status = WristbandStatus.AVAILABLE
        self.patient_id: Optional[str] = None
        self.last_packet: Optional[dict] = None
        self.packet_count = 0

    @abstractmethod
    async def start_monitoring(self):
        pass

    @abstractmethod
    async def stop_monitoring(self):
        pass

    def assign_to_patient(self, patient_id: str):
        self.patient_id = patient_id
        self.status = WristbandStatus.ASSIGNED
        print(f"✓ {self.band_id} assigned to patient {patient_id}")

    def release(self):
        self.patient_id = None
        self.status = WristbandStatus.AVAILABLE
        self.packet_count = 0
        print(f"✓ {self.band_id} released and available")


# ============================================================================
# REAL WRISTBAND
# ============================================================================


class RealWristband(BaseWristband):
    """Real physical wristband using BLE"""

    def __init__(self, band_id: str, ble_address: str):
        super().__init__(band_id, WristbandType.REAL)
        self.ble_address = ble_address
        self.client: Optional[BleakClient] = None
        self.decoder = PacketDecoder()

    async def start_monitoring(self):
        if not BLE_AVAILABLE:
            raise RuntimeError("Bleak library not available")

        self.status = WristbandStatus.IN_USE
        print(
            f"🔵 Connecting to real wristband {self.band_id} at {self.ble_address}..."
        )

        try:
            self.client = BleakClient(self.ble_address)
            await self.client.connect()
            print(f"✓ Connected to {self.band_id}")

            await self.client.start_notify(CHAR_UUID, self._notification_handler)
            print(f"✓ Subscribed to notifications from {self.band_id}")

        except Exception as e:
            print(f"❌ Failed to connect to {self.band_id}: {e}")
            self.status = WristbandStatus.MAINTENANCE

    def _notification_handler(self, sender, data: bytearray):
        decoded = self.decoder.decode(bytes(data))
        if decoded:
            self.last_packet = decoded
            self.packet_count += 1
            asyncio.create_task(self._send_to_backend(decoded))

    async def _send_to_backend(self, decoded: dict):
        if not self.patient_id:
            return

        payload = {
            "band_id": self.band_id,
            "patient_id": self.patient_id,
            "timestamp": time.time(),
            "ver": decoded["ver"],
            "seq": decoded["seq"],
            "ts_ms": decoded["ts_ms"],
            "tier": decoded["tier"],
            "flags": [],
            "hr_bpm": decoded["hr_bpm"],
            "spo2": decoded["spo2"],
            "temp_c": decoded["temp_c"],
            "activity": decoded["activity"],
        }

        try:
            async with aiohttp.ClientSession() as session:
                await session.post(f"{BACKEND_URL}/api/vitals", json=payload)
        except:
            pass

    async def stop_monitoring(self):
        if self.client and self.client.is_connected:
            await self.client.stop_notify(CHAR_UUID)
            await self.client.disconnect()
            print(f"✓ Disconnected from {self.band_id}")

        self.status = WristbandStatus.AVAILABLE


# ============================================================================
# SIMULATED WRISTBAND
# ============================================================================


class SimulatedWristband(BaseWristband):
    """Simulated wristband for testing"""

    def __init__(self, band_id: str, profile: str = "stable"):
        super().__init__(band_id, WristbandType.SIMULATED)
        self.profile = profile
        self.seq = 0
        self.running = False
        self.last_raw_packet = None
        self.packet_history = []

        from wristband_simulator import PATIENT_PROFILES, WristbandSimulator

        self.simulator = WristbandSimulator(
            band_id, PATIENT_PROFILES.get(profile, PATIENT_PROFILES["stable"]), None
        )

    async def start_monitoring(self):
        self.status = WristbandStatus.IN_USE
        self.running = True
        self.simulator.patient_id = self.patient_id

        print(f"🟢 Starting simulated wristband {self.band_id} ({self.profile})")

        while self.running:
            packet = self.simulator.generate_packet()

            self.last_raw_packet = packet
            self.packet_history.append(
                {"timestamp": time.time(), "raw": packet.hex(), "bytes": list(packet)}
            )
            if len(self.packet_history) > 50:
                self.packet_history = self.packet_history[-50:]

            decoder = PacketDecoder()
            decoded = decoder.decode(packet)

            if decoded:
                self.last_packet = decoded
                self.packet_count += 1
                await self._send_to_backend(decoded)

            tier = self.simulator.tier
            interval = 1.0 if tier in ["ALERT", "EMERGENCY"] else 60.0
            await asyncio.sleep(interval)

    async def _send_to_backend(self, decoded: dict):
        if not self.patient_id:
            return

        payload = {
            "band_id": self.band_id,
            "patient_id": self.patient_id,
            "timestamp": time.time(),
            "ver": decoded["ver"],
            "seq": decoded["seq"],
            "ts_ms": decoded["ts_ms"],
            "tier": decoded["tier"],
            "flags": [],
            "hr_bpm": decoded["hr_bpm"],
            "spo2": decoded["spo2"],
            "temp_c": decoded["temp_c"],
            "activity": decoded["activity"],
        }

        try:
            async with aiohttp.ClientSession() as session:
                await session.post(f"{BACKEND_URL}/api/vitals", json=payload)
        except:
            pass

    async def stop_monitoring(self):
        self.running = False
        self.status = WristbandStatus.AVAILABLE
        print(f"✓ Stopped simulated wristband {self.band_id}")


# ============================================================================
# WRISTBAND MANAGER
# ============================================================================


class WristbandManager:
    """Central manager for all wristbands"""

    def __init__(self):
        self.inventory: Dict[str, BaseWristband] = {}
        self.active_monitoring: Dict[str, asyncio.Task] = {}

    def add_simulated_band(self, band_id: str, profile: str = "stable"):
        if not band_id.startswith("MOCK-"):
            band_id = f"MOCK-{band_id.replace('VitalLink-', '').replace('MOCK-', '')}"

        band = SimulatedWristband(band_id, profile)
        self.inventory[band_id] = band
        print(f"➕ Added simulated band {band_id} ({profile})")
        return band

    def add_real_band(self, band_id: str, ble_address: str):
        if not BLE_AVAILABLE:
            print("❌ Cannot add real band: Bleak not installed")
            return None

        band = RealWristband(band_id, ble_address)
        self.inventory[band_id] = band
        print(f"➕ Added real band {band_id} (BLE: {ble_address})")
        return band

    async def scan_for_real_bands(self, timeout: float = 10.0):
        if not BLE_AVAILABLE:
            print("❌ BLE scanning not available: Install bleak")
            return []

        print(f"🔍 Scanning for VitalLink wristbands ({timeout}s)...")
        devices = await BleakScanner.discover(timeout=timeout)

        found = []
        for device in devices:
            uuids = device.metadata.get("uuids", [])
            if any(uuid.lower() == SERVICE_UUID.lower() for uuid in uuids):
                band_id = (
                    device.name or f"VitalLink-{device.address[-5:].replace(':', '')}"
                )
                self.add_real_band(band_id, device.address)
                found.append(band_id)

        print(f"✓ Found {len(found)} real wristband(s)")
        return found

    def get_available_bands(self) -> List[BaseWristband]:
        return [
            b for b in self.inventory.values() if b.status == WristbandStatus.AVAILABLE
        ]

    def assign_band(
        self, patient_id: str, prefer_real: bool = False
    ) -> Optional[BaseWristband]:
        available = self.get_available_bands()

        if not available:
            print("❌ No wristbands available")
            return None

        if prefer_real:
            real_bands = [b for b in available if b.type == WristbandType.REAL]
            band = real_bands[0] if real_bands else available[0]
        else:
            band = available[0]

        band.assign_to_patient(patient_id)
        return band

    async def start_monitoring(self, band_id: str):
        if band_id not in self.inventory:
            print(f"❌ Band {band_id} not in inventory")
            return

        band = self.inventory[band_id]
        if band_id in self.active_monitoring:
            print(f"⚠️  {band_id} already being monitored")
            return

        task = asyncio.create_task(band.start_monitoring())
        self.active_monitoring[band_id] = task

    async def stop_monitoring(self, band_id: str):
        if band_id in self.active_monitoring:
            task = self.active_monitoring[band_id]
            task.cancel()
            del self.active_monitoring[band_id]

        if band_id in self.inventory:
            await self.inventory[band_id].stop_monitoring()

    async def release_band(self, band_id: str):
        await self.stop_monitoring(band_id)
        if band_id in self.inventory:
            self.inventory[band_id].release()

    def get_status(self) -> dict:
        status_counts = {}
        for status in WristbandStatus:
            status_counts[status.value] = sum(
                1 for b in self.inventory.values() if b.status == status
            )

        return {
            "total_bands": len(self.inventory),
            "real_bands": sum(
                1 for b in self.inventory.values() if b.type == WristbandType.REAL
            ),
            "simulated_bands": sum(
                1 for b in self.inventory.values() if b.type == WristbandType.SIMULATED
            ),
            "status_breakdown": status_counts,
            "active_monitoring": len(self.active_monitoring),
        }

    def print_inventory(self):
        print("\n" + "=" * 80)
        print("WRISTBAND INVENTORY")
        print("=" * 80)

        for band_id, band in self.inventory.items():
            type_symbol = "🔵" if band.type == WristbandType.REAL else "🟢"
            status_str = band.status.value.upper()
            patient_str = f"(Patient: {band.patient_id})" if band.patient_id else ""
            packets_str = (
                f"[{band.packet_count} packets]" if band.packet_count > 0 else ""
            )

            print(
                f"{type_symbol} {band_id:20} | {status_str:15} {patient_str:20} {packets_str}"
            )

        print("=" * 80)
        status = self.get_status()
        print(
            f"Total: {status['total_bands']} | "
            f"Real: {status['real_bands']} | "
            f"Simulated: {status['simulated_bands']} | "
            f"Active: {status['active_monitoring']}"
        )
        print("=" * 80 + "\n")
