"""
VitalLink Wristband Simulator & Base Station
Simulates multiple wristbands with realistic vital signs and BLE behavior
"""

import asyncio
import struct
import random
import time
import aiohttp
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import IntFlag

# ============================================================================
# CONSTANTS & FLAGS
# ============================================================================

SERVICE_UUID = "8f5a84f1-22a8-4a4b-9b5f-3fe1d8b2a3a1"
CHAR_UUID = "d3e2c4b7-39b2-4b2a-8d5a-7d2a5e3f1199"

PKT_LEN = 16
PKT_STRUCT = struct.Struct("<B H I B B B h H B B")


class VitalFlags(IntFlag):
    MOTION_ARTIFACT = 1 << 0
    LOW_BATT = 1 << 1
    SENSOR_FAULT = 1 << 2
    ALERT = 1 << 3
    EMERGENCY = 1 << 4


# ============================================================================
# PATIENT CONDITION PROFILES
# ============================================================================


@dataclass
class PatientProfile:
    """Defines baseline vitals and progression patterns"""

    name: str
    hr_base: float  # Baseline heart rate
    hr_variance: float  # Random variation
    spo2_base: float
    spo2_variance: float
    temp_base: float
    temp_variance: float
    deterioration_rate: float  # How fast condition worsens (0-1)
    recovery_rate: float  # Can improve over time


# Preset patient profiles for testing different scenarios
PATIENT_PROFILES = {
    "stable": PatientProfile(
        name="Stable Patient",
        hr_base=72,
        hr_variance=5,
        spo2_base=98,
        spo2_variance=1,
        temp_base=36.8,
        temp_variance=0.2,
        deterioration_rate=0.0,
        recovery_rate=0.0,
    ),
    "mild_anxiety": PatientProfile(
        name="Mild Anxiety",
        hr_base=88,
        hr_variance=8,
        spo2_base=97,
        spo2_variance=1,
        temp_base=37.1,
        temp_variance=0.3,
        deterioration_rate=0.0,
        recovery_rate=0.01,  # Slowly calms down
    ),
    "deteriorating": PatientProfile(
        name="Deteriorating Condition",
        hr_base=85,
        hr_variance=10,
        spo2_base=95,
        spo2_variance=2,
        temp_base=37.5,
        temp_variance=0.4,
        deterioration_rate=0.05,  # Gets worse over time
        recovery_rate=0.0,
    ),
    "critical": PatientProfile(
        name="Critical Patient",
        hr_base=130,
        hr_variance=15,
        spo2_base=88,
        spo2_variance=3,
        temp_base=39.2,
        temp_variance=0.5,
        deterioration_rate=0.02,
        recovery_rate=0.0,
    ),
    "sepsis": PatientProfile(
        name="Sepsis Presentation",
        hr_base=115,
        hr_variance=12,
        spo2_base=92,
        spo2_variance=2,
        temp_base=38.8,
        temp_variance=0.6,
        deterioration_rate=0.08,  # Rapid deterioration
        recovery_rate=0.0,
    ),
}


# ============================================================================
# WRISTBAND SIMULATOR
# ============================================================================


