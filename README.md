# E-Ink Bus Picture Frame
![Bus Timing E-ink Display](https://drive.usercontent.google.com/download?id=1zQvAToLZ3Cnxs84Y6a4Uk20vn-1cJqk0)

Living in Singapore, I'm truly blessed having access to public transportation that is cheap, 'reliable' and consistent. As much as most of us would complain about it everyday, it is a constant necessity that most of us take for granted. 

Based on the idea from [Weatherman Dashboard for ESPHome](https://community.home-assistant.io/t/use-esphome-with-e-ink-displays-to-blend-in-with-your-home-decor/435428), I wanted to make something similar but using a Raspberry Pi Zero with a Waveshare 7.5inch E-Ink display.

This project creates an E-Ink display that shows real-time bus arrival times and train disruption information using data from Singapore's Land Transport Authority (LTA) DataMall API.

## Things you will need
1. [Raspberry Pi Zero W](https://s.click.aliexpress.com/e/_oCx7W6d)
2. [Waveshare 7.5inch E-Ink Display (EPD 7in5 V2)](https://s.click.aliexpress.com/e/_oCtHZjx) 
3. 40-pin GPIO headers for the Raspberry Pi Zero. I chose to solder it onto the board
4. [3D Printed Case](https://www.thingiverse.com/thing:3996613) or an [IKEA Ribba 7x5 picture frame](https://shorturl.at/pmxf3)
3. 5V 3A power supply
4. [Micro USB flat cable](https://s.click.aliexpress.com/e/_oEFqXSD)
5. 4GB or more SD card


## Setup

1. Clone this repository to your Raspberry Pi.
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Rename the `.env.example` file to `.env` in the project root

4. Replace `your_lta_api_key` with your LTA DataMall API key, and `your_first_bus_stop_code` and `your_second_bus_stop_code` with the desired bus stop codes.
   ```
   API_KEY=your_lta_api_key //Get this from LTA DataMall
   BUS_STOP_CODE_A=your_first_bus_stop_code
   BUS_STOP_CODE_B=your_second_bus_stop_code
   ```

## Usage

Run the main script: 
```
python3 app/main.py
```

Alternatively, you can run the script automatically every time the system boots, you can set it up as a startup service using `systemd` on Linux-based systems, such as Raspberry Pi or Ubuntu. Here’s how you can do it:


1. **Create a systemd service file**:
   - Open a terminal.
   - Use a text editor like `nano` to create a new service file:

     ```bash
     sudo nano /etc/systemd/system/bus_display.service
     ```

2. **Add the following content to the service file**:

    ```ini
    [Unit]
    Description=E-Ink Bus Display Service
    After=multi-user.target

    [Service]
    ExecStart=/usr/bin/python3 /path/to/your/app/main.py
    WorkingDirectory=/path/to/your/
    StandardOutput=inherit
    StandardError=inherit
    Restart=always
    User=pi

    [Install]
    WantedBy=multi-user.target
    ```

    - **ExecStart**: Replace `/path/to/your/script.py` with the full path to your Python script.
    - **WorkingDirectory**: Replace `/path/to/your/` with the directory containing your script.
    - **User**: Replace `pi` with the username under which the script should run, if different.
    - `Restart=always` ensures that the service restarts if it fails.

3. **Save and exit**:
   - Press `Ctrl + X`, then `Y`, and then `Enter` to save and exit `nano`.

### Step 2: Enable the Service

1. **Reload systemd to recognize the new service**:

    ```bash
    sudo systemctl daemon-reload
    ```

2. **Enable the service to start on boot**:

    ```bash
    sudo systemctl enable bus_display.service
    ```

3. **Start the service immediately (optional)**:

    ```bash
    sudo systemctl start bus_display.service
    ```

4. **Check the status of the service**:

    ```bash
    sudo systemctl status bus_display.service
    ```

    This command will show whether the service is active and running.
