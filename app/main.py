import sys
import os
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

    #bus_stop_code_A = '53241'  # Downstairs
    #bus_stop_code_B = '53249'  # Opposite
    
    while True:
        bus_info_A = get_bus_arrival(api_key, bus_stop_code_A)
        bus_info_B = get_bus_arrival(api_key, bus_stop_code_B)
        display_bus_arrivals(epd, draw, font48, bus_info_A, bus_info_B)
        time.sleep(30)  # Refresh every 1 minute

except IOError as e:
    logging.error(e)
    
except KeyboardInterrupt:
    logging.info("Exiting...")
    epd.Clear()
    epd7in5_V2.epdconfig.module_exit(cleanup=True)
    exit()

