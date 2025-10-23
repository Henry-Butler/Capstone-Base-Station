# VitalLink - Emergency Room Patient Monitoring System

**A comprehensive IoT-based patient monitoring system using smart wristbands for emergency department triage and real-time vital signs tracking.**

---

## 🎯 Project Overview

VitalLink is an intelligent ER patient monitoring system that uses smart wristbands to continuously track patient vital signs and automatically prioritize care based on real-time health data. The system supports both physical BLE wristbands and simulated devices for testing and demonstration.

### Key Features

- ✅ **Real-time vital sign monitoring** (Heart Rate, SpO₂, Temperature, Activity)
- ✅ **Automatic patient prioritization** based on condition severity
- ✅ **Three-tier alert system** (Normal, Alert, Emergency)
- ✅ **Self-service check-in kiosk** for patient registration
- ✅ **Staff monitoring dashboard** with live updates
- ✅ **Mixed real/simulated wristbands** for flexible testing
- ✅ **Bluetooth Low Energy (BLE)** communication protocol
- ✅ **Dynamic queue management** with priority scoring

---

## 📁 Project Structure

```
vitallink/
├── backend/                    # Backend API Server
│   └── server.py              # FastAPI REST API + WebSocket server
│
├── simulator/                  # Wristband Management System
│   ├── wristband_simulator.py # Original standalone simulator
│   ├── wristband_manager.py   # Unified wristband manager (real + simulated)
│   ├── config_system.py       # Configuration management & CLI tools
│   ├── main_runner.py         # Main system orchestrator
│   └── wristband_config.yaml  # Wristband inventory configuration
│
├── frontend/                   # Web User Interfaces
│   ├── dashboard/             # Staff Monitoring Dashboard (React + Vite)
│   │   ├── src/
│   │   │   ├── App.jsx       # Main dashboard component
│   │   │   └── index.css     # Tailwind CSS imports
│   │   ├── index.html        # HTML entry point
│   │   └── package.json      # NPM dependencies
│   │
│   └── kiosk/                 # Patient Check-in Kiosk (React + Vite)
│       ├── src/
│       │   ├── App.jsx       # Check-in interface component
│       │   └── index.css     # Tailwind CSS imports
│       ├── index.html        # HTML entry point
│       └── package.json      # NPM dependencies
│
├── tests/                     # Test Suite
│   └── test_suite.py         # Comprehensive system tests
│
├── logs/                      # System Logs (auto-generated)
│   ├── backend.log
│   ├── wristbands.log
│   ├── dashboard.log
│   └── kiosk.log
│
├── .venv/                     # Python virtual environment (UV)
├── requirements.txt           # Python dependencies
├── link-start.sh        # Master startup script
├── stop_everything.sh         # Master shutdown script
└── README.md                  # This file
```

---

