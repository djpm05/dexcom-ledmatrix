import time
import board
import displayio
import terminalio
from adafruit_display_text import label
from adafruit_matrixportal.matrix import Matrix
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_connection_manager
import adafruit_requests
import busio
from digitalio import DigitalInOut
import os

# Get credentials from settings.toml
DEXCOM_USERNAME = os.getenv("DEXCOM_USERNAME")
DEXCOM_PASSWORD = os.getenv("DEXCOM_PASSWORD")
DEXCOM_REGION = os.getenv("DEXCOM_REGION", "us")  # Default to "us" if not specified
HIGH_THRESHOLD = os.getenv("HIGH_THRESHOLD")
LOW_THRESHOLD = os.getenv("LOW_THRESHOLD")
PANEL_CHANGE_INTERVAL = os.getenv("PANEL_CHANGE_INTERVAL")

# Dexcom API Configuration
if DEXCOM_REGION == "ous":
    BASE_URL = "https://shareous1.dexcom.com/ShareWebServices/Services"
elif DEXCOM_REGION == "jp":
    BASE_URL = "https://shareous1.dexcom.jp/ShareWebServices/Services"
else:
    BASE_URL = "https://share2.dexcom.com/ShareWebServices/Services"

APPLICATION_ID = "d89443d2-327c-4a6f-89e5-496bbb0317db"

# Matrix setup using MatrixPortal library
matrix = Matrix(width=32, height=16)
display = matrix.display

# Create main group
main_group = displayio.Group()
display.root_group = main_group

# Arrow bitmaps (13x13 pixels each)
ARROW_BITMAPS = {
    "doubleup": [
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,1,1,1,1,1,0,0,0,0],
        [0,0,0,1,1,1,1,1,1,1,0,0,0],
        [0,0,1,1,1,1,1,1,1,1,1,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
    ],
    "singleup": [
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,1,0,1,0,1,0,0,0,0],
        [0,0,0,1,0,0,1,0,0,1,0,0,0],
        [0,0,1,0,0,0,1,0,0,0,1,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
    ],
    "fortyFiveup": [
        [0,0,0,0,0,0,0,0,1,1,1,1,1],
        [0,0,0,0,0,0,0,0,0,0,0,1,1],
        [0,0,0,0,0,0,0,0,0,0,1,0,1],
        [0,0,0,0,0,0,0,0,0,1,0,0,1],
        [0,0,0,0,0,0,0,0,1,0,0,0,1],
        [0,0,0,0,0,0,0,1,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,1,0,0,0,0,0,0,0],
        [0,0,0,0,1,0,0,0,0,0,0,0,0],
        [0,0,0,1,0,0,0,0,0,0,0,0,0],
        [0,0,1,0,0,0,0,0,0,0,0,0,0],
        [0,1,0,0,0,0,0,0,0,0,0,0,0],
        [1,0,0,0,0,0,0,0,0,0,0,0,0],
    ],
    "flat": [
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,1,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,1,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,1,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,1,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,1,0],
        [1,1,1,1,1,1,1,1,1,1,1,1,1],
        [0,0,0,0,0,0,0,0,0,0,0,1,0],
        [0,0,0,0,0,0,0,0,0,0,1,0,0],
        [0,0,0,0,0,0,0,0,0,1,0,0,0],
        [0,0,0,0,0,0,0,0,1,0,0,0,0],
        [0,0,0,0,0,0,0,1,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
    ],
    "fortyFivedown": [
        [1,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,1,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,1,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,1,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,1,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,1,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,1,0,0,0,1],
        [0,0,0,0,0,0,0,0,0,1,0,0,1],
        [0,0,0,0,0,0,0,0,0,0,1,0,1],
        [0,0,0,0,0,0,0,0,0,0,0,1,1],
        [0,0,0,0,0,0,0,0,1,1,1,1,1],
    ],
    "singledown": [
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
        [0,0,1,0,0,0,1,0,0,0,1,0,0],
        [0,0,0,1,0,0,1,0,0,1,0,0,0],
        [0,0,0,0,1,0,1,0,1,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
    ],
    "doubledown": [
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,1,1,1,1,1,1,1,1,1,0,0],
        [0,0,0,1,1,1,1,1,1,1,0,0,0],
        [0,0,0,0,1,1,1,1,1,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,0,1,0,0,0,0,0,0],
    ],
    "unknown": [
        [0,0,0,1,1,1,1,1,1,1,0,0,0],
        [0,0,1,1,1,1,1,1,1,1,1,0,0],
        [0,1,1,1,0,0,0,0,0,1,1,1,0],
        [0,1,1,0,0,0,0,0,0,0,1,1,0],
        [0,0,0,0,0,0,0,0,1,1,1,0,0],
        [0,0,0,0,0,0,1,1,1,1,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0,0],
    ],
}

