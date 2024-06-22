Pico Fridge Monitor
===================

A temperature and door monitor for fridges and freezer. Using a [Raspberry Pi Pico W](https://www.adafruit.com/product/5526), [DS18B20 digital temperature sensors](https://www.adafruit.com/product/374), and [basic reed switches](https://www.adafruit.com/product/375) we can setup a simple http server to report on temperatures and door states. When used with [homebridge-fridge-monitor](https://github.com/codybuell/homebridge-fridge-monitor) you can see everything in Apple's [HomeKit](http://www.apple.com/ios/home/) and even receive alerts when the temperature has crossed above a threshold. For ease of development this project uses [CircuitPython](https://circuitpython.org/), [Adafruit's](https://www.adafruit.com/) take on [MicroPython](https://micropython.org/).

Setup
-----

1. Flash the Pico W with CircuitPython.

    Out of the box the PicoW does not come with CircuitPython. For ease of use version 9 has been vendored in this repository but you can grab the latest [here](https://circuitpython.org/board/raspberry_pi_pico_w/). Note that if you jump versions you may also need to grab updated libraries from [here](https://circuitpython.org/libraries).

    To flash CircuitPython hold the `BOOTSEL` when connecting to your computer, a drive titled `RPI-RP2` should appear. Drag the `firmware/adafruit-circuitpython-raspberry_pi_pico_w-en_US-9.0.5.uf2` file onto the new drive. Once the copy is complete the device will reboot and you'll see a `CIRCUITPY` drive appear.

    One thing to note is that if you are connecting the Pico W to your computer through a hub the order of connections makes a difference. When connecting to a laptop with a Micro USB to USB A cable via a USB A to USB C adapter, if the adapter was connected to the computer last only the `RPI-RP2` mount would appear. To get the `CIRCUITPY` mount to appear the adapter had to be connected to the laptop first, then the USB A cable connected in. 🤷

2. Upload files to the Pico W.

    Edit the `dist/settings.toml` file with your wifi information. Drag the contents of the `dist` folder to the `CIRCUITPY` drive.

3. Determine the `DS18B20` temperature sensor ROM codes.

    The digital temperature sensor uses the Dallas 1-wire protocol meaning that you can have more than one (think fridge freezer combo) sensor going into one pin on the Pico W. The challenge here is that to distinguish between each sensor and therefore identify which is the fridge vs freezer for example, you need to know the ROM code that is burned in at the factory for each sensor. If you are only using one temperature sensor you can skip this step.

    Take one of the `DS18B20` sensor and connect ground to ground, DQ to `GP6,` and Vdd to 3V3. Jump DQ and Vdd with a 4.7k resistor. Boot up the PicoW and pull up a serial console. As the divice boots it will print out something like the following:

    ```text
    Connected to WiFi: 192.168.1.10
    Connected 1-wire devices:
      bytearray(b'(\r\xa7\xaa\x05\x00\x00\xb1')
    Listening on http://192.168.101.49:80
    ```

    Grab the byte array, in the example above `b'(\r\xa7\xaa\x05\x00\x00\xb1'`. Edit `dist/code.py` and set it to `FRIDGE_ROM` or `FREEZER_ROM` and mark the sensor so you'll remember which is which. Repeat for the second sensor.

    Also make note of the IP address.

4. Connect the sensors.

    Wire up everything. Both temperature sensors will share all pins as called out in the previous step. Reed switches will be `GP7` for the fridge, and `GP8` for the freezer. If you need to use another pin be sure to update `dist/code.py`.

5. Make any additional adjustments to `dist/code.py` per your setup and copy it over to the `CIRCUITPY` drive.
7. Install onto your fridge.


Development
-----------

One handy tool when working with MicroPython or CircuitPython is `rshell`:

```bash
pip3 install rshell
rshell -p /dev/tty.usbmodem1322[???] --buffer-size 512
> repl
> ctrl + d (reboots device and you see all console output)
> ctrl + x to exit repl
> ctrl + d to exit rshell
```

Interface
---------

The http server presents three endpoints. `/` returns information for both fridge and freezer, `/fridge` and `/freezer` return only their states. If using with [homebridge-fridge-monitor](https://github.com/codybuell/homebridge-fridge-monitor) you would configure the plugin to hit `/fridge` or `/freezer`, eg `http://192.168.1.10/fridge`.

`/`
```json
{
  "fridge": {
    "temp_f": "77.34",
    "temp_c": "25.19",
    "door_open": true
  },
  "freezer": {
    "temp_f": "77.45",
    "temp_c": "25.25",
    "door_open": true
  }
}
```

`/fridge`, `/freezer`
```json
{
  "temp_f": "77.34",
  "temp_c": "25.19",
  "door_open": true
}
```
