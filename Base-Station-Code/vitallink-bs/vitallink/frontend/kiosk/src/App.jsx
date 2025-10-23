import React, { useState } from 'react';
import { AlertCircle, CheckCircle, Clock, User } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [step, setStep] = useState('welcome');
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    dob: '',
    symptoms: [],
    severity: 'moderate'
  });
  const [assignedBand, setAssignedBand] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const symptoms = [
    'Chest Pain', 'Difficulty Breathing', 'Severe Headache',
    'Abdominal Pain', 'Fever', 'Nausea/Vomiting',
    'Dizziness', 'Injury/Trauma', 'Other'
  ];

  const handleSymptomToggle = (symptom) => {
    setFormData(prev => ({
      ...prev,
      symptoms: prev.symptoms.includes(symptom)
        ? prev.symptoms.filter(s => s !== symptom)
        : [...prev.symptoms, symptom]
    }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      console.log('Submitting check-in data:', formData);
      
      const response = await fetch(`${API_BASE}/api/checkin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Check-in successful:', data);
      
      setAssignedBand({
        patientId: data.patient_id,
        bandId: data.band_id,
        station: Math.floor(Math.random() * 8) + 1
      });
      
      setStep('complete');
    } catch (error) {
      console.error('Check-in failed:', error);
      setError(error.message);
      alert(`Failed to check in: ${error.message}\n\nMake sure the backend is running at ${API_BASE}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (step === 'welcome') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-12 max-w-2xl w-full text-center">
          <div className="mb-8">
            <div className="bg-blue-600 rounded-full w-24 h-24 flex items-center justify-center mx-auto mb-6">
              <User className="w-12 h-12 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-gray-800 mb-3">Welcome to VitalLink</h1>
            <p className="text-xl text-gray-600">Emergency Room Check-In</p>
          </div>
          
          <div className="space-y-4 mb-8 text-left bg-blue-50 p-6 rounded-xl">
            <h2 className="font-semibold text-lg text-gray-800 mb-3">What to expect:</h2>
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-1 flex-shrink-0" />
              <p className="text-gray-700">Answer a few questions about your condition</p>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-1 flex-shrink-0" />
              <p className="text-gray-700">Receive a smart wristband to monitor your vitals</p>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-1 flex-shrink-0" />
              <p className="text-gray-700">Wait comfortably while we track your condition</p>
            </div>
          </div>

          <button
            onClick={() => setStep('form')}
            className="bg-blue-600 text-white px-12 py-4 rounded-xl text-xl font-semibold hover:bg-blue-700 transition-colors shadow-lg"
          >
            Start Check-In
          </button>
        </div>
      </div>
    );
  }

  if (step === 'form') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 p-4">
        <div className="max-w-3xl mx-auto pt-8">
          <div className="bg-white rounded-2xl shadow-2xl p-8">
            <h2 className="text-3xl font-bold text-gray-800 mb-6">Patient Information</h2>
            
            {error && (
              <div className="bg-red-50 border-2 border-red-300 text-red-800 p-4 rounded-lg mb-6">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-5 h-5" />
                  <p className="font-semibold">Error: {error}</p>
                </div>
              </div>
            )}
            
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    First Name *
                  </label>
                  <input
                    type="text"
                    value={formData.firstName}
                    onChange={(e) => setFormData({...formData, firstName: e.target.value})}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none text-lg"
                    placeholder="John"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Last Name *
                  </label>
                  <input
                    type="text"
                    value={formData.lastName}
                    onChange={(e) => setFormData({...formData, lastName: e.target.value})}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none text-lg"
                    placeholder="Doe"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Date of Birth *
                </label>
                <input
                  type="date"
                  value={formData.dob}
                  onChange={(e) => setFormData({...formData, dob: e.target.value})}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none text-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Select Your Symptoms *
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {symptoms.map((symptom) => (
                    <button
                      key={symptom}
                      onClick={() => handleSymptomToggle(symptom)}
                      type="button"
                      className={`px-4 py-3 rounded-lg border-2 transition-all text-left font-medium ${
                        formData.symptoms.includes(symptom)
                          ? 'bg-blue-100 border-blue-500 text-blue-700'
                          : 'bg-white border-gray-300 text-gray-700 hover:border-blue-300'
                      }`}
                    >
                      {symptom}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  How severe are your symptoms? *
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {['mild', 'moderate', 'severe'].map((level) => (
                    <button
                      key={level}
                      onClick={() => setFormData({...formData, severity: level})}
                      type="button"
                      className={`px-6 py-4 rounded-lg border-2 transition-all font-semibold capitalize ${
                        formData.severity === level
                          ? level === 'severe' 
                            ? 'bg-red-100 border-red-500 text-red-700'
                            : level === 'moderate'
                            ? 'bg-yellow-100 border-yellow-500 text-yellow-700'
                            : 'bg-green-100 border-green-500 text-green-700'
                          : 'bg-white border-gray-300 text-gray-700 hover:border-gray-400'
                      }`}
                    >
                      {level}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-4 mt-8">
              <button
                onClick={() => setStep('welcome')}
                type="button"
                className="flex-1 px-6 py-4 border-2 border-gray-300 text-gray-700 rounded-xl font-semibold hover:bg-gray-50 transition-colors"
              >
                Back
              </button>
              <button
                onClick={handleSubmit}
                disabled={!formData.firstName || !formData.lastName || !formData.dob || formData.symptoms.length === 0 || isSubmitting}
                type="button"
                className="flex-1 px-6 py-4 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Checking In...' : 'Complete Check-In'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'complete') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-green-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-12 max-w-2xl w-full text-center">
          <div className="mb-6">
            <div className="bg-green-600 rounded-full w-24 h-24 flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-12 h-12 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-gray-800 mb-3">Check-In Complete!</h1>
            <p className="text-xl text-gray-600">Your wristband has been assigned</p>
          </div>

          <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl p-8 mb-8 text-white">
            <p className="text-sm uppercase tracking-wide mb-2 opacity-90">Your Patient ID</p>
            <p className="text-3xl font-bold mb-4">{assignedBand?.patientId}</p>
            <div className="border-t border-white/30 pt-4">
              <p className="text-sm uppercase tracking-wide mb-2 opacity-90">Wristband ID</p>
              <p className="text-2xl font-semibold">{assignedBand?.bandId}</p>
            </div>
          </div>

          <div className="space-y-4 text-left bg-blue-50 p-6 rounded-xl mb-8">
            <h2 className="font-bold text-lg text-gray-800 mb-3">Next Steps:</h2>
            <div className="flex items-start gap-3">
              <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold flex-shrink-0">1</div>
              <p className="text-gray-700 pt-1">
                <strong>Pick up your wristband</strong> from Station {assignedBand?.station}
              </p>
            </div>
            <div className="flex items-start gap-3">
              <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold flex-shrink-0">2</div>
              <p className="text-gray-700 pt-1">
                <strong>Wear it on your wrist</strong> - make sure it's snug but comfortable
              </p>
            </div>
            <div className="flex items-start gap-3">
              <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold flex-shrink-0">3</div>
              <p className="text-gray-700 pt-1">
                <strong>Take a seat in the waiting area</strong> - your vitals are being monitored
              </p>
            </div>
          </div>

          <div className="flex items-center justify-center gap-2 text-gray-600 mb-6">
            <Clock className="w-5 h-5" />
            <p>A nurse will call you when it's your turn</p>
          </div>

          <button
            onClick={() => {
              setStep('welcome');
              setFormData({ firstName: '', lastName: '', dob: '', symptoms: [], severity: 'moderate' });
              setAssignedBand(null);
              setError(null);
            }}
            className="text-blue-600 font-semibold hover:underline"
          >
            Return to Start
          </button>
        </div>
      </div>
    );
  }
}

export default App;
