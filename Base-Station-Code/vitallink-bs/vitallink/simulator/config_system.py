"""
VitalLink Configuration System
Easy configuration for managing wristband inventory
"""

import yaml
import json
from pathlib import Path

# ============================================================================
# CONFIGURATION FILE EXAMPLE
# ============================================================================

EXAMPLE_CONFIG = """
# VitalLink Wristband Configuration
# Edit this file to manage your wristband inventory

# Backend API URL
backend_url: "http://localhost:8000"

# Auto-scan for real wristbands on startup
auto_scan_ble: false
scan_timeout: 10.0

# Simulated Wristbands
# Add as many as you need for testing
simulated_bands:
  - band_id: "VitalLink-SIM1"
    profile: "stable"
  
  - band_id: "VitalLink-SIM2"
    profile: "mild_anxiety"
  
  - band_id: "VitalLink-SIM3"
    profile: "deteriorating"

# Real Wristbands (Hardware)
# Add BLE addresses of your physical wristbands
# You can find these by running: python -m wristband_manager --scan
real_bands:
  # Example (uncomment and edit when you have real hardware):
  # - band_id: "VitalLink-A3B2"
  #   ble_address: "D7:91:3F:9A:12:34"
  #
  # - band_id: "VitalLink-7B42"
  #   ble_address: "E1:84:7B:42:56:78"

# Default preference when assigning bands
prefer_real_bands: false  # Set to true to use real bands first

# Patient profiles for simulated bands
# Options: stable, mild_anxiety, deteriorating, critical, sepsis
default_profile: "stable"
"""


class WristbandConfig:
    """Configuration manager for wristbands"""

    def __init__(self, config_path: str = "wristband_config.yaml"):
        self.config_path = Path(config_path)
        self.config = {}

        if not self.config_path.exists():
            self.create_default_config()

        self.load()

    def create_default_config(self):
        """Create default configuration file"""
        print(f"Creating default config at {self.config_path}")
        with open(self.config_path, "w") as f:
            f.write(EXAMPLE_CONFIG)

    def load(self):
        """Load configuration from file"""
        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f) or {}
            print(f"✓ Loaded configuration from {self.config_path}")
        except Exception as e:
            print(f"⚠️  Could not load config: {e}")
            print("Using default configuration")
            self.config = {}

    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)

    def get_simulated_bands(self):
        """Get list of simulated bands from config"""
        return self.config.get("simulated_bands", [])

    def get_real_bands(self):
        """Get list of real bands from config"""
        return self.config.get("real_bands", [])

    def add_discovered_band(self, band_id: str, ble_address: str):
        """Add a discovered real band to config"""
        if "real_bands" not in self.config:
            self.config["real_bands"] = []

        # Check if already exists
        for band in self.config["real_bands"]:
            if band.get("ble_address") == ble_address:
                return

        self.config["real_bands"].append(
            {"band_id": band_id, "ble_address": ble_address}
        )

        self.save()
        print(f"✓ Added {band_id} to configuration")

    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, "w") as f:
                yaml.safe_dump(
                    self.config, f, default_flow_style=False, sort_keys=False
                )
            print(f"✓ Saved configuration to {self.config_path}")
        except Exception as e:
            print(f"❌ Failed to save config: {e}")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================


async def cli_scan():
    """CLI: Scan for real wristbands"""
    from wristband_manager import WristbandManager

    print("Scanning for VitalLink wristbands...")
    manager = WristbandManager()
    config = WristbandConfig()

    found = await manager.scan_for_real_bands(timeout=15.0)

    if found:
        print(f"\nFound {len(found)} wristband(s):")
        for band_id in found:
            band = manager.inventory[band_id]
            if hasattr(band, "ble_address"):
                print(f"  {band_id}: {band.ble_address}")

                # Ask to add to config
                response = input(f"Add {band_id} to config? (y/n): ")
                if response.lower() == "y":
                    config.add_discovered_band(band_id, band.ble_address)
    else:
        print("No wristbands found")
        print("\nTroubleshooting:")
        print("  1. Make sure wristbands are powered on")
        print("  2. Remove wristbands from chargers")
        print("  3. Ensure Bluetooth is enabled on this computer")


def cli_inventory():
    """CLI: Show current inventory"""
    config = WristbandConfig()

    print("\n" + "=" * 80)
    print("CONFIGURED WRISTBAND INVENTORY")
    print("=" * 80)

    print("\nSimulated Wristbands:")
    simulated = config.get_simulated_bands() or []
    if simulated:
        for band in simulated:
            print(f"  🟢 {band['band_id']:20} | Profile: {band['profile']}")
    else:
        print("  (none configured)")

    print("\nReal Wristbands (Hardware):")
    real = config.get_real_bands() or []
    if real:
        for band in real:
            print(f"  🔵 {band['band_id']:20} | BLE: {band['ble_address']}")
    else:
        print("  (none configured)")

    print("\n" + "=" * 80)
    print(f"Total: {len(simulated) + len(real)} wristbands")
    print("=" * 80 + "\n")


def cli_add_simulated():
    """CLI: Add a simulated wristband"""
    config = WristbandConfig()

    print("\nAdd Simulated Wristband")
    print("-" * 40)

    band_id = input("Band ID (e.g., VitalLink-SIM4): ")

    print("\nAvailable profiles:")
    print("  1. stable - Normal vitals")
    print("  2. mild_anxiety - Elevated HR")
    print("  3. deteriorating - Gradually worsening")
    print("  4. critical - Severe vitals")
    print("  5. sepsis - Rapid deterioration")

    profile_choice = input("\nSelect profile (1-5): ")
    profiles = ["stable", "mild_anxiety", "deteriorating", "critical", "sepsis"]
    profile = (
        profiles[int(profile_choice) - 1]
        if profile_choice.isdigit() and 1 <= int(profile_choice) <= 5
        else "stable"
    )

    if "simulated_bands" not in config.config:
        config.config["simulated_bands"] = []

    config.config["simulated_bands"].append({"band_id": band_id, "profile": profile})

    config.save()
    print(f"\n✓ Added {band_id} ({profile})")


if __name__ == "__main__":
    import argparse
    import sys

    # Check if yaml is installed
    try:
        import yaml
    except ImportError:
        print("❌ PyYAML not installed. Install with: pip install pyyaml")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="VitalLink Wristband Configuration Tool"
    )
    parser.add_argument("--scan", action="store_true", help="Scan for real wristbands")
    parser.add_argument(
        "--inventory", action="store_true", help="Show configured inventory"
    )
    parser.add_argument(
        "--add-simulated", action="store_true", help="Add a simulated wristband"
    )

    args = parser.parse_args()

    if args.scan:
        import asyncio

        asyncio.run(cli_scan())
    elif args.inventory:
        cli_inventory()
    elif args.add_simulated:
        cli_add_simulated()
    else:
        parser.print_help()
