# rpi4_rs
Wireless networking for Intel Realsense Cameras connected to Raspberry Pi 4 (Model B) units.

## TODO List
- [ ] frames-per-second optimization
- [ ] include instrinsic data with frames
- [ ] parsing realsense config files

## Hardware Requirements
- Intel Realsense camera (tested on D455)
- Raspberry Pi 4 (Model B)
- Wireless Router (tested on a TP-Link Archer C80)

## RPi4 Setup
This repository assumes your Raspberry Pi 4 unit uses Ubuntu 22.04 instead of the original Raspbian OS.

1. Ensure you have the tools needed to build the librealsense SDK on your Pi 4 unit.
```
sudo apt install python3 python3-pip
sudo apt install cmake build-essential
```

2. Run the librealsense SDK installation script.
```
chmod +x ./libuvc_installation.sh
./libuvc_installation.sh
```

3. The Pi 4 unit will be running the `Server.py` script, which requires NumPy.
```
pip3 install numpy
```

## Client Setup
This repository assumes your client is running on a Linux machine with AMD64.

1. Install the librealsense SDK following the guide from the librealsense repository [here](https://github.com/IntelRealSense/librealsense/blob/master/doc/distribution_linux.md). The `dkms` and `utils` packages are sufficient enough.

2. Install Python prerequisites, and the Realsense Python Wrapper.
```
pip3 install numpy opencv-python pyrealsense2
```

## Network Setup
Connect your Pi 4 unit to your wireless router, ensuring it uses a static ip address. Here's a [simple guide](https://linuxconfig.org/how-to-configure-static-ip-address-on-ubuntu-22-04-jammy-jellyfish-desktop-server) to setting a static ip address for your device.

In `client.py` and `server.py`, change the `mc_ip_address` variable to the static ip assigned to your Pi 4 unit.

## Running the Client and Server
1. On your Pi 4, run the `Server.py` script.
2. On your client device, run the `Client.py` script.

Run the script in the exact sequence outlined above.

## Acknowledgement
The client-server scripts are adapted from [EtherSense](https://github.com/krejov100/EtherSense) and the librealsense SDK installation script is adapted from [librealsense](https://github.com/IntelRealSense/librealsense/blob/master/doc/libuvc_installation.md). Thanks to [krehov100](https://github.com/krejov100) for the open-source ethernet networking for Intel Realsense cameras.
