# VitalLink Hardware Integration Guide

## 🎯 Overview

This system allows you to seamlessly switch between:
- **Simulated wristbands** - For testing without hardware
- **Real wristbands** - Physical BLE devices
- **Mixed mode** - Use both simultaneously!

## 📁 File Structure

```
vitallink/
├── simulator/
│   ├── wristband_simulator.py     # Original simulator (still works)
│   ├── wristband_manager.py       # NEW: Unified wristband manager
│   ├── config_system.py           # NEW: Configuration management
│   └── main_runner.py             # NEW: Main system runner
├── wristband_config.yaml          # Configuration file (auto-created)
└── backend/
    └── server.py                  # Backend API
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd ~/documents/school/capstone/vitallink-BS/vitallink
source .venv/bin/activate.fish  # or .venv/bin/activate

# Install BLE support (for real hardware)
#uv pip install bleak pyyaml

# Or with pip:
 pip install bleak pyyaml
```

### 2. Create Configuration

```bash
# Create the new files
cd simulator
nano wristband_manager.py     # Copy code from artifact 1
nano config_system.py          # Copy code from artifact 2
nano main_runner.py            # Copy code from artifact 3
```

### 3. Run Configuration Tool

```bash
python config_system.py --inventory
```

This creates `wristband_config.yaml` with default simulated bands.

### 4. Start the System

```bash
# Start backend first
python backend/server.py

# In another terminal, start the wristband system
python simulator/main_runner.py
```

That's it! The system will:
1. ✅ Auto-check in 3 demo patients
2. ✅ Assign wristbands from config
3. ✅ Start monitoring and sending data
4. ✅ Update the dashboard in real-time

---

## 🔧 Configuration File

Edit `wristband_config.yaml`:

```yaml
# VitalLink Wristband Configuration

backend_url: "http://localhost:8000"

# Auto-scan for real wristbands on startup
auto_scan_ble: false
scan_timeout: 10.0

# Simulated Wristbands (for testing)
simulated_bands:
  - band_id: "VitalLink-SIM1"
    profile: "stable"
  
  - band_id: "VitalLink-SIM2"
    profile: "mild_anxiety"
  
  - band_id: "VitalLink-SIM3"
    profile: "deteriorating"

# Real Wristbands (Hardware)
real_bands:
  # Add your real wristbands here:
  # - band_id: "VitalLink-A3B2"
  #   ble_address: "D7:91:3F:9A:12:34"

# Prefer real bands over simulated when available
prefer_real_bands: false
```

---

## 🔍 Finding Real Wristbands

### Scan for BLE Devices

```bash
python config_system.py --scan
```

This will:
1. Scan for 15 seconds
2. Find wristbands advertising the VitalLink service UUID
3. Offer to add them to your config

### Manual BLE Address Discovery

If scanning doesn't work, find addresses manually:

```bash
# On Linux
bluetoothctl
scan on
# Look for devices starting with "VitalLink-"
# Note the MAC address
```

Then add to `wristband_config.yaml`:

```yaml
real_bands:
  - band_id: "VitalLink-A3B2"
    ble_address: "AA:BB:CC:DD:EE:FF"  # Your device's MAC
```

---

## 🎮 Usage Modes

### Mode 1: Automatic (Default)

```bash
python simulator/main_runner.py
```

Automatically:
- Loads wristbands from config
- Checks in demo patients
- Assigns bands
- Starts monitoring

### Mode 2: Interactive

```bash
python simulator/main_runner.py --interactive
```

Menu-driven:
- Manually assign bands
- Scan for new devices
- Release bands
- View inventory

### Mode 3: Configuration Management

```bash
# View inventory
python config_system.py --inventory

# Scan for devices
python config_system.py --scan

# Add simulated band
python config_system.py --add-simulated
```

---

## 🔄 Switching Between Real and Simulated

### Using Only Simulated Bands

```yaml
# wristband_config.yaml
simulated_bands:
  - band_id: "VitalLink-SIM1"
    profile: "stable"
  - band_id: "VitalLink-SIM2"
    profile: "deteriorating"

real_bands: []  # Empty

prefer_real_bands: false
```

### Using Only Real Bands

```yaml
simulated_bands: []  # Empty

real_bands:
  - band_id: "VitalLink-REAL1"
    ble_address: "D7:91:3F:9A:12:34"
  - band_id: "VitalLink-REAL2"
    ble_address: "E1:84:7B:42:56:78"

prefer_real_bands: true
```

### Mixed Mode (1 Real + 2 Simulated)

```yaml
simulated_bands:
  - band_id: "VitalLink-SIM1"
    profile: "stable"
  - band_id: "VitalLink-SIM2"
    profile: "critical"

real_bands:
  - band_id: "VitalLink-REAL1"
    ble_address: "D7:91:3F:9A:12:34"

prefer_real_bands: true  # Use real band first
```

---

## 🏥 Real Hardware Integration

### When You Get Physical Wristbands

