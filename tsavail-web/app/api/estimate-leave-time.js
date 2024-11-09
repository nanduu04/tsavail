export default async function handler(req, res) {
    if (req.method === 'POST') {
      const { flight_time, airport_code, start_location } = req.body;
  
      try {
        const response = await fetch('http://localhost:5000/flight', { // Flask endpoint
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ flight_time, airport_code, start_location }),
        });
  
        const data = await response.json();
  
        if (response.ok) {
          res.status(200).json(data);
        } else {
          res.status(response.status).json({ error: data.error || 'Failed to fetch data from server' });
        }
      } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to fetch data from server' });
      }
    } else {
      res.setHeader('Allow', ['POST']);
      res.status(405).end(`Method ${req.method} Not Allowed`);
    }
  }
  