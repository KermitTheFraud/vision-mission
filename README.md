# 🚁 Vision-Based Drone Tracking & Control System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?style=for-the-badge&logo=opencv&logoColor=white)
![Ultralytics](https://img.shields.io/badge/YOLOv11-Ultralytics-orange?style=for-the-badge&logo=yolo&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-lightblue?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-purple?style=for-the-badge&logo=windows&logoColor=white)

**An autonomous drone control system using external camera vision tracking**

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Architecture](#architecture) • [Configuration](#configuration)

</div>

---

## 📋 Overview

This project implements a computer vision-based autonomous drone control system for the DJI Tello drone. Using an external USB camera and a custom-trained YOLO model, the system tracks the drone's position in real-time and enables autonomous navigation through user-defined waypoints.

### 🎯 Key Features

- **External Vision Tracking** - Ground-based camera tracks drone position using YOLOv11
- **GUI Waypoint System** - Interactive overlay for recording flight paths
- **Autonomous Navigation** - Vision-based control with position feedback
- **Multi-threaded Architecture** - Concurrent execution of vision, control, and UI
- **Live Video Feed** - Picture-in-picture drone camera view (Windows)
- **Automatic WiFi Connection** - Seamless drone network switching (Windows)

## 🛠️ Requirements

### Software Dependencies

```bash
# Core Requirements
Python >= 3.8
opencv-python >= 4.5.0
ultralytics >= 8.0.0
numpy >= 1.19.0
tkinter (usually included with Python)

# Platform-specific
pywin32 (Windows only, for Win32 APIs)
```

### Hardware Requirements

- **DJI Tello Drone** (EDU or standard)
- **External USB Camera** (minimum 1080p recommended)
- **Windows 11** (full support) or **macOS** (partial support)
- **WiFi adapter** capable of 2.4GHz connections

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/vision-mission.git
   cd vision-mission
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install opencv-python ultralytics numpy
   
   # Windows only - for drone feed display
   pip install pywin32
   ```

4. **Download YOLO weights**
   - Place your trained `best.pt` file in the project root
   - Or update the path in `yolo.py` (line 13)

## 🚀 Usage

### Quick Start

1. **Connect external camera** (USB port)
2. **Power on Tello drone**
3. **Run the application**
   ```bash
   python main.py
   ```

### Flight Operation

1. **Recording Waypoints**
   - Click `REC` button to start recording
   - Click on the overlay to add waypoints
   - Minimum spacing: 256px horizontal, 144px vertical

2. **Starting Mission**
   - Click `START` to begin autonomous flight
   - System will:
     - Connect to drone WiFi (Windows)
     - Take off to 2000mm altitude
     - Navigate through waypoints
     - Perform victory flips
     - Land automatically

3. **Emergency Stop**
   - Click `STOP` or press `Ctrl+C` to exit
   - Drone will land immediately

### Platform-Specific Notes

#### Windows 11 (Full Support)
- Automatic WiFi switching to drone network
- Live drone camera feed in PIP window
- All features fully functional

#### macOS (Partial Support)
- Manual WiFi connection required
- No drone camera feed (Win32 APIs unavailable)
- Core tracking and control work normally

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   GUI Thread    │     │  Vision Thread   │     │   UDP Thread    │
│  (main.py)      │     │   (yolo.py)      │     │ (udp_logic.py)  │
│                 │     │                  │     │                 │
│  ┌───────────┐  │     │  ┌────────────┐ │     │  ┌───────────┐ │
│  │ Tkinter   │  │────▶│  │   YOLO     │ │────▶│  │  Mission  │ │
│  │ Overlay   │  │     │  │  Tracking  │ │     │  │ Execution │ │
│  └───────────┘  │     │  └────────────┘ │     │  └───────────┘ │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │                         │
        └────────────────────────┴─────────────────────────┘
                          Global Variables
                    (waypoints, drone_location)
```

### Module Structure

```
vision-mission/
├── main.py              # Entry point, thread orchestration
├── gui.py               # Tkinter waypoint recording interface
├── yolo.py              # Vision tracking with YOLO model
├── udp_logic.py         # Mission control and drone commands
├── udp_sender.py        # Low-level UDP communication
├── navigation.py        # Coordinate transformation logic
├── drone_ap_connect.py  # WiFi connection manager (Windows)
├── drone_feed.py        # Drone camera display (Windows)
├── best.pt              # YOLO model weights (not included)
└── README.md            # This file
```

### Thread Communication

- **GUI → UDP**: `destination_list` (waypoint coordinates)
- **Vision → UDP**: `drone_location` (current position)
- **UDP → Drone**: Socket commands via `udp_sender`

## ⚙️ Configuration

### Network Settings

```python
# drone_ap_connect.py
TELLO_SSID = "TELLO-E9C59F"  # Your drone's network name

# udp_sender.py
TELLO_IP = '192.168.10.1'
TELLO_PORT = 8889
LOCAL_IPS = ['192.168.10.2', '192.168.10.3']
```

### Vision Settings

```python
# yolo.py
WEIGHTS = "best.pt"          # Path to YOLO weights
CAM_IDX = 1                  # Camera index (0 or 1)
CONF_THR = 0.5              # Detection confidence threshold
```

### Navigation Parameters

```python
# navigation.py
pixel_ref = 1920            # Reference width in pixels
real_cm_ref = 300           # Real-world width in cm

# udp_logic.py
x_tol = 128                 # Horizontal tolerance (pixels)
y_tol = 72                  # Vertical tolerance (pixels)
```

## 🐛 Troubleshooting

### Common Issues

1. **"No vision data" errors**
   - Check camera index in `yolo.py` (try 0 or 1)
   - Ensure YOLO weights file exists
   - Verify camera is connected

2. **WiFi connection fails (Windows)**
   - Run as administrator
   - Ensure drone SSID matches configuration
   - Check Windows Defender firewall

3. **Drone doesn't respond**
   - Verify IP addresses in `udp_sender.py`
   - Check drone battery level
   - Ensure only one instance running

### Debug Mode

Enable verbose output:
```python
# yolo.py
DEBUG = True  # Shows YOLO inference details
```

## 📊 Technical Details

### Coordinate System

- **GUI**: Screen coordinates (Y-down)
- **Vision**: Inverted Y-axis for logical coordinates
- **Navigation**: 90° rotation applied (right → forward)

### Movement Constraints

- **Minimum movement**: 20cm (commands < 5cm ignored)
- **Waypoint spacing**: 256px horizontal, 144px vertical
- **Edge margins**: 150px from screen borders
- **Takeoff altitude**: 2000mm (auto-ascend if lower)

### Performance

- **Vision**: ~30 FPS @ 1920x1080
- **UDP commands**: 0.5s delay between sends
- **Retry logic**: 3 attempts per waypoint
- **Timeout**: 15 seconds for drone responses

## 🤝 Contributing

This is an exam project for educational purposes. If you're part of the study group:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes with clear messages
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Style

- Use descriptive variable names
- Add inline comments for complex logic
- Document coordinate transformations
- Include platform compatibility notes

## 📝 License

This project is created for educational purposes as part of a university exam project.

## 👥 Authors

- **Your Name** - *Initial development* - [GitHub Profile]

## 🙏 Acknowledgments

- DJI Tello SDK documentation
- Ultralytics YOLOv11 framework
- Study group members for testing and feedback
- Course instructors for project guidance

---

<div align="center">

**Built with ❤️ for autonomous drone navigation**

[Report Bug](https://github.com/yourusername/vision-mission/issues) • [Documentation](https://github.com/yourusername/vision-mission/wiki)

</div>
