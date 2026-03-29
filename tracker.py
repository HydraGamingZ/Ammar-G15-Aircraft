import requests
import csv
import time
from datetime import datetime

print("Starting the Continuous Flight Tracker...")

# 1. We create our blank digital spreadsheet and name the columns
with open('perak_flights.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    # These are the exact details your assignment asks for!
    writer.writerow(['Timestamp', 'Aircraft_ID', 'Flight_Name', 'Latitude', 'Longitude', 'Altitude'])

print("Spreadsheet created! Now tracking every 5 minutes...")

# 2. We create an endless loop so it runs continuously for 3 days
while True:
    try:
        url = "https://opensky-network.org/api/states/all?lamin=3.50&lamax=6.00&lomin=100.20&lomax=101.80"
        response = requests.get(url)
        data = response.json()
        
        # Get the exact current time (the timestamp)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 3. We check if there are any airplanes
        if data['states'] is not None:
            print(f"[{current_time}] Found airplanes! Saving to spreadsheet...")
            
            # Open the spreadsheet and add the new airplanes to the bottom
            with open('perak_flights.csv', mode='a', newline='') as file:
                writer = csv.writer(file)
                for plane in data['states']:
                    # Save: Time, ID, Name, Lat, Long, Altitude
                    writer.writerow([current_time, plane[0], plane[1], plane[6], plane[5], plane[7]])
        else:
            print(f"[{current_time}] No airplanes right now. Still watching...")

        # 4. We tell the code to sleep for 5 minutes (300 seconds). 
        # This is CRUCIAL so the OpenSky website doesn't block us for asking too fast!
        time.sleep(300)

    except Exception as e:
        # If the internet drops, the program won't crash. It will just try again later.
        print("Waiting for internet connection...")
        time.sleep(300)