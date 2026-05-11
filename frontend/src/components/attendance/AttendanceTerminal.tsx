'use client';

/**
 * Attendance Terminal Component
 * 
 * Provides biometric face recognition interface for employee check-in/check-out.
 * Integrates with Face Plugin SDK for biometric capture and verification.
 */

import React, { useState, useEffect, useRef } from 'react';
import { BiometricData, CheckInResponse, CheckOutResponse, AttendanceRecord } from '@/types';
import { checkIn, checkOut } from '@/services/attendance';

interface AttendanceTerminalProps {
  terminalId?: string;
  onSuccess?: (attendance: AttendanceRecord) => void;
  onError?: (error: string) => void;
}

type TerminalMode = 'idle' | 'capturing' | 'processing' | 'success' | 'error';

export default function AttendanceTerminal({
  terminalId = 'TERMINAL_01',
  onSuccess,
  onError,
}: AttendanceTerminalProps) {
  const [mode, setMode] = useState<TerminalMode>('idle');
  const [employeeId, setEmployeeId] = useState('');
  const [message, setMessage] = useState('');
  const [lastAttendance, setLastAttendance] = useState<AttendanceRecord | null>(null);
  const [biometricData, setBiometricData] = useState<BiometricData | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Initialize Face Plugin SDK (mock implementation)
  useEffect(() => {
    // In production, this would initialize the actual Face Plugin SDK
    console.log('Face Plugin SDK initialized for terminal:', terminalId);
    
    return () => {
      // Cleanup
      console.log('Face Plugin SDK cleanup');
    };
  }, [terminalId]);

  /**
   * Start face capture process.
   * In production, this would activate the Face Plugin SDK camera.
   */
  const startFaceCapture = async () => {
    if (!employeeId.trim()) {
      setMessage('Please enter Employee ID');
      return;
    }

    setMode('capturing');
    setMessage('Position your face in the camera...');

    try {
      // Mock: Simulate face capture
      // In production, this would use Face Plugin SDK to capture face
      await simulateFaceCapture();
    } catch (error) {
      setMode('error');
      setMessage('Face capture failed. Please try again.');
      onError?.('Face capture failed');
    }
  };

  /**
   * Simulate face capture (mock implementation).
   * In production, this would use the actual Face Plugin SDK.
   */
  const simulateFaceCapture = async (): Promise<void> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        // Generate mock biometric data
        const mockBiometricData: BiometricData = {
          face_encoding: Array.from({ length: 128 }, () => Math.random()),
          quality_score: 0.85 + Math.random() * 0.15, // 0.85 - 1.0
          capture_timestamp: new Date().toISOString(),
        };

        setBiometricData(mockBiometricData);
        setMessage('Face captured successfully!');
        resolve();
      }, 2000);
    });
  };

  /**
   * Process check-in with biometric verification.
   */
  const handleCheckIn = async () => {
    if (!biometricData) {
      setMessage('No biometric data captured');
      return;
    }

    setMode('processing');
    setMessage('Verifying identity...');

    try {
      const response: CheckInResponse = await checkIn(
        employeeId,
        biometricData,
        terminalId
      );

      setMode('success');
      setMessage(
        `Check-in successful! ${response.message}\n` +
        `Similarity: ${(response.similarity_score * 100).toFixed(1)}%`
      );
      setLastAttendance(response.attendance);
      onSuccess?.(response.attendance);

      // Reset after 3 seconds
      setTimeout(() => {
        resetTerminal();
      }, 3000);
    } catch (error: any) {
      setMode('error');
      const errorMessage = error.response?.data?.error || 'Check-in failed';
      setMessage(errorMessage);
      onError?.(errorMessage);

      // Reset after 3 seconds
      setTimeout(() => {
        resetTerminal();
      }, 3000);
    }
  };

  /**
   * Process check-out.
   */
  const handleCheckOut = async () => {
    if (!employeeId.trim()) {
      setMessage('Please enter Employee ID');
      return;
    }

    setMode('processing');
    setMessage('Processing check-out...');

    try {
      const response: CheckOutResponse = await checkOut(employeeId, terminalId);

      setMode('success');
      setMessage(
        `Check-out successful!\n` +
        `Working hours: ${response.working_hours.toFixed(2)}h\n` +
        `Overtime: ${response.overtime_hours.toFixed(2)}h`
      );
      setLastAttendance(response.attendance);
      onSuccess?.(response.attendance);

      // Reset after 3 seconds
      setTimeout(() => {
        resetTerminal();
      }, 3000);
    } catch (error: any) {
      setMode('error');
      const errorMessage = error.response?.data?.error || 'Check-out failed';
      setMessage(errorMessage);
      onError?.(errorMessage);

      // Reset after 3 seconds
      setTimeout(() => {
        resetTerminal();
      }, 3000);
    }
  };

  /**
   * Reset terminal to idle state.
   */
  const resetTerminal = () => {
    setMode('idle');
    setEmployeeId('');
    setMessage('');
    setBiometricData(null);
  };

  /**
   * Get status color based on mode.
   */
  const getStatusColor = () => {
    switch (mode) {
      case 'capturing':
        return 'bg-blue-500';
      case 'processing':
        return 'bg-yellow-500';
      case 'success':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      {/* Terminal Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Attendance Terminal
        </h2>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${getStatusColor()}`}></div>
          <span className="text-sm text-gray-600">
            Terminal ID: {terminalId}
          </span>
        </div>
      </div>

      {/* Camera Preview Area */}
      <div className="mb-6 bg-gray-900 rounded-lg overflow-hidden aspect-video relative">
        <video
          ref={videoRef}
          className="w-full h-full object-cover"
          autoPlay
          muted
          playsInline
        />
        <canvas ref={canvasRef} className="hidden" />
        
        {/* Overlay for face detection */}
        {mode === 'capturing' && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="border-4 border-blue-500 rounded-full w-64 h-64 animate-pulse"></div>
          </div>
        )}

        {/* Status overlay */}
        {mode !== 'idle' && (
          <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-75 p-4">
            <p className="text-white text-center">{message}</p>
          </div>
        )}
      </div>

      {/* Employee ID Input */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Employee ID
        </label>
        <input
          type="text"
          value={employeeId}
          onChange={(e) => setEmployeeId(e.target.value)}
          placeholder="Enter Employee ID"
          disabled={mode !== 'idle'}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
        />
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <button
          onClick={startFaceCapture}
          disabled={mode !== 'idle'}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {mode === 'capturing' ? 'Capturing...' : 'Check In'}
        </button>
        <button
          onClick={handleCheckOut}
          disabled={mode !== 'idle'}
          className="px-6 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          Check Out
        </button>
      </div>

      {/* Biometric Capture Button (after face capture) */}
      {biometricData && mode === 'capturing' && (
        <div className="mb-6">
          <button
            onClick={handleCheckIn}
            className="w-full px-6 py-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 transition-colors"
          >
            Verify & Check In
          </button>
        </div>
      )}

      {/* Last Attendance Info */}
      {lastAttendance && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h3 className="font-semibold text-gray-800 mb-2">Last Attendance</h3>
          <div className="text-sm text-gray-600 space-y-1">
            <p>Date: {lastAttendance.date}</p>
            <p>Status: <span className="font-medium">{lastAttendance.status}</span></p>
            {lastAttendance.check_in && (
              <p>Check-in: {new Date(lastAttendance.check_in).toLocaleTimeString()}</p>
            )}
            {lastAttendance.check_out && (
              <p>Check-out: {new Date(lastAttendance.check_out).toLocaleTimeString()}</p>
            )}
            {lastAttendance.working_hours && (
              <p>Working Hours: {lastAttendance.working_hours.toFixed(2)}h</p>
            )}
            <p>
              Biometric Verified:{' '}
              <span className={lastAttendance.biometric_verified ? 'text-green-600' : 'text-red-600'}>
                {lastAttendance.biometric_verified ? 'Yes' : 'No'}
              </span>
            </p>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="font-semibold text-blue-900 mb-2">Instructions</h4>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li>Enter your Employee ID</li>
          <li>Click "Check In" and position your face in the camera</li>
          <li>Wait for face verification to complete</li>
          <li>For check-out, enter Employee ID and click "Check Out"</li>
        </ul>
      </div>
    </div>
  );
}