def show_message(message):
    # Clear the main group
    while len(main_group) > 0:
        main_group.pop()
    
    message_label = label.Label(
        terminalio.FONT,
        text=message,
        color=0x143445,
        scale=1
    )
    message_label.x = 32  # Start off-screen to the right
    message_label.y = 8
    main_group.append(message_label)
    
    # Scroll the message across the screen
    text_width = len(message) * 6  # Approximate width
    for x in range(32, -text_width, -1):
        message_label.x = x
        time.sleep(0.03)
    

# ESP32 SPI WiFi setup
show_message("Connecting...")
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

# Connect to WiFi
print("Connecting to WiFi...")
WIFI_SSID = os.getenv("CIRCUITPY_WIFI_SSID")
WIFI_PASSWORD = os.getenv("CIRCUITPY_WIFI_PASSWORD")
while not esp.is_connected:
    try:
        esp.connect_AP(WIFI_SSID, WIFI_PASSWORD)
    except ConnectionError as e:
        print("Could not connect to WiFi, retrying:", e)
        show_message("WiFi retrying...")
        time.sleep(1)
        continue
print("Connected!")
show_message("Connected!")

# Setup requests
pool = adafruit_connection_manager.get_radio_socketpool(esp)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(esp)
requests = adafruit_requests.Session(pool, ssl_context)

# Create main group (reset after messages)
main_group = displayio.Group()
display.root_group = main_group

# Trend arrows and descriptions
TREND_ARROWS = {
    "none": "?",
    "unknown": "?",
    "doubleup": "↑↑",
    "singleup": "↑",
    "fortyFiveup": "↗",
    "flat": "→",
    "fortyFivedown": "↘",
    "singledown": "↓",
    "doubledown": "↓↓",
    "notcomputable": "?",
    "rateoutofrange": "?",
    # Also support numeric values for backwards compatibility
    1: "↑↑",
    2: "↑",
    3: "↗",
    4: "→",
    5: "↘",
    6: "↓",
    7: "↓↓",
    8: "?",
    9: "?",
}

def get_color(value):
    if value < int(LOW_THRESHOLD):
        return 0xFF0000  # Red
    elif value <= int(HIGH_THRESHOLD):
        return 0x00FF00  # Green
    else:
        return 0xFFFF00  # Yellow

def dexcom_login():
    print("Logging into Dexcom...")
    show_message("Logging in...")
    
    # Step 1: Get Account ID
    account_url = f"{BASE_URL}/General/AuthenticatePublisherAccount"
    account_data = {
        "accountName": DEXCOM_USERNAME,
        "password": DEXCOM_PASSWORD,
        "applicationId": APPLICATION_ID
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Dexcom Share/3.0.2.11 CFNetwork/711.2.23 Darwin/14.0.0"
    }
    
    response = requests.post(account_url, json=account_data, headers=headers)
    account_id = response.text.strip('"')
    response.close()
    
    # Step 2: Get Session ID
    session_url = f"{BASE_URL}/General/LoginPublisherAccountById"
    session_data = {
        "accountId": account_id,
        "password": DEXCOM_PASSWORD,
        "applicationId": APPLICATION_ID
    }
    
    response = requests.post(session_url, json=session_data, headers=headers)
    session_id = response.text.strip('"')
    response.close()
    
    print("Login successful!")
    return session_id

def get_glucose_readings(session_id, max_count=32):
    url = f"{BASE_URL}/Publisher/ReadPublisherLatestGlucoseValues"
    params = f"?sessionId={session_id}&minutes=1440&maxCount={max_count}"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Dexcom Share/3.0.2.11 CFNetwork/711.2.23 Darwin/14.0.0"
    }
    
    response = requests.get(url + params, headers=headers)
    data = response.json()
    response.close()
    
    return data