1. **Power on the wristbands** (remove from charger)
2. **Scan for them:**
   ```bash
   python config_system.py --scan
   ```
3. **Add to config** when prompted
4. **Set preference:**
   ```yaml
   prefer_real_bands: true
   ```
5. **Run system:**
   ```bash
   python simulator/main_runner.py
   ```

The system will:
- ✅ Automatically connect to real wristbands
- ✅ Subscribe to BLE notifications
- ✅ Decode packets according to your spec
- ✅ Send data to backend
- ✅ Fall back to simulated if real bands unavailable

### Packet Decoding

The `PacketDecoder` class handles your exact packet format:

```python
# Your 16-byte packet structure:
# Byte 0:     version
# Byte 1-2:   sequence number
# Byte 3-6:   timestamp (ms)
# Byte 7:     flags
# Byte 8:     HR (bpm)
# Byte 9:     SpO2 (%)
# Byte 10-11: Temperature * 100
# Byte 12-13: Activity * 100
# Byte 14:    Checksum
# Byte 15:    Reserved
```

No code changes needed - it's already implemented!

---

## 📊 Inventory Management

### View Current Status

```bash
python config_system.py --inventory
```

Output:
```
================================================================================
CONFIGURED WRISTBAND INVENTORY
================================================================================

Simulated Wristbands:
  🟢 VitalLink-SIM1        | Profile: stable
  🟢 VitalLink-SIM2        | Profile: deteriorating

Real Wristbands (Hardware):
  🔵 VitalLink-REAL1       | BLE: D7:91:3F:9A:12:34

================================================================================
Total: 3 wristbands
================================================================================
```

### Add Wristbands

```bash
# Add simulated
python config_system.py --add-simulated

# Add real (after scanning)
python config_system.py --scan
```

### Remove Wristbands

Edit `wristband_config.yaml` and delete the entry.

---

## 🧪 Testing

### Test 1: Simulated Only

```bash
# Use default config (3 simulated bands)
python simulator/main_runner.py
```

Should see 3 patients with updating vitals.

### Test 2: Real Hardware

```bash
# Edit config to add real band
nano wristband_config.yaml

# Run
python simulator/main_runner.py
```

Watch for:
- "🔵 Connecting to real wristband..."
- "✓ Connected to VitalLink-REAL1"
- "✓ Subscribed to notifications"

### Test 3: Mixed Mode

```yaml
# 1 real + 2 simulated
simulated_bands:
  - band_id: "VitalLink-SIM1"
    profile: "stable"
  - band_id: "VitalLink-SIM2"
    profile: "critical"

real_bands:
  - band_id: "VitalLink-REAL1"
    ble_address: "AA:BB:CC:DD:EE:FF"

prefer_real_bands: true
```

First patient gets real band, others get simulated.

---

## 🔧 Troubleshooting

### "Bleak not installed"

```bash
uv pip install bleak
# or
pip install bleak
```

### "No wristbands found during scan"

1. Ensure wristbands are powered (off charger)
2. Check Bluetooth is enabled
3. Try increasing scan timeout in config:
   ```yaml
   scan_timeout: 30.0
   ```

### "Failed to connect to wristband"

1. Check BLE address is correct
2. Ensure wristband is in range
3. Try re-pairing in system Bluetooth settings
4. Check wristband battery

### "Checksum failed"

The real wristband's packet format doesn't match. Check:
1. Byte order (little-endian)
2. Field sizes match your spec
3. Checksum calculation (sum of bytes 0-13 mod 256)

---

## 📝 Next Steps

1. **Test with simulated bands** ✅ (you've done this)
2. **Get physical wristbands** 
3. **Scan and add to config**
4. **Test with 1 real wristband**
5. **Add more real wristbands**
6. **Deploy with full real hardware**

The system is designed to work seamlessly at every stage!

---

## 🎓 For Your Capstone Demo

### Demo Scenario 1: All Simulated (Safe)
- Use 5 simulated wristbands with different profiles
- Show various patient conditions
- Demonstrate deterioration in real-time

### Demo Scenario 2: Mixed (Impressive)
- 1-2 real wristbands you wear
- 3 simulated wristbands
- Show that system handles both seamlessly

### Demo Scenario 3: All Real (Ultimate)
- All physical wristbands
- Live patient simulation
- Production-ready demonstration

---

## 📚 Code Architecture

```
BaseWristband (Abstract)
├── RealWristband (BLE Hardware)
│   ├── Uses Bleak library
│   ├── Connects via BLE
│   ├── Receives notifications
│   └── Decodes packets
│
└── SimulatedWristband (Testing)
    ├── Uses existing simulator
    ├── Generates realistic vitals
    └── Same interface as real

WristbandManager
├── Manages inventory
├── Assigns to patients
├── Starts/stops monitoring
└── Handles both types uniformly
```

The key: **Both types implement the same interface**, so the rest of your system doesn't care which it's using!

---

**Questions? Check the code comments or run with `--help` flag!**
