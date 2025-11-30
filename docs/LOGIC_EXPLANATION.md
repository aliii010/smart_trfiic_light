# Traffic Light Dashboard - Logic Explanation

This document explains the core logic of the Traffic Light Dashboard application, including how different media sources are processed, vehicle detection works, and the traffic light state machine operates.

## Table of Contents
1. [Media Source Processing](#media-source-processing)
2. [Vehicle Detection System](#vehicle-detection-system)
3. [Traffic Light State Machine](#traffic-light-state-machine)
4. [Congestion-Based Timing Logic](#congestion-based-timing-logic)
5. [Overall Business Logic Flow](#overall-business-logic-flow)

---

## Media Source Processing

The application supports three types of media sources: **Images**, **Videos**, and **RTSP streams**. Each is handled differently based on its characteristics.

### Image Processing

**Location:** `traffic_light_dashboard.py` - `stream_media()` function (lines 79-104)

**How it works:**
1. When an image source is selected, the system reads the image file using `cv2.imread()`
2. The image is immediately processed for vehicle detection:
   ```python
   frame = cv2.imread(source_path)
   vehicle_count, annotated_frame = count_cars_from_frame(frame)
   ```
3. The detection happens **once** when the image is loaded
4. The annotated frame (with bounding boxes) is displayed as a static image
5. Vehicle count is updated immediately and used to calculate traffic light timing

**Key Code:**
```python
if source_type == 'image':
    frame = cv2.imread(source_path)
    if frame is not None:
        current_frame['value'] = frame
        vehicle_count, annotated_frame = count_cars_from_frame(frame)
        update_vehicle_count(vehicle_count)
        calculate_and_store_max_time()
        # Display annotated frame as base64 encoded image
        img_base64 = frame_to_base64(annotated_frame)
        media_static_image.source = f'data:image/jpeg;base64,{img_base64}'
```

**Characteristics:**
- Single-frame processing
- Detection runs immediately on load
- Result is static (no continuous updates)
- Uses `ui.image` component for display

---

### Video Processing

**Location:** `traffic_light_dashboard.py` - `stream_media()` function (lines 106-160)

**How it works:**
1. Video file is validated and opened using `cv2.VideoCapture()`
2. The video is served through HTTP using a FastAPI endpoint (`/video`)
3. The HTML5 `<video>` element plays the video file directly
4. **Background frame processing** runs in parallel:
   - Frames are continuously read from the video
   - Current frame is stored in `current_frame['value']` for detection
   - Detection is **not** run on every frame - only when traffic light color changes
5. When the video ends, it loops back to the beginning

**Key Code:**
```python
if source_type == 'video':
    # Serve video through HTTP
    encoded_path = urllib.parse.quote(source_path, safe='')
    video_url = f'/video?file_path={encoded_path}'
    media_video.source = video_url
    
    # Background frame processing
    cap = cv2.VideoCapture(str(video_path))
    async def process_video_frames():
        while is_streaming['value']:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop video
                continue
            current_frame['value'] = frame  # Store for detection
            await asyncio.sleep(0.1)  # Process every 100ms
```

**Characteristics:**
- Continuous frame extraction in background
- Video playback via HTML5 video element
- Detection triggered by traffic light state changes (not every frame)
- Efficient processing (only stores frames, doesn't detect on every frame)

---

### RTSP Stream Processing

**Location:** `traffic_light_dashboard.py` - `stream_media()` function (lines 162-209)

**How it works:**
1. RTSP stream is opened using `cv2.VideoCapture()` with `cv2.CAP_FFMPEG`
2. Buffer size is set to 1 to reduce latency: `cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)`
3. **Continuous frame processing** runs in an async loop:
   - Frames are read at ~30 FPS (every 33ms)
   - Each frame is converted to base64 and displayed via `ui.interactive_image`
   - Current frame is stored for detection triggers
4. If connection is lost, the system attempts to reconnect
5. Detection runs when traffic light color changes (red/green transitions)

**Key Code:**
```python
# RTSP stream
cap = cv2.VideoCapture(source_path, cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce latency

async def process_rtsp_frames():
    while is_streaming['value']:
        ret, frame = cap.read()
        if not ret:
            await asyncio.sleep(1)  # Reconnect attempt
            continue
        current_frame['value'] = frame  # Store for detection
        img_base64 = frame_to_base64(frame)
        media_image.source = f'data:image/jpeg;base64,{img_base64}'
        await asyncio.sleep(0.033)  # ~30 FPS
```

**Characteristics:**
- Real-time streaming with low latency
- Continuous frame updates to UI
- Automatic reconnection on connection loss
- Uses `ui.interactive_image` for efficient updates
- Detection triggered by state changes, not every frame

---

## Vehicle Detection System

**Location:** `model.py`

### Detection Model

The system uses **YOLOv8** (YOLO - You Only Look Once) for object detection:
- Model file: `yolov8n.pt` (nano version for speed)
- Framework: Ultralytics YOLO
- Annotation: Supervision library for bounding boxes and labels

### Detection Process

**Function:** `count_cars_from_frame(frame: np.ndarray)`

**How it works:**
1. Frame is passed to YOLO model: `res = model(frame, verbose=False)`
2. Detections are extracted using Supervision: `sv.Detections.from_ultralytics(res[0])`
3. **Filtering:** Only specific vehicle classes are counted:
   - Class ID 2: Car
   - Class ID 5: Bus
   - Class ID 7: Truck
4. Annotated frame is created with bounding boxes and labels
5. Returns: `(vehicle_count, annotated_frame)`

**Key Code:**
```python
def count_cars_from_frame(frame: np.ndarray) -> tuple[int, None] | tuple[int, ndarray]:
    res = model(frame, verbose=False)
    detections = sv.Detections.from_ultralytics(res[0])
    # Filter for vehicles only (car, bus, truck)
    detections = detections[(detections.class_id == 2) | 
                           (detections.class_id == 5) | 
                           (detections.class_id == 7)]
    
    car_count = len(detections.class_id)
    
    # Annotate frame with boxes and labels
    annotated = frame.copy()
    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()
    annotated = box_annotator.annotate(annotated, detections)
    annotated = label_annotator.annotate(annotated, detections, labels)
    
    return car_count, annotated
```

### When Detection Runs

Detection is **not** run on every frame. Instead, it's triggered strategically:

1. **For Images:** Immediately when image is loaded
2. **For Videos/RTSP:** When traffic light transitions to **Red** or **Green**
   - Detection flag is set in `controller.py` when color changes
   - UI timer checks this flag and runs detection if needed
   - This prevents unnecessary computation while maintaining accuracy

**Trigger Logic:**
```python
# In controller.py - when color changes
def set_color_red():
    detection_needed['value'] = True  # Trigger detection

def set_color_green():
    detection_needed['value'] = True  # Trigger detection

# In info_pannel.py - UI update loop
if should_trigger_detection() and current_frame['value'] is not None:
    vehicle_count, _ = count_cars_from_frame(current_frame['value'])
    update_vehicle_count(vehicle_count)
    calculate_and_store_max_time()
    clear_detection_flag()
```

---

## Traffic Light State Machine

**Location:** `controller.py` - `traffic_light_state_machine()` function

### State Transitions

The traffic light follows a standard cycle:
1. **Red** → **Green** (after red timer expires)
2. **Green** → **Yellow** (after green timer expires)
3. **Yellow** → **Red** (after yellow timer expires)

### Base Timing

Default durations for each state:
```python
lights = {
    "red": 10,    # 10 seconds base
    "yellow": 3,  # 3 seconds (fixed)
    "green": 5    # 5 seconds base
}
```

**Note:** Yellow time is always 3 seconds (fixed). Red and Green times are adjusted based on congestion.

### State Machine Loop

**How it works:**
1. Runs continuously in an async loop
2. Checks elapsed time every 100ms
3. When `elapsed >= max_time`, transitions to next state
4. Each state change:
   - Resets the state start time
   - Clears stored max time (forces recalculation)
   - Sets detection flag (for red/green transitions)

**Key Code:**
```python
async def traffic_light_state_machine():
    traffic_light_running['value'] = True
    
    while traffic_light_running['value']:
        current_state = active_color['value']
        max_time = get_max_time()
        elapsed = time.time() - state_start_time['value']
        
        if elapsed >= max_time:
            if current_state == "red":
                set_color_green()
            elif current_state == "green":
                set_color_yellow()
            elif current_state == "yellow":
                set_color_red()
        
        await asyncio.sleep(0.1)  # Check every 100ms
```

---

## Congestion-Based Timing Logic

**Location:** `controller.py`

### Congestion Levels

Vehicle count determines congestion level:
```python
def get_congestion(counter):
    if counter > 15:
        return 'very_high'
    elif counter > 10:
        return 'high'
    elif counter > 5:
        return 'medium'
    else:
        return 'low'
```

### Congestion Multipliers

Each congestion level has a multiplier that affects timing:
```python
congestion_multipliers = {
    'low': 0,        # No adjustment
    'medium': 0.2,   # 20% adjustment
    'high': 0.5,     # 50% adjustment
    'very_high': 0.8 # 80% adjustment
}
```

### Time Calculation

**For Red Light:**
- Higher congestion = **shorter** red time (to clear traffic faster)
- Formula: `max_time = base_time - (base_time * multiplier)`
- Example: 10s base, very_high congestion → 10 - (10 * 0.8) = 2 seconds

**For Green Light:**
- Higher congestion = **longer** green time (to allow more vehicles through)
- Formula: `max_time = base_time + (base_time * multiplier)`
- Example: 5s base, very_high congestion → 5 + (5 * 0.8) = 9 seconds

**Key Code:**
```python
def calculate_and_store_max_time():
    state = active_color['value']
    congestion = get_congestion(count['value'])
    multiplier = congestion_multipliers.get(congestion, 1.0)
    base_time = lights.get(state, 5)
    i = int(base_time * multiplier)
    
    if state == "red":
        max_time = base_time - i  # Decrease for red
    else:
        max_time = i + base_time  # Increase for green
    
    stored_max_time['value'] = max_time
    return max_time
```

**Important:** The max time is calculated **once** when the state changes and stored. This ensures consistent timing throughout the state duration, even if vehicle count changes.

---

## Overall Business Logic Flow

### Application Startup
1. NiceGUI web server starts on port 8188
2. Main page loads with two sections:
   - Scene section (media display)
   - Traffic section (traffic light and info)

### Media Loading Flow
1. User selects media type (image/video/RTSP) and provides path
2. `stream_media()` function is called
3. Based on type:
   - **Image:** Load, detect, display
   - **Video:** Open file, start background processing, serve via HTTP
   - **RTSP:** Open stream, start continuous frame processing
4. Traffic light state machine starts automatically (if not already running)

### Detection and Timing Flow
1. **Initial State:** Traffic light starts at Red
2. **On Red/Green Transition:**
   - Detection flag is set (`detection_needed = True`)
   - UI timer (runs every 500ms) checks the flag
   - If flag is set and frame exists:
     - Run vehicle detection on current frame
     - Update vehicle count
     - Calculate congestion level
     - Calculate and store max time for current state
     - Clear detection flag
3. **During State:**
   - State machine checks elapsed time every 100ms
   - Max time remains constant (stored value)
   - UI updates every 500ms (time remaining, congestion, etc.)
4. **State Transition:**
   - When timer expires, transition to next state
   - Reset stored max time
   - Set detection flag (for red/green)
   - Cycle repeats

### UI Update Flow
**Location:** `components/info_pannel.py` - `update_ui()` function

Runs every 500ms and updates:
1. **Traffic Light:** Visual state and blinking (for yellow)
2. **Vehicle Count:** Latest detected count
3. **Congestion Level:** Badge with color coding
4. **Time Remaining:** Countdown for current state
5. **Max Time Display:** Total duration for current state

### Yellow Light Blinking
- Yellow light blinks (toggles visibility) every 500ms
- Blink state is managed in `yellow_blink_state['value']`
- Provides visual indication that yellow is active

---

## Key Design Decisions

### Why Detection on State Change Only?
- **Performance:** YOLO detection is computationally expensive
- **Accuracy:** Detecting at state transitions captures the relevant traffic situation
- **Efficiency:** Avoids unnecessary processing on every frame

### Why Store Max Time?
- **Consistency:** Timing doesn't change mid-state, preventing confusion
- **Predictability:** Users see consistent countdown
- **Logic:** Congestion is assessed at state start, not continuously

### Why Different Display Methods?
- **Image:** Static display (no updates needed)
- **Video:** HTML5 video element (native playback, efficient)
- **RTSP:** Interactive image (real-time updates, low latency)

### Why Background Frame Processing?
- **Separation of Concerns:** Display and detection are decoupled
- **Performance:** Video playback doesn't block detection processing
- **Flexibility:** Can process frames at different rates than display

---

## Code Structure Summary

```
traffic_light_dashboard.py
├── Media source handling (open_media_source, stream_media)
├── Frame conversion (frame_to_base64)
├── UI components (scene_section, traffic_section)
└── HTTP endpoints (/video)

model.py
└── Vehicle detection (count_cars_from_frame)

controller.py
├── Traffic light state machine (traffic_light_state_machine)
├── Timing calculations (get_max_time, calculate_and_store_max_time)
├── Congestion logic (get_congestion)
└── State management (set_color_*, get_current_color)

components/
├── info_pannel.py - UI updates and detection triggers
└── traffic_lights.py - Visual traffic light display
```

---

## Summary

The application creates an intelligent traffic light system that:
1. **Processes multiple media types** (image, video, RTSP) efficiently
2. **Detects vehicles** using YOLOv8 at strategic moments
3. **Adjusts timing** based on detected congestion
4. **Manages state transitions** automatically through a state machine
5. **Updates UI** in real-time with current status

The system balances performance (not detecting every frame) with accuracy (detecting at state changes) to provide responsive, congestion-aware traffic light control.

