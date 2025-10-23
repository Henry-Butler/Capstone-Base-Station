import React, { useState, useEffect } from 'react';
import * as LucideIcons from 'lucide-react';

const { Activity, AlertCircle, Clock, Users, Bell, Heart, Thermometer, Wind, CheckCircle, UserX } = LucideIcons;

const API_BASE = 'http://localhost:8000';

function App() {
  const [patients, setPatients] = useState([]);
  const [stats, setStats] = useState({
    total_patients: 0,
    active_patients: 0,
    tier_breakdown: { EMERGENCY: 0, ALERT: 0, NORMAL: 0 },
    average_wait_minutes: 0
  });
  const [filter, setFilter] = useState('all');
  const [activeTab, setActiveTab] = useState('patients');
  const [wristbands, setWristbands] = useState([]);
  const [selectedWristband, setSelectedWristband] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const queueResponse = await fetch(`${API_BASE}/api/queue`);
        const queueData = await queueResponse.json();
        
        const statsResponse = await fetch(`${API_BASE}/api/stats`);
        const statsData = await statsResponse.json();
        
        const wristbandResponse = await fetch(`${API_BASE}/api/wristband-details`);
        const wristbandData = await wristbandResponse.json();
        
        setPatients(queueData.map(p => ({
          patient_id: p.patient_id,
          band_id: p.band_id,
          name: p.name,
          tier: p.tier,
          priority_score: p.priority_score,
          wait_time_minutes: p.wait_time_minutes,
          last_hr: p.last_hr,
          last_spo2: p.last_spo2,
          last_temp: p.last_temp,
          symptoms: []
        })));
        
        setStats(statsData);
        setWristbands(wristbandData.wristbands || []);
        
        console.log(`✓ Fetched ${queueData.length} patients and ${wristbandData.wristbands?.length || 0} wristbands`);
      } catch (error) {
        console.error('Failed to fetch from backend:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000);
    
    return () => clearInterval(interval);
  }, []);

  const getTierColor = (tier) => {
    switch(tier) {
      case 'EMERGENCY': return 'bg-red-100 text-red-800 border-red-300';
      case 'ALERT': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'NORMAL': return 'bg-green-100 text-green-800 border-green-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getTierIcon = (tier) => {
    switch(tier) {
      case 'EMERGENCY': return <AlertCircle className="w-5 h-5" />;
      case 'ALERT': return <Bell className="w-5 h-5" />;
      case 'NORMAL': return <CheckCircle className="w-5 h-5" />;
      default: return <Activity className="w-5 h-5" />;
    }
  };

  const getVitalStatus = (type, value) => {
    if (type === 'hr') {
      if (value > 110 || value < 50) return 'text-red-600 font-bold';
      if (value > 100 || value < 60) return 'text-yellow-600 font-semibold';
      return 'text-green-600';
    }
    if (type === 'spo2') {
      if (value < 88) return 'text-red-600 font-bold';
      if (value < 92) return 'text-yellow-600 font-semibold';
      return 'text-green-600';
    }
    if (type === 'temp') {
      if (value > 39.5 || value < 35.5) return 'text-red-600 font-bold';
      if (value > 38.3 || value < 36.0) return 'text-yellow-600 font-semibold';
      return 'text-green-600';
    }
    return 'text-gray-700';
  };

  const handleDischarge = async (patientId) => {
    try {
      await fetch(`${API_BASE}/api/patients/${patientId}/discharge`, {
        method: 'POST',
      });
      console.log(`✓ Discharged patient ${patientId}`);
      setPatients(prev => prev.filter(p => p.patient_id !== patientId));
    } catch (error) {
      console.error('Failed to discharge patient:', error);
      setPatients(prev => prev.filter(p => p.patient_id !== patientId));
    }
  };

  const filteredPatients = patients
    .filter(p => filter === 'all' || p.tier === filter)
    .sort((a, b) => b.priority_score - a.priority_score);

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 shadow-lg">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-1">VitalLink Dashboard</h1>
              <p className="text-blue-100">Emergency Department Patient Monitoring</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="bg-white bg-opacity-20 rounded-lg px-4 py-2">
                <p className="text-sm text-blue-100">Last Update</p>
                <p className="text-lg font-semibold">{new Date().toLocaleTimeString()}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto p-6">
          <div className="grid grid-cols-4 gap-6">
            <div className="flex items-center gap-4">
              <div className="bg-blue-100 p-3 rounded-lg">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Active Patients</p>
                <p className="text-2xl font-bold text-gray-800">{stats.active_patients}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="bg-red-100 p-3 rounded-lg">
                <AlertCircle className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Emergency</p>
                <p className="text-2xl font-bold text-red-600">{stats.tier_breakdown.EMERGENCY}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="bg-yellow-100 p-3 rounded-lg">
                <Bell className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Alert</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.tier_breakdown.ALERT}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="bg-green-100 p-3 rounded-lg">
                <Clock className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Avg Wait Time</p>
                <p className="text-2xl font-bold text-gray-800">{stats.average_wait_minutes} min</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-4 py-4">
            <button
              onClick={() => setActiveTab('patients')}
              className={`px-6 py-2 rounded-t-lg font-semibold transition-colors ${
                activeTab === 'patients'
                  ? 'bg-blue-100 text-blue-700 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              📋 Patients ({patients.length})
            </button>
            <button
              onClick={() => setActiveTab('wristbands')}
              className={`px-6 py-2 rounded-t-lg font-semibold transition-colors ${
                activeTab === 'wristbands'
                  ? 'bg-purple-100 text-purple-700 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              ⌚ Wristbands ({wristbands.length})
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        {activeTab === 'patients' ? (
          <>
            <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
              <div className="flex gap-2">
                <button
                  onClick={() => setFilter('all')}
                  className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
                    filter === 'all' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  All Patients ({patients.length})
                </button>
                <button
                  onClick={() => setFilter('EMERGENCY')}
                  className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
                    filter === 'EMERGENCY' 
                      ? 'bg-red-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Emergency ({stats.tier_breakdown.EMERGENCY})
                </button>
                <button
                  onClick={() => setFilter('ALERT')}
                  className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
                    filter === 'ALERT' 
                      ? 'bg-yellow-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Alert ({stats.tier_breakdown.ALERT})
                </button>
                <button
                  onClick={() => setFilter('NORMAL')}
                  className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
                    filter === 'NORMAL' 
                      ? 'bg-green-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Stable ({stats.tier_breakdown.NORMAL})
                </button>
              </div>
            </div>

            <div className="space-y-4">
              {filteredPatients.map((patient, index) => (
                <div 
                  key={patient.patient_id}
                  className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-start gap-4">
                        <div className="text-2xl font-bold text-gray-400 min-w-12 text-center pt-1">
                          #{index + 1}
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-gray-800 mb-1">{patient.name}</h3>
                          <div className="flex items-center gap-3 text-sm text-gray-600">
                            <span className="font-mono">{patient.patient_id}</span>
                            <span>•</span>
                            <span className="font-mono">{patient.band_id}</span>
                          </div>
                          {patient.symptoms && patient.symptoms.length > 0 && (
                            <div className="flex flex-wrap gap-2 mt-2">
                              {patient.symptoms.map(symptom => (
                                <span key={symptom} className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-xs font-medium">
                                  {symptom}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        <div className={`px-4 py-2 rounded-lg border-2 flex items-center gap-2 font-semibold ${getTierColor(patient.tier)}`}>
                          {getTierIcon(patient.tier)}
                          {patient.tier}
                        </div>
                        <button
                          onClick={() => handleDischarge(patient.patient_id)}
                          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-2 font-semibold"
                        >
                          <UserX className="w-4 h-4" />
                          Discharge
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-4 pt-4 border-t">
                      <div className="bg-gray-50 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <Heart className="w-4 h-4 text-gray-600" />
                          <span className="text-xs text-gray-600 font-medium">Heart Rate</span>
                        </div>
                        <p className={`text-2xl font-bold ${getVitalStatus('hr', patient.last_hr)}`}>
                          {patient.last_hr}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">bpm</p>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <Wind className="w-4 h-4 text-gray-600" />
                          <span className="text-xs text-gray-600 font-medium">SpO₂</span>
                        </div>
                        <p className={`text-2xl font-bold ${getVitalStatus('spo2', patient.last_spo2)}`}>
                          {patient.last_spo2}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">%</p>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <Thermometer className="w-4 h-4 text-gray-600" />
                          <span className="text-xs text-gray-600 font-medium">Temperature</span>
                        </div>
                        <p className={`text-2xl font-bold ${getVitalStatus('temp', patient.last_temp)}`}>
                          {patient.last_temp.toFixed(1)}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">°C</p>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <Clock className="w-4 h-4 text-gray-600" />
                          <span className="text-xs text-gray-600 font-medium">Wait Time</span>
                        </div>
                        <p className="text-2xl font-bold text-gray-700">
                          {patient.wait_time_minutes}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">minutes</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {filteredPatients.length === 0 && (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center">
                <Activity className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-600 mb-2">No patients in this category</h3>
                <p className="text-gray-500">Patients will appear here as they check in</p>
              </div>
            )}
          </>
        ) : (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-2xl font-bold mb-4">Wristband Inventory</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {wristbands.map(band => (
                  <div
                    key={band.band_id}
                    onClick={() => setSelectedWristband(band)}
                    className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                      band.status === 'in_use'
                        ? 'bg-blue-50 border-blue-300 hover:border-blue-400'
                        : 'bg-gray-50 border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono font-bold text-lg">
                        {band.type === 'real' ? '🔵' : '🟢'} {band.band_id}
                      </span>
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        band.status === 'in_use' ? 'bg-blue-600 text-white' :
                        band.status === 'available' ? 'bg-green-600 text-white' :
                        'bg-gray-400 text-white'
                      }`}>
                        {band.status.toUpperCase().replace('_', ' ')}
                      </span>
                    </div>
                    
                    {band.patient_id && (
                      <div className="text-sm text-gray-600 mb-2">
                        Patient: <span className="font-mono font-semibold">{band.patient_id}</span>
                      </div>
                    )}
                    
                    <div className="text-xs text-gray-500 flex justify-between">
                      <span>Packets: {band.packet_count}</span>
                      {band.is_monitoring && (
                        <span className="text-green-600 font-semibold">● LIVE</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {wristbands.length === 0 && (
                <p className="text-gray-500 text-center py-8">No wristbands configured</p>
              )}
            </div>

            {selectedWristband && selectedWristband.last_raw_packet && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold flex items-center gap-2">
                    <span>Packet Details: {selectedWristband.band_id}</span>
                    {selectedWristband.type === 'simulated' && (
                      <span className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded">MOCK</span>
                    )}
                  </h3>
                  <button
                    onClick={() => setSelectedWristband(null)}
                    className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
                  >
                    ✕
                  </button>
                </div>

                <div className="mb-4">
                  <h4 className="font-semibold text-sm text-gray-600 mb-2">Raw Packet (16 bytes, Hex):</h4>
                  <div className="bg-gray-900 text-green-400 p-4 rounded font-mono text-sm overflow-x-auto">
                    {selectedWristband.last_raw_packet.hex.toUpperCase().match(/.{1,2}/g).join(' ')}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Format: [ver][seq][timestamp][flags][hr][spo2][temp_x100][activity_x100][checksum][rfu]
                  </p>
                </div>

                {selectedWristband.last_raw_packet.decoded && (
                  <>
                    <div className="mb-4">
                      <h4 className="font-semibold text-sm text-gray-600 mb-3">Decoded Fields:</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div className="bg-gray-50 p-3 rounded border">
                          <div className="text-xs text-gray-600 mb-1">Version</div>
                          <div className="font-mono text-lg font-bold">0x{selectedWristband.last_raw_packet.decoded.version.toString(16).padStart(2, '0')}</div>
                        </div>
                        <div className="bg-gray-50 p-3 rounded border">
                          <div className="text-xs text-gray-600 mb-1">Sequence #</div>
                          <div className="font-mono text-lg font-bold">{selectedWristband.last_raw_packet.decoded.sequence}</div>
                        </div>
                        <div className="bg-gray-50 p-3 rounded border col-span-2">
                          <div className="text-xs text-gray-600 mb-1">Timestamp (ms since boot)</div>
                          <div className="font-mono text-lg font-bold">{selectedWristband.last_raw_packet.decoded.timestamp_ms.toLocaleString()}</div>
                        </div>
                        <div className="bg-blue-50 p-3 rounded border">
                          <div className="text-xs text-gray-600 mb-1">Heart Rate</div>
                          <div className="font-mono text-2xl font-bold text-blue-600">{selectedWristband.last_raw_packet.decoded.hr_bpm}</div>
                          <div className="text-xs text-gray-500">bpm</div>
                        </div>
                        <div className="bg-green-50 p-3 rounded border">
                          <div className="text-xs text-gray-600 mb-1">SpO₂</div>
                          <div className="font-mono text-2xl font-bold text-green-600">{selectedWristband.last_raw_packet.decoded.spo2}</div>
                          <div className="text-xs text-gray-500">%</div>
                        </div>
                        <div className="bg-orange-50 p-3 rounded border">
                          <div className="text-xs text-gray-600 mb-1">Temperature</div>
                          <div className="font-mono text-2xl font-bold text-orange-600">{selectedWristband.last_raw_packet.decoded.temperature_c.toFixed(2)}</div>
                          <div className="text-xs text-gray-500">°C</div>
                        </div>
                        <div className="bg-purple-50 p-3 rounded border">
                          <div className="text-xs text-gray-600 mb-1">Activity</div>
                          <div className="font-mono text-2xl font-bold text-purple-600">{selectedWristband.last_raw_packet.decoded.activity.toFixed(2)}</div>
                          <div className="text-xs text-gray-500">RMS</div>
                        </div>
                        <div className="bg-gray-50 p-3 rounded border">
                          <div className="text-xs text-gray-600 mb-1">Checksum</div>
                          <div className="font-mono text-lg font-bold">{selectedWristband.last_raw_packet.decoded.checksum}</div>
                        </div>
                        <div className="bg-gray-50 p-3 rounded border">
                          <div className="text-xs text-gray-600 mb-1">Flags (raw)</div>
                          <div className="font-mono text-lg font-bold">0x{selectedWristband.last_raw_packet.decoded.flags.raw.toString(16).padStart(2, '0')}</div>
                        </div>
                      </div>
                    </div>

                    {selectedWristband.last_raw_packet.decoded.flags && (
                      <div className="mt-4">
                        <h4 className="font-semibold text-sm text-gray-600 mb-2">Status Flags:</h4>
                        <div className="flex flex-wrap gap-2">
                          {selectedWristband.last_raw_packet.decoded.flags.emergency && (
                            <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-semibold border border-red-300">
                              🚨 Bit 4: Emergency
                            </span>
                          )}
                          {selectedWristband.last_raw_packet.decoded.flags.alert && (
                            <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-semibold border border-yellow-300">
                              ⚠️ Bit 3: Alert
                            </span>
                          )}
                          {selectedWristband.last_raw_packet.decoded.flags.sensor_fault && (
                            <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-semibold border border-purple-300">
                              ⚙️ Bit 2: Sensor Fault
                            </span>
                          )}
                          {selectedWristband.last_raw_packet.decoded.flags.low_battery && (
                            <span className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm font-semibold border border-orange-300">
                              🔋 Bit 1: Low Battery
                            </span>
                          )}
                          {selectedWristband.last_raw_packet.decoded.flags.motion_artifact && (
                            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold border border-blue-300">
                              👋 Bit 0: Motion Artifact
                            </span>
                          )}
                          {!Object.values(selectedWristband.last_raw_packet.decoded.flags).some(v => v === true) && (
                            <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm font-semibold">
                              ✓ No flags set (all normal)
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
