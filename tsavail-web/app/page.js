"use client"; // Add this line
import { useState } from 'react';

export default function Home() {
  const [flightTime, setFlightTime] = useState('');
  const [airportCode, setAirportCode] = useState('LGA');
  const [startLocation, setStartLocation] = useState('');
  const [leaveTime, setLeaveTime] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch('/api/estimate-leave-time', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ flight_time: flightTime, airport_code: airportCode, start_location: startLocation }),
      });
      const data = await response.json();
      if (response.ok) {
        setLeaveTime(data.leave_time);
      } else {
        alert(data.error || 'An error occurred');
      }
    } catch (error) {
      console.error(error);
      alert('Failed to fetch data');
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h1>Airport Leave Time Estimator</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Flight Time:
          <input
            type="datetime-local"
            value={flightTime}
            onChange={(e) => setFlightTime(e.target.value)}
            required
          />
        </label>
        <label>
          Airport Code:
          <input
            type="text"
            value={airportCode}
            onChange={(e) => setAirportCode(e.target.value)}
            required
          />
        </label>
        <label>
          Starting Location:
          <input
            type="text"
            value={startLocation}
            onChange={(e) => setStartLocation(e.target.value)}
            required
          />
        </label>
        <button type="submit">Get Leave Time</button>
      </form>

      {leaveTime && (
        <div style={{ marginTop: '20px' }}>
          <h2>Recommended Time to Leave</h2>
          <p>{leaveTime}</p>
        </div>
      )}
    </div>
  );
}

