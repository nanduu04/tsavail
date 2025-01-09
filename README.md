Sure! Here’s the updated README to include instructions for setting up a virtual environment and running the Flask server:

NYC Airport Wait Times Application

Description

This application scrapes the latest wait times and walk times from NYC airports (LaGuardia, JFK, and Newark). It displays the wait times and shows the walk times.

Features

    •	Schedule a cron job to scrape wait times from all NYC airports.
    •	Display the wait times.
    •	User authentication for login and registration.
    •	Enter flight details and save the flight information.
    •	Calculate travel time from your current location to the airport.
    •	Notification system to email you a specified number of minutes before your flight.
    •	Use real-time flight data to update the user on departure times.

To-Do List

    •	Schedule a cron job to scrape wait times from all NYC airports.
    •	Display the wait times.
    •	Login and Registration.
    •	Enter flight details and be able to save the flight.
    •	Find the time it takes from your current location to the airport.
    •	Notification system where we email  minutes before the flight.
    •	Use real-time flight data to update the user on departure time.

Setup and Installation

Backend

    1.	Navigate to the backend directory:

cd backend

    2.	Create and activate a Python virtual environment:

python3 -m venv venv
source venv/bin/activate # On Windows use `venv\Scripts\activate`

    3.	Install the required dependencies:

pip3 install -r requirements.txt

    4.	Run the Flask server:

flask run

Frontend

    1.	Navigate to the frontend directory:

cd app

    2.	Install the required dependencies:

npm install

    3.	Run the frontend server:

npm run

Deployment

For production deployment, consider using services like AWS, Heroku, or Vercel.

Contributing

Please make sure to update tests as appropriate.

License

MIT

This README now includes instructions for setting up a virtual environment, activating it, and running the Flask server.
