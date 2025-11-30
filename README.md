# Traffic Management System

A comprehensive system that detects vehicles from video feeds and optimizes traffic light timings based on real-time congestion levels.

## Features

- **Vehicle Detection**: Uses YOLOv8 to detect vehicles (cars, trucks, buses, motorcycles) from video feeds
- **Real-time Processing**: Processes video streams in real-time with efficient detection
- **Traffic Light Optimization**: Dynamically adjusts traffic light timings based on vehicle congestion
- **Multi-lane Support**: Supports multiple traffic lights at intersections
- **Congestion Analysis**: Categorizes traffic into low, medium, high, and very high congestion levels

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. The YOLOv8 model (`yolov8n.pt`) will be automatically downloaded on first run, or you can use the existing one in the project.

## Usage

### Web GUI (Recommended)

Launch the NiceGUI web interface:

```bash
python gui.py
```

Or with options:
```bash
python gui.py --video 0 --port 8080
```

Then open your browser to `http://localhost:8080` to access the web interface.

**GUI Features:**
- Real-time video feed with vehicle detection
- Traffic light status for each direction
- Vehicle counts and congestion levels
- Start/Stop controls
- Statistics dashboard

### Command Line Interface

#### Basic Usage (Webcam)
```bash
python main.py
```

#### Using a Video File
```bash
python main.py --video path/to/video.mp4
```

#### Using Specific Camera
```bash
python main.py --video 0  # Camera index
```

#### Without Display (for headless systems)
```bash
python main.py --no-display
```

#### Custom Model
```bash
python main.py --model path/to/custom_model.pt
```

## System Architecture

### Components

1. **GUI Interface** (`gui.py`)
   - NiceGUI web-based interface
   - Real-time video display
   - Traffic light status monitoring
   - System controls and statistics

2. **VehicleDetector** (`vehicle_detector.py`)
   - Detects vehicles using YOLO
   - Tracks vehicle counts over time
   - Determines congestion levels

2. **TrafficLight** (`traffic_light_optimizer.py`)
   - Represents individual traffic lights
   - Calculates optimal green time based on congestion
   - Manages light state transitions

3. **IntersectionController** (`traffic_light_optimizer.py`)
   - Manages multiple traffic lights
   - Optimizes light sequence based on congestion
   - Coordinates light transitions

4. **TrafficManagementSystem** (`traffic_system.py`)
   - Integrates detection and optimization
   - Manages video processing threads
   - Provides system status

## How It Works

1. **Vehicle Detection**: 
   - Video frames are processed through YOLOv8 model
   - Vehicles are detected and counted
   - Detection history is maintained for congestion analysis

2. **Congestion Analysis**:
   - Average vehicle count over recent frames determines congestion level
   - Levels: low (<5), medium (5-15), high (15-30), very high (>30)

3. **Traffic Light Optimization**:
   - Green time is calculated based on vehicle count and congestion level
   - Higher congestion = longer green time (up to maximum limit)
   - Light sequence prioritizes directions with higher congestion

4. **Dynamic Adjustment**:
   - System continuously monitors vehicle counts
   - Green times are adjusted in real-time
   - Light sequence adapts to changing traffic patterns

## Configuration

### Traffic Light Parameters

You can customize traffic lights when creating them:

```python
TrafficLight(
    light_id='north',
    initial_green_time=30,  # Initial green duration (seconds)
    min_green_time=10,      # Minimum green duration
    max_green_time=90        # Maximum green duration
)
```

### Detection Parameters

Adjust detection sensitivity in `VehicleDetector`:

```python
detector = VehicleDetector(
    model_path="models/yolov8n.pt",
    confidence_threshold=0.5  # Detection confidence threshold
)
```

## Example Output

The system displays:
- Real-time vehicle detection with bounding boxes
- Current traffic light state for each direction
- Vehicle count and congestion level
- Time remaining for green lights

## Performance

- Processing speed depends on hardware and video resolution
- YOLOv8n (nano) model provides good balance of speed and accuracy
- For better accuracy, use YOLOv8s, YOLOv8m, or YOLOv8l models

## Requirements

- Python 3.8+
- CUDA-capable GPU (optional, for faster processing)
- Webcam or video file for input

## Notes

- The system uses a single video source for all directions in the demo
- In production, you would use separate cameras for each lane/direction
- Yellow light duration is fixed at 3 seconds
- Red light duration depends on other lights' green times

## License

This project is for educational purposes.