class WristbandSimulator:
    """Simulates a single wristband with realistic vital sign generation"""

    def __init__(self, band_id: str, profile: PatientProfile, patient_id: str = None):
        self.band_id = band_id
        self.profile = profile
        self.patient_id = patient_id or f"P{random.randint(100000, 999999)}"

        # State
        self.seq = 0
        self.start_time = time.time()
        self.battery = 100.0
        self.is_active = True
        self.tier = "NORMAL"

        # Vital signs state (evolves over time)
        self.current_hr = profile.hr_base
        self.current_spo2 = profile.spo2_base
        self.current_temp = profile.temp_base
        self.activity_level = 0.5  # 0-1 scale

        # Time since condition change
        self.time_elapsed = 0

    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate 8-bit checksum"""
        return sum(data[0:14]) & 0xFF

    def _generate_vitals(self) -> tuple:
        """Generate realistic vital signs with progression"""
        self.time_elapsed += 1

        # Apply deterioration/recovery over time
        if self.profile.deterioration_rate > 0:
            self.current_hr += random.uniform(0, self.profile.deterioration_rate * 2)
            self.current_spo2 -= random.uniform(
                0, self.profile.deterioration_rate * 0.5
            )
            self.current_temp += random.uniform(
                0, self.profile.deterioration_rate * 0.1
            )

        if self.profile.recovery_rate > 0:
            # Trend back toward normal
            self.current_hr += (72 - self.current_hr) * self.profile.recovery_rate
            self.current_spo2 += (98 - self.current_spo2) * self.profile.recovery_rate
            self.current_temp += (36.8 - self.current_temp) * self.profile.recovery_rate

        # Add random variance
        hr = self.current_hr + random.gauss(0, self.profile.hr_variance)
        spo2 = self.current_spo2 + random.gauss(0, self.profile.spo2_variance)
        temp = self.current_temp + random.gauss(0, self.profile.temp_variance)

        # Clamp to realistic ranges
        hr = max(30, min(200, hr))
        spo2 = max(70, min(100, spo2))
        temp = max(34.0, min(42.0, temp))

        # Activity varies (simulates patient movement)
        self.activity_level += random.gauss(0, 0.1)
        self.activity_level = max(0, min(2.0, self.activity_level))

        return int(hr), int(spo2), temp, self.activity_level

    def _determine_tier(self, hr: int, spo2: int, temp: float) -> tuple:
        """Determine alert tier based on vitals"""
        flags = 0

        # Battery warning
        if self.battery < 15:
            flags |= VitalFlags.LOW_BATT

        # Check for critical vitals (EMERGENCY)
        if hr > 140 or hr < 45 or spo2 < 88 or temp > 39.5 or temp < 35.0:
            flags |= VitalFlags.EMERGENCY
            tier = "EMERGENCY"
        # Check for concerning vitals (ALERT)
        elif hr > 110 or hr < 50 or spo2 < 92 or temp > 38.3 or temp < 35.5:
            flags |= VitalFlags.ALERT
            tier = "ALERT"
        else:
            tier = "NORMAL"

        return tier, flags

    def generate_packet(self) -> bytes:
        """Generate a complete 16-byte vitals packet"""
        # Generate vitals
        hr, spo2, temp, activity = self._generate_vitals()

        # Determine tier and flags
        tier, flags = self._determine_tier(hr, spo2, temp)
        self.tier = tier

        # Timestamp
        ts_ms = int((time.time() - self.start_time) * 1000)

        # Convert values to packet format
        skin_c_x100 = int(temp * 100)
        act_rms_x100 = int(activity * 100)

        # Pack data (without checksum yet)
        partial_pkt = PKT_STRUCT.pack(
            1,  # version
            self.seq & 0xFFFF,  # sequence
            ts_ms & 0xFFFFFFFF,  # timestamp
            flags,
            hr,
            spo2,
            skin_c_x100,
            act_rms_x100,
            0,  # checksum placeholder
            0,  # reserved
        )

        # Calculate and insert checksum
        checksum = self._calculate_checksum(partial_pkt)
        packet = bytearray(partial_pkt)
        packet[14] = checksum

        # Update state
        self.seq += 1
        self.battery = max(0, self.battery - 0.001)  # Slow drain

        return bytes(packet)

    def get_status(self) -> dict:
        """Get current wristband status"""
        return {
            "band_id": self.band_id,
            "patient_id": self.patient_id,
            "profile": self.profile.name,
            "tier": self.tier,
            "battery": round(self.battery, 1),
            "seq": self.seq,
            "active": self.is_active,
        }


# ============================================================================
# BASE STATION SIMULATOR
# ============================================================================


class BaseStationSimulator:
    """Simulates the base station that manages multiple wristbands"""

    def __init__(self):
        self.wristbands: Dict[str, WristbandSimulator] = {}
        self.running = False
        self.packet_log: List[dict] = []

    def add_wristband(
        self, band_id: str, profile_name: str = "stable", patient_id: str = None
    ) -> WristbandSimulator:
        """Add a new wristband to the simulation"""
        profile = PATIENT_PROFILES.get(profile_name, PATIENT_PROFILES["stable"])
        band = WristbandSimulator(band_id, profile, patient_id)
        self.wristbands[band_id] = band
        print(f"[BASE] Added wristband {band_id} with profile '{profile.name}'")
        return band

    def remove_wristband(self, band_id: str):
        """Remove a wristband (patient discharged)"""
        if band_id in self.wristbands:
            del self.wristbands[band_id]
            print(f"[BASE] Removed wristband {band_id}")

    def decode_packet(self, band_id: str, data: bytes) -> dict:
        """Decode a packet and return structured data"""
        if len(data) != PKT_LEN:
            return {"error": "Invalid packet length"}

        # Verify checksum
        checksum_calc = sum(data[0:14]) & 0xFF
        if checksum_calc != data[14]:
            return {"error": "Checksum failed"}

        # Unpack
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

        # Determine tier
        tier = (
            "EMERGENCY"
            if (flags & VitalFlags.EMERGENCY)
            else "ALERT"
            if (flags & VitalFlags.ALERT)
            else "NORMAL"
        )

        # Build flag list
        flag_list = []
        if flags & VitalFlags.MOTION_ARTIFACT:
            flag_list.append("MOTION_ARTIFACT")
        if flags & VitalFlags.LOW_BATT:
            flag_list.append("LOW_BATT")
        if flags & VitalFlags.SENSOR_FAULT:
            flag_list.append("SENSOR_FAULT")
        if flags & VitalFlags.ALERT:
            flag_list.append("ALERT")
        if flags & VitalFlags.EMERGENCY:
            flag_list.append("EMERGENCY")

        return {
            "band_id": band_id,
            "patient_id": self.wristbands[band_id].patient_id
            if band_id in self.wristbands
            else "UNKNOWN",
            "timestamp": time.time(),
            "ver": ver,
            "seq": seq,
            "ts_ms": ts_ms,
            "tier": tier,
            "flags": flag_list,
            "hr_bpm": hr_bpm,
            "spo2": spo2,
            "temp_c": skin_c_x100 / 100.0,
            "activity": act_rms_x100 / 100.0,
            "checksum": f"0x{checksum:02X}",
        }

    async def send_to_backend(self, decoded_data: dict):
        """Send vitals data to backend API"""
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    "http://localhost:8000/api/vitals", json=decoded_data
                )
        except Exception as e:
            # Silently fail if backend not available
            pass

    async def simulate_band_transmission(self, band_id: str):
        """Simulate continuous transmission from one wristband"""
        band = self.wristbands[band_id]

        while self.running and band.is_active and band_id in self.wristbands:
            # Generate packet
            packet = band.generate_packet()

            # Decode for logging
            decoded = self.decode_packet(band_id, packet)

            # Determine send interval based on tier
            if band.tier == "EMERGENCY":
                interval = 1.0  # 1 Hz
            elif band.tier == "ALERT":
                interval = 1.0  # 1 Hz
            else:
                interval = 60.0  # Every 60s for NORMAL

            # Log packet
            self.packet_log.append(decoded)

            # Send to backend API
            await self.send_to_backend(decoded)

            # Print to console
            tier_symbol = (
                "🔴"
                if band.tier == "EMERGENCY"
                else "🟡"
                if band.tier == "ALERT"
                else "🟢"
            )
            print(
                f"{tier_symbol} [{band_id}] {band.patient_id} | "
                f"HR={decoded['hr_bpm']} SpO2={decoded['spo2']}% "
                f"Temp={decoded['temp_c']:.1f}°C | {band.tier} | "
                f"Seq={decoded['seq']}"
            )

            await asyncio.sleep(interval)

    async def run(self):
        """Start the base station simulation"""
        self.running = True
        print("[BASE] Starting base station simulation...")
        print("=" * 80)

        # Create tasks for each wristband
        tasks = [
            asyncio.create_task(self.simulate_band_transmission(band_id))
            for band_id in self.wristbands.keys()
        ]

        # Run until stopped
        await asyncio.gather(*tasks, return_exceptions=True)

    def stop(self):
        """Stop the simulation"""
        self.running = False
        print("\n[BASE] Stopping base station...")

    def get_summary(self) -> dict:
        """Get current status of all wristbands"""
        return {
            "total_bands": len(self.wristbands),
            "active_bands": sum(1 for b in self.wristbands.values() if b.is_active),
            "tiers": {
                "EMERGENCY": sum(
                    1 for b in self.wristbands.values() if b.tier == "EMERGENCY"
                ),
                "ALERT": sum(1 for b in self.wristbands.values() if b.tier == "ALERT"),
                "NORMAL": sum(
                    1 for b in self.wristbands.values() if b.tier == "NORMAL"
                ),
            },
            "total_packets": len(self.packet_log),
        }


# ============================================================================
# AUTO CHECK-IN FUNCTION
# ============================================================================


async def auto_checkin_patients():
    """Automatically check in patients via API"""
    patients = [
        {
            "firstName": "John",
            "lastName": "Smith",
            "dob": "1985-03-15",
            "symptoms": ["Chest Pain"],
            "severity": "mild",
        },
        {
            "firstName": "Sarah",
            "lastName": "Johnson",
            "dob": "1990-07-22",
            "symptoms": ["Fever", "Difficulty Breathing"],
            "severity": "moderate",
        },
        {
            "firstName": "Michael",
            "lastName": "Chen",
            "dob": "1978-11-05",
            "symptoms": ["Severe Headache"],
            "severity": "severe",
        },
    ]

    assigned = []
    try:
        async with aiohttp.ClientSession() as session:
            for patient_data in patients:
                async with session.post(
                    "http://localhost:8000/api/checkin", json=patient_data
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        assigned.append(data)
                        print(
                            f"[CHECKIN] {patient_data['firstName']} {patient_data['lastName']} → {data['patient_id']} / {data['band_id']}"
                        )
    except Exception as e:
        print(f"[ERROR] Could not check in patients: {e}")
        print("[INFO] Make sure backend is running at http://localhost:8000")
        return []

    return assigned


# ============================================================================
# MAIN - CONTINUOUS MODE
# ============================================================================


async def continuous_mode():
    """Run simulator continuously, sending data to backend"""
    print("\n" + "=" * 80)
    print("CONTINUOUS MODE: Sending data to backend at http://localhost:8000")
    print("=" * 80 + "\n")

    # Auto check-in patients first
    print("Checking in patients...")
    assigned = await auto_checkin_patients()

    if not assigned:
        print("\n[ERROR] No patients checked in. Is the backend running?")
        print("[INFO] Start backend with: python backend/server.py")
        return

    print()

    base = BaseStationSimulator()

    # Add wristbands using the assigned IDs
    profiles = ["stable", "mild_anxiety", "deteriorating"]
    for i, assignment in enumerate(assigned):
        profile = profiles[i] if i < len(profiles) else "stable"
        base.add_wristband(assignment["band_id"], profile, assignment["patient_id"])

    print("\nPress Ctrl+C to stop\n")
    print("=" * 80)

    # Run indefinitely
    try:
        await base.run()
    except KeyboardInterrupt:
        base.stop()
        print("\n" + "=" * 80)
        print("SUMMARY:")
        print(base.get_summary())
        print("=" * 80)
        print("\n[BASE] Simulator stopped by user")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                     VitalLink Wristband Simulator                        ║
║                  Emergency Department Monitoring System                  ║
╚══════════════════════════════════════════════════════════════════════════╝

Available Patient Profiles:
  - stable: Normal vitals, no deterioration
  - mild_anxiety: Elevated HR, improves over time
  - deteriorating: Gradually worsening condition
  - critical: Severe vitals, triggers emergency tier
  - sepsis: Rapid deterioration pattern
""")

    # Run continuous mode
    asyncio.run(continuous_mode())
