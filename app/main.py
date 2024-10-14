import sys
import os
import textwrap
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setting up directories
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import requests
import json
from datetime import datetime
from waveshare_epd import epd7in5_V2
import time
from PIL import Image, ImageDraw, ImageFont
import traceback
import logging


logging.basicConfig(level=logging.DEBUG)

def get_bus_arrival(api_key, bus_stop_code):
    url = "https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival?BusStopCode=" + bus_stop_code
    headers = {
        'AccountKey': api_key,
        'accept': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        services = data.get("Services", [])
        bus_info = []
        
        for service in services:
            service_no = service["ServiceNo"]
            arrival_times = []
            for bus in ["NextBus", "NextBus2", "NextBus3"]:
                if service.get(bus):
                    eta = service[bus]["EstimatedArrival"]
                    if eta:
                        eta_time = datetime.strptime(eta, "%Y-%m-%dT%H:%M:%S%z")
                        time_diff = (eta_time - datetime.now(eta_time.tzinfo)).total_seconds() / 60
                        arrival_times.append(round(time_diff))
            if arrival_times:
                bus_info.append((service_no, arrival_times))
        return bus_info
    else:
        logging.error("Error: Unable to fetch data. Status code: " + str(response.status_code))
        return []

def get_train_disruptions():
    api_key = os.getenv('API_KEY')
    url = "https://datamall2.mytransport.sg/ltaodataservice/TrainServiceAlerts"
    headers = {
        'AccountKey': api_key,
        'accept': 'application/json'
    }

    print("Fetching train disruptions...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")

    try:
        response = requests.get(url, headers=headers)
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")

        response.raise_for_status()  # Raises an HTTPError for bad responses
        data = response.json()

        print("Parsed JSON data:")
        print(json.dumps(data, indent=2))

        disruptions = []
        content = ''

        if 'value' in data:
            print("'value' key found in data")
            if 'AffectedSegments' in data['value'] and data['value']['AffectedSegments']:
                print("Processing AffectedSegments...")
                for segment in data['value']['AffectedSegments']:
                    disruption = {
                        'Line': segment.get('Line', ''),
                        'Direction': segment.get('Direction', ''),
                        'Stations': segment.get('Stations', '').split(',')
                    }
                    disruptions.append(disruption)
                    print(f"Added disruption: {disruption}")

            if 'Message' in data['value'] and data['value']['Message']:
                print("Processing Message...")
                content = data['value']['Message'][0].get('Content', '')
                print(f"Content: {content}")

        if not disruptions and not content:
            print("No disruptions found")
            return "No Disruptions Today!"
        else:
            result = {
                'disruptions': disruptions,
                'content': content
            }
            print(f"Returning result: {result}")
            return result

    except requests.RequestException as e:
        print(f"Error fetching train disruptions: {e}")
        return None

def display_bus_arrivals(epd, draw, font, bus_info_A, bus_info_B):
    draw.rectangle((0, 0, epd.width, epd.height), fill=255)  # Clear the display
    y = 20  # Initial Y position for text
    column_offset = epd.width // 2  # Divide the screen into two columns
    
    draw.text((120, y),"Downstairs", font=font, fill=0)

    # Display for Bus Stop A (left column)
    for service_no, arrival_times in bus_info_A:
        draw.rectangle((20, y+50, 180, y + 110), fill=0)
        draw.text((50, y + 58), service_no, font=font, fill=255)
        times_text = " | ".join(map(str, arrival_times))
        draw.text((220, y + 55), times_text, font=font, fill=0)
        y += 70
    
    y = 20  # Reset Y position for the right column

    draw.text((120+column_offset, y),"Opposite", font=font, fill=0)

    # Display for Bus Stop B (right column)
    for service_no, arrival_times in bus_info_B:
        draw.rectangle((20 + column_offset, y+50, 180 + column_offset, y + 110), fill=0)
        draw.text((50 + column_offset, y + 58), service_no, font=font, fill=255)
        times_text = " | ".join(map(str, arrival_times))
        draw.text((220 + column_offset, y + 55), times_text, font=font, fill=0)
        y += 70
    
    epd.display(epd.getbuffer(Himage))

def display_train_disruption(epd, draw, font, train_info):
    # Clear the image
    Himage = Image.new('1', (epd.width, epd.height), 255)
    draw = ImageDraw.Draw(Himage)

    # Draw title
    draw.text((10, 10), "Train Disruptions", font=font, fill=0)

    if train_info == "No Disruptions Today!":
        draw.text((10, 60), train_info, font=font, fill=0)
    elif train_info:
        y_offset = 60
        for disruption in train_info['disruptions']:
            draw.text((10, y_offset), f"Line: {disruption['Line']}", font=font, fill=0)
            y_offset += 40
            draw.text((10, y_offset), f"Direction: {disruption['Direction']}", font=font, fill=0)
            y_offset += 40
            stations = ", ".join(disruption['Stations'])
            draw.text((10, y_offset), f"Stations: {stations}", font=font, fill=0)
            y_offset += 60

        # Display content (message) if available
        if train_info['content']:
            draw.text((10, y_offset), "Message:", font=font, fill=0)
            y_offset += 40
            # Wrap text to fit display width
            wrapped_text = textwrap.wrap(train_info['content'], width=40)  # Adjust width as needed
            for line in wrapped_text:
                draw.text((10, y_offset), line, font=font, fill=0)
                y_offset += 30

    # Display the image on the E-Ink display
    epd.display(epd.getbuffer(Himage))

try:
    logging.info("Bus Arrival Display on E-Ink")
    epd = epd7in5_V2.EPD()
    
    logging.info("Init and Clear")
    epd.init()
    epd.Clear()

  # Using a larger and bold font
    font48 = ImageFont.truetype(os.path.join(picdir, 'OpenSans-Bold.ttf'), 32)
    Himage = Image.new('1', (epd.width, epd.height), 255)
    draw = ImageDraw.Draw(Himage)
    
    api_key = os.getenv('API_KEY')
    bus_stop_code_A = os.getenv('BUS_STOP_CODE_A')
    bus_stop_code_B = os.getenv('BUS_STOP_CODE_B')

    
    while True:
        #Display Bus Arrival
        bus_info_A = get_bus_arrival(api_key, bus_stop_code_A)
        bus_info_B = get_bus_arrival(api_key, bus_stop_code_B)
        display_bus_arrivals(epd, draw, font48, bus_info_A, bus_info_B)
        time.sleep(30)  # Refresh every 30 seconds

        # Display train disruptions
        # Uncomment to display train info
        # train_info = get_train_disruptions()
        # display_train_disruption(epd, draw, font48, train_info)
        # time.sleep(15)  # Display train info for 30 seconds

except IOError as e:
    logging.error(e)
    
except KeyboardInterrupt:
    logging.info("Exiting...")
    epd.Clear()
    epd7in5_V2.epdconfig.module_exit(cleanup=True)
    exit()

