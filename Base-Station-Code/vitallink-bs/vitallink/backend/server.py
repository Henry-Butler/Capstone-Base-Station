"""
VitalLink Backend API
FastAPI server for managing patients, wristbands, and real-time data
"""

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import asyncio
import json
from collections import defaultdict

# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("=" * 80)
    print("VitalLink Backend API Started")
    print("=" * 80)
    print("API Documentation: http://localhost:8000/docs")
    print("WebSocket Endpoint: ws://localhost:8000/ws")
    print("=" * 80)
    yield
    # Shutdown
    print("\nVitalLink Backend API Shutting Down")


# ============================================================================
# APP INITIALIZATION
# ============================================================================

app = FastAPI(title="VitalLink API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DATA MODELS
# ============================================================================


class PatientCheckIn(BaseModel):
    firstName: str
    lastName: str
    dob: str
    symptoms: List[str]
    severity: str


class Patient(BaseModel):
    patient_id: str
    band_id: str
    first_name: str
    last_name: str
    dob: str
    symptoms: List[str]
    severity: str
    check_in_time: datetime
    current_tier: str = "NORMAL"
    last_vitals: Optional[dict] = None
    is_active: bool = True


class VitalsData(BaseModel):
    band_id: str
    patient_id: str
    timestamp: float
    tier: str
    hr_bpm: int
    spo2: int
    temp_c: float
    activity: float
    flags: List[str]
    seq: int


class QueuePosition(BaseModel):
    patient_id: str
    band_id: str
    name: str
    tier: str
    priority_score: float
    wait_time_minutes: int
    last_hr: int
    last_spo2: int
    last_temp: float


# ============================================================================
# IN-MEMORY STORAGE
# ============================================================================

patients_db: Dict[str, Patient] = {}
vitals_history: Dict[str, List[VitalsData]] = defaultdict(list)
available_bands = [
    f"VitalLink-{hex(i)[2:].upper().zfill(4)}" for i in range(0x1000, 0x2000)
]
active_websockets: List[WebSocket] = []

# Wristband details cache
wristband_details_cache = {}

# ============================================================================
# PRIORITY ALGORITHM
# ============================================================================


def calculate_priority_score(patient: Patient) -> float:
    score = 0.0

    tier_scores = {"EMERGENCY": 100, "ALERT": 50, "NORMAL": 0}
    score += tier_scores.get(patient.current_tier, 0)

    wait_minutes = (datetime.now() - patient.check_in_time).total_seconds() / 60
    if wait_minutes > 30:
        score += (wait_minutes - 30) * 0.5
    elif wait_minutes > 60:
        score += (wait_minutes - 60) * 1.0

    severity_scores = {"severe": 20, "moderate": 10, "mild": 5}
    score += severity_scores.get(patient.severity, 0)

    if patient.last_vitals:
        hr = patient.last_vitals.get("hr_bpm", 75)
        spo2 = patient.last_vitals.get("spo2", 98)
        temp = patient.last_vitals.get("temp_c", 37.0)

        if hr > 110 or hr < 50:
            score += 10
        if hr > 140 or hr < 40:
            score += 30

        if spo2 < 92:
            score += 15
        if spo2 < 88:
            score += 40

        if temp > 38.5:
            score += 15
        if temp > 39.5:
            score += 25

    return score


# ============================================================================
# API ENDPOINTS
# ============================================================================


@app.get("/")
async def root():
    return {
        "message": "VitalLink Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }


@app.post("/api/checkin")
async def check_in_patient(data: PatientCheckIn):
    if not available_bands:
        raise HTTPException(status_code=503, detail="No wristbands available")

    patient_id = f"P{len(patients_db) + 100001}"
    band_id = available_bands.pop(0)

    patient = Patient(
        patient_id=patient_id,
        band_id=band_id,
        first_name=data.firstName,
        last_name=data.lastName,
        dob=data.dob,
        symptoms=data.symptoms,
        severity=data.severity,
        check_in_time=datetime.now(),
        current_tier="NORMAL",
    )

    patients_db[patient_id] = patient

    await broadcast_update({"type": "patient_added", "patient": patient.dict()})

    return {
        "patient_id": patient_id,
        "band_id": band_id,
        "message": "Check-in successful",
    }


@app.post("/api/vitals")
async def receive_vitals(data: VitalsData):
    patient_id = data.patient_id

    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient = patients_db[patient_id]
    patient.current_tier = data.tier
    patient.last_vitals = data.dict()

    vitals_history[patient_id].append(data)
    if len(vitals_history[patient_id]) > 1000:
        vitals_history[patient_id] = vitals_history[patient_id][-1000:]

    await broadcast_update(
        {"type": "vitals_update", "patient_id": patient_id, "vitals": data.dict()}
    )

    return {"status": "received"}


@app.get("/api/queue")
async def get_queue():
    active_patients = [p for p in patients_db.values() if p.is_active]

    queue = []
    for patient in active_patients:
        priority_score = calculate_priority_score(patient)
        wait_minutes = int(
            (datetime.now() - patient.check_in_time).total_seconds() / 60
        )

        queue.append(
            QueuePosition(
                patient_id=patient.patient_id,
                band_id=patient.band_id,
                name=f"{patient.first_name} {patient.last_name}",
                tier=patient.current_tier,
                priority_score=priority_score,
                wait_time_minutes=wait_minutes,
                last_hr=patient.last_vitals.get("hr_bpm", 0)
                if patient.last_vitals
                else 0,
                last_spo2=patient.last_vitals.get("spo2", 0)
                if patient.last_vitals
                else 0,
                last_temp=patient.last_vitals.get("temp_c", 0)
                if patient.last_vitals
                else 0,
            )
        )

    queue.sort(key=lambda x: x.priority_score, reverse=True)

    return queue


@app.get("/api/patients/{patient_id}")
async def get_patient_details(patient_id: str):
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient = patients_db[patient_id]
    history = vitals_history.get(patient_id, [])

    return {
        "patient": patient.dict(),
        "vitals_history": [v.dict() for v in history[-50:]],
        "priority_score": calculate_priority_score(patient),
    }


@app.post("/api/patients/{patient_id}/discharge")
async def discharge_patient(patient_id: str):
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient = patients_db[patient_id]
    patient.is_active = False

    available_bands.append(patient.band_id)

    await broadcast_update({"type": "patient_discharged", "patient_id": patient_id})

    return {"message": "Patient discharged", "band_returned": patient.band_id}


@app.get("/api/stats")
async def get_statistics():
    active_patients = [p for p in patients_db.values() if p.is_active]

    tier_counts = {"EMERGENCY": 0, "ALERT": 0, "NORMAL": 0}
    for patient in active_patients:
        tier_counts[patient.current_tier] += 1

    total_vitals = sum(len(v) for v in vitals_history.values())

    avg_wait = 0
    if active_patients:
        wait_times = [
            (datetime.now() - p.check_in_time).total_seconds() / 60
            for p in active_patients
        ]
        avg_wait = sum(wait_times) / len(wait_times)

    return {
        "total_patients": len(patients_db),
        "active_patients": len(active_patients),
        "tier_breakdown": tier_counts,
        "available_bands": len(available_bands),
        "total_vitals_received": total_vitals,
        "average_wait_minutes": round(avg_wait, 1),
    }


# ============================================================================
# WRISTBAND ENDPOINTS
# ============================================================================


@app.post("/api/wristband-details")
async def update_wristband_details(data: dict):
    """Receive wristband details from wristband system"""
    global wristband_details_cache
    wristband_details_cache = data
    return {"status": "updated"}


@app.get("/api/wristband-details")
async def get_cached_wristband_details():
    """Get cached wristband details"""
    return wristband_details_cache


# ============================================================================
# WEBSOCKET
# ============================================================================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)

    await websocket.send_json(
        {"type": "connected", "message": "Connected to VitalLink server"}
    )

    try:
        while True:
            data = await websocket.receive_text()
    except:
        active_websockets.remove(websocket)


async def broadcast_update(message: dict):
    disconnected = []
    for websocket in active_websockets:
        try:
            await websocket.send_json(message)
        except:
            disconnected.append(websocket)

    for ws in disconnected:
        active_websockets.remove(ws)


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