## 🔄 System Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PATIENT CHECK-IN FLOW                        │
└─────────────────────────────────────────────────────────────────┘

   1. Patient arrives at ER
          ↓
   2. Self-service kiosk (http://localhost:5174)
      - Enter personal info
      - Select symptoms
      - Rate severity
          ↓
   3. Backend API assigns patient ID + wristband ID
          ↓
   4. Wristband Manager detects new patient
          ↓
   5. Auto-assigns wristband (prefers real over simulated)
          ↓
   6. Starts monitoring vital signs


┌─────────────────────────────────────────────────────────────────┐
│                    DATA MONITORING FLOW                         │
└─────────────────────────────────────────────────────────────────┘

   Wristband (Real BLE or Simulated)
          ↓
   Generates 16-byte packet every 1-60 seconds
   [ver][seq][timestamp][flags][hr][spo2][temp][activity][checksum]
          ↓
   Wristband Manager decodes packet
          ↓
   Sends to Backend API (/api/vitals)
          ↓
   Backend processes & stores data
          ↓
   WebSocket broadcasts to connected clients
          ↓
   Staff Dashboard updates in real-time (http://localhost:5173)
          ↓
   Priority queue recalculates
          ↓
   Emergency alerts triggered if thresholds exceeded
```

---

## 📄 File Purposes

### Backend (`backend/`)

#### `server.py`

**Purpose:** Core backend API server  
**Technology:** FastAPI + Uvicorn  
**Key Functions:**

- Patient registration and management
- Vital signs data ingestion and storage
- Priority queue calculation algorithm
- WebSocket real-time updates
- RESTful API endpoints for all operations

**Main Endpoints:**

- `POST /api/checkin` - Register new patient
- `POST /api/vitals` - Receive vital signs data
- `GET /api/queue` - Get prioritized patient queue
- `GET /api/stats` - System statistics
- `GET /api/wristband-details` - Wristband inventory
- `POST /api/patients/{id}/discharge` - Discharge patient
- `WS /ws` - WebSocket for real-time updates

---

### Wristband System (`simulator/`)

#### `wristband_simulator.py`

**Purpose:** Original standalone wristband simulator  
**Technology:** Python asyncio  
**Key Functions:**

- Generates realistic vital sign data
- Simulates 5 patient condition profiles (stable, deteriorating, critical, etc.)
- Creates proper 16-byte BLE packets with checksums
- Can run independently for testing

**When to use:** Quick testing without the full system

---

#### `wristband_manager.py`

**Purpose:** Unified wristband management system  
**Technology:** Python asyncio + Bleak (for BLE)  
**Key Functions:**

- **Manages both real and simulated wristbands** with identical interface
- Scans for real BLE devices
- Decodes 16-byte packets according to spec
- Handles wristband inventory (available, assigned, in-use)
- Auto-assigns wristbands to new patients

**Key Classes:**

- `BaseWristband` - Abstract interface for all wristbands
- `RealWristband` - Connects to physical BLE devices
- `SimulatedWristband` - Software simulation for testing
- `WristbandManager` - Central inventory manager
- `PacketDecoder` - Decodes 16-byte BLE packets

---

#### `config_system.py`

**Purpose:** Configuration management and CLI tools  
**Technology:** Python + PyYAML  
**Key Functions:**

- Loads wristband inventory from YAML config
- Command-line tools for managing wristbands
- BLE device scanning and discovery
- Add/remove wristbands without code changes

**CLI Commands:**

```bash
python config_system.py --inventory      # Show configured wristbands
python config_system.py --scan           # Scan for real BLE devices
python config_system.py --add-simulated  # Add a simulated wristband
```

---

#### `main_runner.py`

**Purpose:** Main system orchestrator  
**Technology:** Python asyncio  
**Key Functions:**

- **Auto-detects new patient check-ins** from backend
- **Auto-assigns wristbands** (prefers real, falls back to simulated)
- Creates emergency simulated bands if inventory depleted
- Reports wristband status to backend every 10 seconds
- Manages lifecycle of all wristband monitoring tasks

**This is the heart of the wristband system!**

---

#### `wristband_config.yaml`

**Purpose:** Wristband inventory configuration  
**Technology:** YAML configuration file  
**Structure:**

```yaml
backend_url: "http://localhost:8000"
auto_scan_ble: true                    # Scan for real bands on startup
prefer_real_bands: true                # Use real bands first

simulated_bands:                       # MOCK wristbands for testing
  - band_id: "MOCK-SIM1"
    profile: "stable"
  
real_bands:                            # Physical BLE devices
  - band_id: "VitalLink-A3B2"
    ble_address: "AA:BB:CC:DD:EE:FF"
```

**Edit this file** to add/remove wristbands without touching code!

---

### Frontend (`frontend/`)

#### `dashboard/src/App.jsx`

**Purpose:** Staff monitoring dashboard  
**Technology:** React + Vite + Tailwind CSS  
**Key Features:**

- **Patients Tab:**
  - Real-time vital signs display
  - Color-coded alert tiers (🟢 Normal, 🟡 Alert, 🔴 Emergency)
  - Priority queue ordering
  - Filter by tier
  - Discharge patients
- **Wristbands Tab:**
  - Inventory management view
  - Real vs simulated differentiation (🔵 vs 🟢)
  - Click wristband to see **raw 16-byte packet hex dump**
  - Decoded packet fields
  - Flag visualization (emergency, alert, battery, etc.)

**Port:** <http://localhost:5173>

---

#### `kiosk/src/App.jsx`

**Purpose:** Patient self-service check-in  
**Technology:** React + Vite + Tailwind CSS  
**Key Features:**

- User-friendly check-in wizard
- Symptom selection
- Severity rating
- Wristband assignment confirmation
- Next steps guidance

**Port:** <http://localhost:5174>

---

### Tests (`tests/`)

#### `test_suite.py`

**Purpose:** Comprehensive system testing  
**Technology:** Python asyncio  
**Test Coverage:**

- Patient data validation
- Packet generation and checksums
- Tier classification logic
- Priority score calculation
- Simulator stability
- Deterioration detection
- Transmission timing

**Run with:** `python tests/test_suite.py`

---

### Scripts

#### `link-start.sh`

**Purpose:** Master startup script - **ONE COMMAND TO START ENTIRE SYSTEM**  
**What it does:**

1. ✅ Activates Python virtual environment
2. ✅ Starts backend API server (port 8000)
3. ✅ Starts wristband management system
4. ✅ Starts staff dashboard (port 5173)
5. ✅ Starts check-in kiosk (port 5174)
6. ✅ Creates logs for all services

**Usage:** `./start_everything.sh`

---

#### `stop_everything.sh`

**Purpose:** Clean shutdown of all services  
**What it does:**

1. Stops backend server
2. Stops wristband system
3. Stops frontend dev servers
4. Cleans up PID files

**Usage:** `./stop_everything.sh`

---

## 🔗 How Components Connect

### 1. Patient Check-In Flow

```
Kiosk (React) 
    → POST /api/checkin 
    → Backend creates patient record
    → Main Runner detects new patient
    → Wristband Manager assigns band
    → Monitoring starts
```

### 2. Vital Signs Data Flow

```
Wristband (Real or Simulated)
    → Generates 16-byte BLE packet
    → Wristband Manager decodes
    → POST /api/vitals to Backend
    → Backend updates patient record
    → WebSocket broadcasts to Dashboard
    → Dashboard displays live data
```

### 3. Priority Queue Flow

```
Backend calculates priority scores every 3 seconds based on:
    - Tier (Emergency=100, Alert=50, Normal=0)
    - Wait time (increases after 30 min)
    - Initial severity (severe=20, moderate=10, mild=5)
    - Vital sign abnormalities
    → Queue reordered
    → Dashboard fetches updated queue
    → Patients displayed in priority order
```

### 4. Wristband Inventory Flow

```
Main Runner reports inventory every 10 seconds:
    → POST /api/wristband-details (full inventory + packet data)
    → Backend caches data
    → Dashboard fetches wristband details
    → Wristbands tab displays inventory
    → Click wristband → show raw packet hex
```

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend | FastAPI + Uvicorn | REST API + WebSocket server |
| Wristband System | Python asyncio + Bleak | BLE communication + simulation |
| Frontend | React + Vite | Fast, modern UI development |
| Styling | Tailwind CSS | Utility-first responsive design |
| Icons | Lucide React | Beautiful, consistent icons |
| BLE Protocol | Bluetooth Low Energy | Wireless communication with wristbands |
| Data Format | 16-byte binary packets | Efficient, spec-compliant data transmission |
| Configuration | YAML | Human-readable wristband inventory |
| Virtual Env | UV (optional) or venv | Python dependency isolation |

---

## 🚀 Quick Start

### 1. Start Everything

```bash
./start_everything.sh
```

### 2. Access Interfaces

- **Staff Dashboard:** <http://localhost:5173>
- **Check-in Kiosk:** <http://localhost:5174>
- **API Documentation:** <http://localhost:8000/docs>

### 3. Test the System

1. Open kiosk, check in a patient
2. Watch dashboard - patient appears with assigned wristband
3. Click "Wristbands" tab to see inventory
4. Click any wristband to view raw packet data

### 4. Stop Everything

```bash
./stop_everything.sh
```

---

## 🔧 Configuration

### Adding Simulated Wristbands

Edit `simulator/wristband_config.yaml`:

```yaml
simulated_bands:
  - band_id: "MOCK-SIM4"
    profile: "critical"
```

### Adding Real Wristbands

1. Scan for devices:

```bash
   python simulator/config_system.py --scan
```

2. Add to config when prompted, or manually:

```yaml
   real_bands:
     - band_id: "VitalLink-A3B2"
       ble_address: "AA:BB:CC:DD:EE:FF"
```

### Changing Priority Preferences

```yaml
prefer_real_bands: true   # Use real bands first
auto_scan_ble: true       # Scan on startup
```

---

## 📊 BLE Packet Structure

VitalLink wristbands transmit 16-byte packets over BLE:

| Bytes | Field | Type | Description |
|-------|-------|------|-------------|
| 0 | Version | uint8 | Protocol version (0x01) |
| 1-2 | Sequence | uint16 | Packet counter |
| 3-6 | Timestamp | uint32 | Milliseconds since boot |
| 7 | Flags | uint8 | Status bits (emergency, alert, battery, etc.) |
| 8 | Heart Rate | uint8 | BPM |
| 9 | SpO₂ | uint8 | Oxygen saturation % |
| 10-11 | Temperature | int16 | Celsius × 100 (3650 = 36.50°C) |
| 12-13 | Activity | uint16 | RMS × 100 |
| 14 | Checksum | uint8 | Sum of bytes 0-13 mod 256 |
| 15 | Reserved | uint8 | Future use |

**Example Packet:**

```
01 2A 00 87 D6 12 00 02 4E 61 3D 0E B4 00 BA 00
```

**View in Dashboard:** Click any wristband in the Wristbands tab!

---

## 📝 Development Notes

### For Hardware Integration

When you get physical wristbands:

1. Power on wristbands (remove from charger)
2. Run: `python simulator/config_system.py --scan`
3. Add discovered bands to config
4. Set `prefer_real_bands: true`
5. Restart system - real bands will be used automatically!

### Mixed Mode Testing

You can run **1 real + 5 simulated** simultaneously:

- Real wristband: For actual patient (you wearing it)
- Simulated: For demo patients with various conditions

### Packet Debugging

View raw packets in real-time:

1. Dashboard → Wristbands tab
2. Click any active wristband
3. See hex dump + decoded fields
4. Perfect for verifying hardware compliance!

---

## 🎓 For Capstone Presentation

### Demo Flow

1. **Start system:** `./start_everything.sh`
2. **Show kiosk:** Check in yourself as a patient
3. **Show dashboard:** You appear in queue with assigned wristband
4. **Show wristbands tab:** Your band is listed as "in use"
5. **Click your wristband:** Show raw 16-byte packet matching spec
6. **Add mock patient:** Check in another via kiosk
7. **Show auto-assignment:** System assigns MOCK band automatically
8. **Show priority queue:** Emergency patients automatically moved to top

### Key Talking Points

- ✅ Real-time vital sign monitoring
- ✅ Automatic triage prioritization
- ✅ Seamless real/simulated wristband mixing
- ✅ Production-ready BLE protocol implementation
- ✅ Complete end-to-end system
- ✅ Scalable microservice architecture

---

## 📚 Additional Resources

- **BLE Protocol Details:** See uploaded specification document
- **API Documentation:** <http://localhost:8000/docs> (when running)
- **Wristband Inventory:** `python simulator/config_system.py --inventory`
- **System Logs:** `tail -f logs/*.log`

---

## 🏆 Credits

**VitalLink Emergency Room Patient Monitoring System**  
Capstone Project - 2025  
**Developer:** Mai(Andrew Hartley)
**Institution:** [Northeastern University]

---

## 📄 License

Educational/Capstone Project
