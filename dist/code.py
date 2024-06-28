import os
import wifi
import board
import digitalio
import socketpool
import ipaddress

from adafruit_httpserver import Server, Request, JSONResponse
from adafruit_onewire.bus import OneWireBus, OneWireAddress
from adafruit_ds18x20 import DS18X20

################################################################################
##                                                                            ##
##  Configuration                                                             ##
##                                                                            ##
################################################################################

# dhcp or static ip address
static_ip  = False
ip_address = "192.168.1.242"
netmask    = "255.255.255.0"
gateway    = "192.168.1.1"

# what units are we monitoring
units = ["fridge", "freezer"]

# door reed switch connections
fridge_door_pin  = board.GP7
freezer_door_pin = board.GP8

# temp sensor ROM codes, only needed if monitoring multiple sensors
FRIDGE_ROM  = b"(dY\xaa\x05\x00\x00\xe0"
FREEZER_ROM = b"(\r\xa7\xaa\x05\x00\x00\xb1"

################################################################################
##                                                                            ##
##  Functions                                                                 ##
##                                                                            ##
################################################################################


# convert celcius to fahrenheit
def c_to_f(temp):
    temp_f = (temp * 9 / 5) + 32
    return temp_f


# read the temperature
def read_temp(device):
    print(f"Reading {device} temperature...")
    temperature = device.temperature
    data = {
        "temp_f": float(f"{c_to_f(temperature):.2f}"),
        "temp_c": float(f"{temperature:.2f}"),
    }
    print(" ", data)
    return data


################################################################################
##                                                                            ##
##  Setup                                                                     ##
##                                                                            ##
################################################################################

# conditionally set static ip
if static_ip:
    ipv4 = ipaddress.IPv4Address(ip_address)
    nm   = ipaddress.IPv4Address(netmask)
    gw   = ipaddress.IPv4Address(gateway)
    wifi.radio.set_ipv4_address(ipv4=ipv4, netmask=nm, gateway=gw)

# initialize network connection
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))
print(f"Connected to WiFi: {wifi.radio.ipv4_address}")

# fridge reed switch setup
fridge_reed_switch = digitalio.DigitalInOut(fridge_door_pin)
fridge_reed_switch.direction = digitalio.Direction.INPUT
fridge_reed_switch.pull = digitalio.Pull.UP

# freezer reed switch setup
freezer_reed_switch = digitalio.DigitalInOut(freezer_door_pin)
freezer_reed_switch.direction = digitalio.Direction.INPUT
freezer_reed_switch.pull = digitalio.Pull.UP

# server setup
pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static", debug=False)

# one-wire bus for DS18B20
ow_bus = OneWireBus(board.GP6)

# print currently attached ROMs
print("Connected 1-wire devices:")
for device in ow_bus.scan():
    print(" ", device.rom)

if len(units) > 1:
    # assign our sensor addresses
    fridge  = DS18X20(ow_bus, OneWireAddress(FRIDGE_ROM))
    freezer = DS18X20(ow_bus, OneWireAddress(FREEZER_ROM))
else:
    # if only one sensor: scan for temp sensor
    fridge  = freezer
    freezer = DS18X20(ow_bus, ow_bus.scan()[0])

################################################################################
##                                                                            ##
##  Routes                                                                    ##
##                                                                            ##
################################################################################


# root
@server.route('/')
def default_route(request: Request):
    print("Received request: ", request)
    fridge_data  = read_temp(fridge)
    freezer_data = read_temp(freezer)
    fridge_data["door_open"]  = fridge_reed_switch.value
    freezer_data["door_open"] = freezer_reed_switch.value
    data = {
        "fridge": fridge_data,
        "freezer": freezer_data,
    }
    return JSONResponse(request, data)


# fridge
@server.route('/fridge')
def fridge_route(request: Request):
    print("Received request: ", request)
    fridge_data  = read_temp(fridge)
    fridge_data["door_open"]  = fridge_reed_switch.value
    return JSONResponse(request, fridge_data)


# freezer
@server.route('/freezer')
def freezer_route(request: Request):
    print("Received request: ", request)
    freezer_data = read_temp(freezer)
    freezer_data["door_open"] = freezer_reed_switch.value
    return JSONResponse(request, freezer_data)


################################################################################
##                                                                            ##
##  Run                                                                       ##
##                                                                            ##
################################################################################

# run server
print("Listening on http://%s:80" % wifi.radio.ipv4_address)
server.serve_forever(str(wifi.radio.ipv4_address), 80)