def show_current_reading(value, trend):
    # Clear the main group
    while len(main_group) > 0:
        main_group.pop()
    
    color = get_color(value)
    # Convert trend to lowercase for case-insensitive matching
    trend_key = trend.lower() if isinstance(trend, str) else trend
    
    # Get arrow bitmap
    arrow_pattern = ARROW_BITMAPS.get(trend_key, ARROW_BITMAPS["unknown"])
    
    # Create value text
    value_text = label.Label(
        terminalio.FONT,
        text=str(value),
        color=color,
        scale=1
    )
    value_text.x = 0
    value_text.y = 8
    main_group.append(value_text)
    
    # Create arrow bitmap (13x13)
    arrow_bitmap = displayio.Bitmap(13, 13, 2)
    arrow_palette = displayio.Palette(2)
    arrow_palette[0] = 0x000000  # Background
    arrow_palette[1] = color  # Arrow color
    
    for y in range(13):
        for x in range(13):
            if arrow_pattern[y][x] == 1:
                arrow_bitmap[x, y] = 1
    
    arrow_grid = displayio.TileGrid(arrow_bitmap, pixel_shader=arrow_palette, x=18, y=1)
    main_group.append(arrow_grid)

def show_graph(readings):
    # Clear the main group
    while len(main_group) > 0:
        main_group.pop()
    
    # Create a bitmap for the graph
    bitmap = displayio.Bitmap(32, 16, 4)
    
    # Define palette with colors
    palette = displayio.Palette(4)
    palette[0] = 0x000000  # Black (background)
    palette[1] = 0xFF0000  # Red
    palette[2] = 0x00FF00  # Green
    palette[3] = 0xFFFF00  # Yellow
    
    # Plot readings from left to right (oldest on left, newest on right)
    num_readings = min(len(readings), 32)
    for i in range(num_readings):
        reading = readings[num_readings - 1 - i]  # Reverse order so newest is on right
        value = reading.get('Value', 0)
        
        # Map glucose value (30-300 range) to pixel height (0-15)
        y = int(((value - 30) / (300 - 30)) * 15)
        y = max(0, min(15, y))  # Clamp to display height
        y = 15 - y  # Invert Y (0 is top)
        
        x = i  # Plot from left to right
        
        # Determine color based on value
        if value < int(LOW_THRESHOLD):
            color_index = 1  # Red
        elif value <= int(HIGH_THRESHOLD):
            color_index = 2  # Green
        else:
            color_index = 3  # Yellow
        
        bitmap[x, y] = color_index
    
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)
    main_group.append(tile_grid)

# Main loop
session_id = None
last_refresh = 0
REFRESH_INTERVAL = 300  # 5 minutes
show_number = True  # Toggle between number and graph
last_display_switch = 0

print("Starting Dexcom display...")

try:
    while True:
        current_time = time.monotonic()
        
        # Refresh session and data every 5 minutes
        if session_id is None or (current_time - last_refresh) > REFRESH_INTERVAL:
            try:
                session_id = dexcom_login()
                readings = get_glucose_readings(session_id, 32)
                last_refresh = current_time
                
                if readings and len(readings) > 0:
                    latest = readings[0]
                    value = latest.get('Value', 0)
                    trend = latest.get('Trend', 0)
                    
                    print(f"Glucose: {value} mg/dL, Trend: {TREND_ARROWS.get(trend.lower() if isinstance(trend, str) else trend, '?')}")
                    print(f"\nAll {len(readings)} readings (newest to oldest):")
                    for i, reading in enumerate(readings):
                        val = reading.get('Value', 0)
                        tr = reading.get('Trend', 0)
                        # Convert trend to lowercase for case-insensitive matching
                        trend_key = tr.lower() if isinstance(tr, str) else tr
                        arrow = TREND_ARROWS.get(trend_key, '?')
                        print(f"  {i+1}. Value: {val} mg/dL, Trend: {tr} ({arrow})")
                    print()
                    
            except Exception as e:
                print(f"Error: {e}")
                show_message(f"Error: {str(e)[:20]}")
                session_id = None  # Force re-login on next iteration
                time.sleep(60)  # Wait a minute before retrying
                continue
        
        # Switch between number and graph every PANEL_CHANGE_INTERVAL seconds
        if readings and len(readings) > 0 and (current_time - last_display_switch) >= int(PANEL_CHANGE_INTERVAL):
            latest = readings[0]
            value = latest.get('Value', 0)
            trend = latest.get('Trend', 0)
            
            if show_number:
                show_current_reading(value, trend)
            else:
                show_graph(readings)
            
            show_number = not show_number
            last_display_switch = current_time
        
        time.sleep(0.1)  # Small delay in main loop

except KeyboardInterrupt:
    print("Stopped by user")
