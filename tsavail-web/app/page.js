"use client";

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
    <div style={styles.container}>
      <h1 style={styles.title}>Airport Leave Time Estimator</h1>
      <form onSubmit={handleSubmit} style={styles.form}>
        <label style={styles.label}>
          Flight Time:
          <input
            type="datetime-local"
            value={flightTime}
            onChange={(e) => setFlightTime(e.target.value)}
            required
            style={styles.input}
          />
        </label>
        <label style={styles.label}>
          Airport Code:
          <input
            type="text"
            value={airportCode}
            onChange={(e) => setAirportCode(e.target.value)}
            required
            style={styles.input}
          />
        </label>
        <label style={styles.label}>
          Starting Location:
          <input
            type="text"
            value={startLocation}
            onChange={(e) => setStartLocation(e.target.value)}
            required
            style={styles.input}
          />
        </label>
        <button type="submit" style={styles.button}>Get Leave Time</button>
      </form>

      {leaveTime && (
        <div style={styles.resultContainer}>
          <h2 style={styles.resultTitle}>Recommended Time to Leave</h2>
          <p style={styles.resultText}>{leaveTime}</p>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    padding: '20px',
    maxWidth: '600px',
    margin: '0 auto',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
  },
  title: {
    fontSize: '2rem',
    marginBottom: '20px',
    color: '#333',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    width: '100%',
  },
  label: {
    marginBottom: '15px',
    fontSize: '1rem',
    color: '#555',
  },
  input: {
    padding: '10px',
    fontSize: '1rem',
    borderRadius: '5px',
    border: '1px solid #ccc',
    width: '100%',
    boxSizing: 'border-box',
    marginTop: '5px',
  },
  button: {
    padding: '10px 15px',
    fontSize: '1rem',
    backgroundColor: '#0070f3',
    color: '#fff',
    border: 'none',
    borderRadius: '5px',
    cursor: 'pointer',
    marginTop: '10px',
  },
  resultContainer: {
    marginTop: '20px',
    padding: '15px',
    borderRadius: '5px',
    backgroundColor: '#f0f8ff',
    width: '100%',
  },
  resultTitle: {
    fontSize: '1.5rem',
    color: '#0070f3',
  },
  resultText: {
    fontSize: '1.25rem',
    color: '#333',
  },
};

