# NORA Installation Guide

This guide explains how to set up the NORA system on a Raspberry Pi.

## Prerequisites

- Raspberry Pi running Raspbian
- Python 3.x installed

## Installation Steps

1. Clone the repository to your Raspberry Pi:

```bash
cd /home/pi
git clone https://github.com/Hel1umJ/CSE5911_Capstone_Pulse_Patrol.git NORA
cd NORA
```

2. Install required dependencies:

```bash
# Web server dependencies
pip3 install flask

# GUI dependencies
pip3 install pillow matplotlib requests
```

3. Make the startup script executable:

```bash
chmod +x start_nora.sh
```

4. Test the startup script manually:

```bash
./start_nora.sh
```

If both the web server and GUI start successfully, press Ctrl+C to stop them, then continue to the next step.

## Setting Up Autostart with systemd

1. Install the systemd service file:

```bash
sudo cp nora.service /etc/systemd/system/
sudo systemctl daemon-reload
```

2. Enable the service to start at boot:

```bash
sudo systemctl enable nora.service
```

3. Start the service:

```bash
sudo systemctl start nora.service
```

4. Check service status:

```bash
sudo systemctl status nora.service
```