# Traffic Light Dashboard - Code Flow Documentation

This document explains the code execution flow, function call sequences, data flow, and component interactions in the Traffic Light Dashboard application.

## Table of Contents
1. [Application Startup Flow](#application-startup-flow)
2. [UI Component Initialization](#ui-component-initialization)
3. [Media Loading Flow](#media-loading-flow)
4. [Frame Processing Flow](#frame-processing-flow)
5. [Detection Trigger Flow](#detection-trigger-flow)
6. [State Machine Execution Flow](#state-machine-execution-flow)
7. [UI Update Flow](#ui-update-flow)
8. [Data Flow and State Management](#data-flow-and-state-management)
9. [Async Task Management](#async-task-management)
10. [Event Handling Flow](#event-handling-flow)

---

## Application Startup Flow

### Entry Point
**File:** `traffic_light_dashboard.py` (line 390-391)

```python
if __name__ in {'__main__', '__mp_main__'}:
    ui.run(port=8188, title='Traffic Light Dashboard')
```

### Startup Sequence

1. **NiceGUI Server Initialization**
   - `ui.run()` starts the FastAPI/Quasar web server
   - Server listens on port 8188
   - WebSocket connections are established for real-time updates

2. **Route Registration**
   - `@ui.page('/')` decorator registers `main_page()` as the root route handler
   - `@app.get('/video')` registers the video serving endpoint

3. **Global State Initialization**
   ```python
   media_capture = {'value': None}      # Stores cv2.VideoCapture object
   is_streaming = {'value': False}      # Streaming status flag
   current_frame = {'value': None}      # Current frame for detection
   ```

4. **Page Load Handler**
   - When user navigates to `/`, `main_page()` is called
   - This function sets up the entire UI structure

---

## UI Component Initialization

### Main Page Structure
**File:** `traffic_light_dashboard.py` (line 379-387)

**Call Sequence:**
```
main_page()
├── ui.query('body').style(...)           # Set page background
├── header()                              # Render header component
└── ui.row()
    ├── scene_section()                   # Left section: media display
    └── traffic_section()                # Right section: traffic light
```

### Header Component
**File:** `components/header.py`

**Function:** `header()`
- Creates a header bar with title
- No interactive elements
- Renders once on page load

### Scene Section
**File:** `traffic_light_dashboard.py` (line 215-343)

**Function:** `scene_section()`

**Initialization Flow:**
```
scene_section()
├── ui.column() (container)
│   ├── ui.card() (main card)
│   │   ├── ui_refs = {}                  # Dictionary to store UI element references
│   │   │
│   │   ├── ui.row() (top bar)
│   │   │   ├── open_popup_button = ui.button(...)
│   │   │   │   └── .on('click', toggle_popup)  # Event handler registration
│   │   │   │
│   │   │   └── popup_card = ui.card(...)
│   │   │       ├── source_type_select = ui.select(...)
│   │   │       ├── source_path_input = ui.input(...)
│   │   │       └── load_button = ui.button(...)
│   │   │           └── .on('click', load_media)  # Event handler registration
│   │   │
│   │   ├── ui.column() (media container)
│   │   │   ├── media_video = ui.video(...)
│   │   │   │   └── .on("ended", lambda: ui.notify(...))
│   │   │   ├── media_image = ui.interactive_image(...)
│   │   │   ├── media_static_image = ui.image(...)
│   │   │   └── placeholder = ui.column(...)
│   │   │
│   │   └── ui.row() (caption bar)
│   │       └── caption_label = ui.label(...)
│   │
│   └── load_media() (async function defined, not called yet)
```

**Key Points:**
- All UI elements are stored in `ui_refs` dictionary for later access
- Event handlers are registered during initialization
- `load_media()` is defined but not executed until button click

### Traffic Section
**File:** `traffic_light_dashboard.py` (line 345-357)

**Function:** `traffic_section()`

**Initialization Flow:**
```
traffic_section()
├── ui.column() (container)
│   └── ui.card()
│       ├── ui.label('Traffic Light Status')
│       ├── get_current_color()                    # Call to controller
│       ├── create_traffic_light(color)            # Render traffic light
│       ├── ui.separator()
│       └── info_panel(current_frame)              # Info panel with timer
```

**Key Points:**
- Calls `get_current_color()` from controller to get initial state
- Passes `current_frame` dictionary reference to `info_panel`
- `info_panel` sets up a timer that runs continuously

---

## Media Loading Flow

### User Interaction Flow

**Trigger:** User clicks "Load" button in popup

**Call Sequence:**
```
User clicks "Load" button
└── load_button.on('click') event fires
    └── load_media() (async function)
```

### load_media() Function
**File:** `traffic_light_dashboard.py` (line 302-339)

**Execution Flow:**
```python
async def load_media():
    # 1. Get UI element references
    source_type_select = ui_refs['source_type_select']
    source_path_input = ui_refs['source_path_input']
    media_image = ui_refs['media_image']
    # ... get other references
    
    # 2. Extract user input
    source_type = source_type_select.value
    source_path = source_path_input.value.strip()
    
    # 3. Validation
    if not source_path:
        ui.notify('Please enter a source path', type='warning')
        return
    
    # 4. Cleanup previous media
    is_streaming['value'] = False
    await asyncio.sleep(0.1)  # Wait for loops to exit
    
    if media_capture['value'] is not None:
        if isinstance(media_capture['value'], cv2.VideoCapture):
            media_capture['value'].release()
        media_capture['value'] = None
    
    current_frame['value'] = None
    
    # 5. Hide all media elements
    media_image.style('display: none;')
    media_static_image.style('display: none;')
    media_video.style('display: none;')
    placeholder.style('display: none;')
    popup_card.style('display: none;')
    
    # 6. Load new media
    await stream_media(media_image, media_static_image, media_video, source_type, source_path)
    
    # 7. Notify user
    ui.notify(f'Loaded {source_type}: {source_path}', type='positive')
```

### stream_media() Function
**File:** `traffic_light_dashboard.py` (line 68-209)

**Function Signature:**
```python
async def stream_media(media_image, media_static_image, media_video, source_type: str, source_path: str)
```

**Execution Flow (Image):**
```
stream_media(source_type='image', ...)
├── Cleanup previous capture (if exists)
├── cv2.imread(source_path)                    # Read image file
├── current_frame['value'] = frame              # Store frame globally
├── count_cars_from_frame(frame)               # Run detection immediately
│   └── Returns: (vehicle_count, annotated_frame)
├── update_vehicle_count(vehicle_count)        # Update global count
├── calculate_and_store_max_time()             # Calculate timing
├── frame_to_base64(annotated_frame)           # Convert to base64
├── media_static_image.source = 'data:image/...'  # Set image source
├── media_static_image.style('display: block;')    # Show image
└── ui.notify('Image loaded successfully')
```

**Execution Flow (Video):**
```
stream_media(source_type='video', ...)
├── Validate video file exists
├── Encode path: urllib.parse.quote(source_path)
├── Create video URL: f'/video?file_path={encoded_path}'
├── media_video.source = video_url              # Set video source
├── media_video.style('display: block;')         # Show video element
├── cv2.VideoCapture(str(video_path))          # Open video file
├── media_capture['value'] = cap                # Store capture object
├── is_streaming['value'] = True                # Set streaming flag
├── start_traffic_light() (if not running)      # Start state machine
└── asyncio.create_task(process_video_frames()) # Start background task
```

**Execution Flow (RTSP):**
```
stream_media(source_type='rtsp', ...)
├── open_media_source('rtsp', source_path)      # Open RTSP stream
│   └── cv2.VideoCapture(source_path, cv2.CAP_FFMPEG)
│       └── cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce latency
├── media_capture['value'] = cap
├── is_streaming['value'] = True
├── media_image.style('display: block;')        # Show interactive image
├── start_traffic_light() (if not running)
└── asyncio.create_task(process_rtsp_frames())  # Start background task
```

---

## Frame Processing Flow

### Video Frame Processing
**File:** `traffic_light_dashboard.py` (line 135-153)

**Function:** `process_video_frames()` (nested async function)

**Execution Flow:**
```python
async def process_video_frames():
    try:
        while is_streaming['value']:              # Loop while streaming
            ret, frame = cap.read()               # Read frame from video
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop to beginning
                continue
            
            current_frame['value'] = frame        # Store frame globally
            
            await asyncio.sleep(0.1)              # Wait 100ms
    except Exception as e:
        print(f"Error processing video frames: {e}")
    finally:
        if isinstance(cap, cv2.VideoCapture):
            cap.release()                         # Cleanup
```

**Key Points:**
- Runs in background async task
- Continuously updates `current_frame['value']`
- Does NOT run detection (only stores frames)
- Detection triggered separately by state machine

### RTSP Frame Processing
**File:** `traffic_light_dashboard.py` (line 182-208)

**Function:** `process_rtsp_frames()` (nested async function)

**Execution Flow:**
```python
async def process_rtsp_frames():
    try:
        while is_streaming['value']:
            ret, frame = cap.read()               # Read frame from RTSP
            if not ret:
                await asyncio.sleep(1)            # Wait before retry
                continue                          # Try to reconnect
            
            current_frame['value'] = frame        # Store for detection
            
            img_base64 = frame_to_base64(frame)   # Convert to base64
            media_image.source = f'data:image/...'  # Update UI
            
            await asyncio.sleep(0.033)            # ~30 FPS
    except Exception as e:
        ui.notify(f'Error streaming RTSP: {e}', type='negative')
    finally:
        if isinstance(cap, cv2.VideoCapture):
            cap.release()
        is_streaming['value'] = False
        media_capture['value'] = None
```

**Key Points:**
- Updates UI in real-time (every 33ms)
- Handles connection loss gracefully
- Both stores frame AND updates display

### frame_to_base64() Function
**File:** `traffic_light_dashboard.py` (line 29-34)

**Function:**
```python
def frame_to_base64(frame: np.ndarray) -> str:
    if frame is None:
        return ''
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buffer).decode('utf-8')
```

**Flow:**
1. Check if frame is None → return empty string
2. Encode frame as JPEG (85% quality)
3. Encode buffer as base64
4. Return as UTF-8 string

---

## Detection Trigger Flow

### Detection Trigger Mechanism

**Location:** `components/info_pannel.py` (line 52-66)

**Function:** `update_ui()` (called by timer)

**Trigger Flow:**
```
UI Timer (every 500ms)
└── update_ui()
    ├── Check: should_trigger_detection()
    │   └── Returns: detection_needed['value']
    │
    └── If True AND current_frame['value'] is not None:
        ├── count_cars_from_frame(current_frame['value'])
        │   └── model.py: count_cars_from_frame()
        │       ├── model(frame, verbose=False)        # YOLO inference
        │       ├── sv.Detections.from_ultralytics()   # Convert detections
        │       ├── Filter: class_id in [2, 5, 7]      # Vehicles only
        │       ├── box_annotator.annotate()           # Draw boxes
        │       ├── label_annotator.annotate()         # Draw labels
        │       └── Return: (car_count, annotated_frame)
        │
        ├── update_vehicle_count(vehicle_count)
        │   └── controller.py: count['value'] = vehicle_count
        │
        ├── calculate_and_store_max_time()
        │   └── controller.py: calculate_and_store_max_time()
        │       ├── get_congestion(count['value'])
        │       ├── Calculate max_time based on congestion
        │       └── stored_max_time['value'] = max_time
        │
        └── clear_detection_flag()
            └── controller.py: detection_needed['value'] = False
```

### When Detection Flag is Set

**Location:** `controller.py` (line 75-91)

**State Transition Functions:**
```python
def set_color_red():
    active_color['value'] = "red"
    state_start_time['value'] = time.time()
    stored_max_time['value'] = None
    detection_needed['value'] = True      # ← Flag set here

def set_color_green():
    active_color['value'] = "green"
    state_start_time['value'] = time.time()
    stored_max_time['value'] = None
    detection_needed['value'] = True      # ← Flag set here

def set_color_yellow():
    active_color['value'] = "yellow"
    state_start_time['value'] = time.time()
    stored_max_time['value'] = None
    detection_needed['value'] = False    # ← No detection for yellow
```

**Call Chain:**
```
traffic_light_state_machine()
└── When timer expires:
    ├── set_color_red() / set_color_green() / set_color_yellow()
    └── detection_needed['value'] = True (for red/green)
        └── Next update_ui() call will trigger detection
```

---

## State Machine Execution Flow

### State Machine Initialization
**File:** `controller.py` (line 120-130)

**Function:** `start_traffic_light()`

**Flow:**
```python
def start_traffic_light():
    if not traffic_light_running['value']:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(traffic_light_state_machine())
        except RuntimeError:
            asyncio.create_task(traffic_light_state_machine())
```

**Called From:**
- `stream_media()` when video/RTSP is loaded (line 132, 179)
- `update_ui()` if not already running (line 54-55)

### State Machine Loop
**File:** `controller.py` (line 100-118)

**Function:** `traffic_light_state_machine()`

**Execution Flow:**
```python
async def traffic_light_state_machine():
    traffic_light_running['value'] = True
    
    while traffic_light_running['value']:
        # 1. Get current state
        current_state = active_color['value']
        
        # 2. Get max time for current state
        max_time = get_max_time()
        #   └── get_max_time()
        #       ├── If stored_max_time['value'] is not None:
        #       │   └── Return stored_max_time['value']
        #       └── Else:
        #           ├── get_congestion(count['value'])
        #           ├── Calculate max_time
        #           └── stored_max_time['value'] = max_time
        #           └── Return max_time
        
        # 3. Calculate elapsed time
        elapsed = time.time() - state_start_time['value']
        
        # 4. Check if transition needed
        if elapsed >= max_time:
            if current_state == "red":
                set_color_green()
            elif current_state == "green":
                set_color_yellow()
            elif current_state == "yellow":
                set_color_red()
        
        # 5. Wait before next check
        await asyncio.sleep(0.1)  # 100ms interval
```

**State Transition Sequence:**
```
Initial: Red (10s base)
├── Timer counts down
├── When elapsed >= max_time:
│   └── set_color_green()
│       ├── active_color['value'] = "green"
│       ├── state_start_time['value'] = time.time()
│       ├── stored_max_time['value'] = None
│       └── detection_needed['value'] = True
│
└── Green (5s base + congestion adjustment)
    ├── Timer counts down
    ├── When elapsed >= max_time:
    │   └── set_color_yellow()
    │       ├── active_color['value'] = "yellow"
    │       ├── state_start_time['value'] = time.time()
    │       ├── stored_max_time['value'] = None
    │       └── detection_needed['value'] = False
    │
    └── Yellow (3s fixed)
        ├── Timer counts down
        ├── When elapsed >= max_time:
        │   └── set_color_red()
        │       ├── active_color['value'] = "red"
        │       ├── state_start_time['value'] = time.time()
        │       ├── stored_max_time['value'] = None
        │       └── detection_needed['value'] = True
        │
        └── Loop back to Red
```

---

## UI Update Flow

### Info Panel Timer
**File:** `components/info_pannel.py` (line 104)

**Setup:**
```python
ui.timer(0.5, update_ui)  # Update every 500ms
```

### update_ui() Function
**File:** `components/info_pannel.py` (line 52-102)

**Complete Execution Flow:**
```python
def update_ui():
    # 1. Ensure state machine is running
    if not traffic_light_running['value']:
        asyncio.create_task(traffic_light_state_machine())
    
    # 2. Get current color
    current_color = get_current_color()
    
    # 3. Trigger detection if needed
    if should_trigger_detection() and current_frame['value'] is not None:
        vehicle_count, _ = count_cars_from_frame(current_frame['value'])
        update_vehicle_count(vehicle_count)
        calculate_and_store_max_time()
        clear_detection_flag()
    
    # 4. Get congestion level
    congestion = get_congestion(count['value'])
    
    # 5. Handle yellow light blinking
    if current_color == 'yellow' and previous_color['value'] != 'yellow':
        yellow_blink_state['value'] = True  # Start visible
    elif current_color == 'yellow':
        yellow_blink_state['value'] = not yellow_blink_state['value']  # Toggle
    
    previous_color['value'] = current_color
    
    # 6. Update UI components
    create_traffic_light.refresh(current_color)
    vehicle_detected_label.refresh(count['value'])
    
    # 7. Update congestion badge
    congestion_badge.text = congestion.replace('_', ' ').title()
    congestion_badge.props(f'color={congestion_colors.get(congestion, "green")}')
    
    # 8. Update time remaining
    remaining = get_time_remaining()
    remaining_label.text = f'{remaining}s'
    
    # 9. Update light text
    light_text.refresh()
```

**UI Refresh Functions:**
- `create_traffic_light.refresh()` - Re-renders traffic light component
- `vehicle_detected_label.refresh()` - Updates vehicle count display
- `light_text.refresh()` - Updates max time display

**Direct Updates:**
- `congestion_badge.text` - Updates congestion text
- `congestion_badge.props()` - Updates badge color
- `remaining_label.text` - Updates countdown timer

---

## Data Flow and State Management

### Global State Variables

**Location:** `traffic_light_dashboard.py` (line 25-27)
```python
media_capture = {'value': None}      # cv2.VideoCapture object or None
is_streaming = {'value': False}      # Boolean flag for streaming status
current_frame = {'value': None}      # numpy.ndarray frame or None
```

**Location:** `controller.py` (line 19-24)
```python
active_color = {'value': "red"}                    # Current traffic light color
state_start_time = {'value': time.time()}         # When current state started
count = {'value': 0}                               # Vehicle count
traffic_light_running = {'value': False}          # State machine running flag
stored_max_time = {'value': None}                 # Cached max time for current state
detection_needed = {'value': False}               # Flag to trigger detection
```

**Location:** `components/traffic_lights.py` (line 10)
```python
yellow_blink_state = {'value': False}             # Yellow light visibility state
```

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Media Source (Image/Video/RTSP)          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Frame Processing (Background Task)              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  process_video_frames() / process_rtsp_frames()     │  │
│  │  - Reads frames from source                          │  │
│  │  - Updates: current_frame['value'] = frame          │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              State Machine (Background Task)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  traffic_light_state_machine()                        │  │
│  │  - Checks elapsed time                               │  │
│  │  - Transitions states                                │  │
│  │  - Sets: detection_needed['value'] = True             │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              UI Update Timer (Every 500ms)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  update_ui()                                         │  │
│  │  - Checks: should_trigger_detection()               │  │
│  │  - If True: Runs detection on current_frame         │  │
│  │  - Updates: count['value'] = vehicle_count           │  │
│  │  - Calculates: stored_max_time['value']              │  │
│  │  - Updates all UI components                         │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    UI Components                             │
│  - Traffic Light Display                                    │
│  - Vehicle Count Display                                    │
│  - Congestion Badge                                         │
│  - Time Remaining Display                                   │
└─────────────────────────────────────────────────────────────┘
```

### State Synchronization

**State Machine → Detection:**
```
traffic_light_state_machine()
└── set_color_red() / set_color_green()
    └── detection_needed['value'] = True
        └── update_ui() checks flag
            └── Runs detection if flag is True
```

**Detection → Timing:**
```
count_cars_from_frame()
└── Returns: vehicle_count
    └── update_vehicle_count(vehicle_count)
        └── count['value'] = vehicle_count
            └── calculate_and_store_max_time()
                └── get_congestion(count['value'])
                    └── stored_max_time['value'] = calculated_time
                        └── get_max_time() uses stored value
```

**Timing → State Machine:**
```
traffic_light_state_machine()
└── get_max_time()
    └── Returns stored_max_time['value']
        └── Used to determine when to transition
```

---

## Async Task Management

### Concurrent Tasks

The application runs multiple async tasks simultaneously:

1. **State Machine Task**
   - Function: `traffic_light_state_machine()`
   - Interval: 100ms
   - Purpose: Manage traffic light state transitions

2. **Frame Processing Tasks**
   - Function: `process_video_frames()` or `process_rtsp_frames()`
   - Interval: 100ms (video) or 33ms (RTSP)
   - Purpose: Read and store frames from media source

3. **UI Update Timer**
   - Function: `update_ui()`
   - Interval: 500ms
   - Purpose: Update UI components and trigger detection

4. **NiceGUI WebSocket**
   - Handled by NiceGUI framework
   - Purpose: Real-time UI updates to browser

### Task Creation

**Video/RTSP Loading:**
```python
# In stream_media()
asyncio.create_task(process_video_frames())  # or process_rtsp_frames()
```

**State Machine:**
```python
# In start_traffic_light()
loop = asyncio.get_running_loop()
loop.create_task(traffic_light_state_machine())
```

**UI Timer:**
```python
# In info_panel()
ui.timer(0.5, update_ui)  # NiceGUI manages this
```

### Task Coordination

**Shared State:**
- All tasks access global dictionaries: `{'value': ...}`
- No explicit locking needed (Python GIL handles single-threaded execution)
- Async tasks yield control with `await asyncio.sleep()`

**Cleanup:**
```python
# When stopping streaming
is_streaming['value'] = False  # Signals tasks to exit
await asyncio.sleep(0.1)      # Wait for loops to exit
media_capture['value'].release()  # Release resources
```

---

## Event Handling Flow

### User Events

**1. Configure Media Source Button Click**
```
User clicks "Configure Media Source"
└── open_popup_button.on('click')
    └── toggle_popup()
        └── popup_card.style('display: block/none;')
```

**2. Load Button Click**
```
User clicks "Load" button
└── load_button.on('click')
    └── load_media() (async)
        ├── Validates input
        ├── Cleans up previous media
        └── await stream_media(...)
            └── Starts appropriate processing task
```

**3. Video End Event**
```
Video playback ends
└── media_video.on("ended")
    └── ui.notify("Video ended")
```

### System Events

**1. State Transition**
```
State timer expires
└── traffic_light_state_machine()
    └── set_color_*()
        ├── Updates active_color['value']
        ├── Resets state_start_time['value']
        └── Sets detection_needed['value']
            └── Next update_ui() triggers detection
```

**2. Detection Trigger**
```
UI timer fires (every 500ms)
└── update_ui()
    └── Checks should_trigger_detection()
        └── If True: Runs detection
            └── Updates count['value']
                └── Recalculates timing
```

### HTTP Endpoints

**Video Serving Endpoint**
**File:** `traffic_light_dashboard.py` (line 361-376)

```python
@app.get('/video')
async def serve_video(file_path: str):
    video_path = Path(file_path)
    if video_path.exists() and video_path.is_file():
        return FileResponse(
            str(video_path),
            media_type='video/mp4',
            headers={'Accept-Ranges': 'bytes'}
        )
    else:
        return Response(status_code=404)
```

**Request Flow:**
```
Browser requests video
└── GET /video?file_path=/path/to/video.mp4
    └── serve_video(file_path)
        ├── Validates file exists
        └── Returns FileResponse
            └── Browser streams video
```

---

## Function Call Hierarchy

### Complete Call Tree

```
Application Start
└── ui.run()
    └── NiceGUI Server Starts
        └── @ui.page('/')
            └── main_page()
                ├── header()
                ├── scene_section()
                │   ├── UI elements created
                │   └── load_media() [defined, not called]
                │       └── stream_media() [called on button click]
                │           ├── open_media_source()
                │           ├── count_cars_from_frame() [for images]
                │           ├── update_vehicle_count()
                │           ├── calculate_and_store_max_time()
                │           ├── start_traffic_light()
                │           └── asyncio.create_task(process_*_frames())
                │
                └── traffic_section()
                    ├── get_current_color()
                    ├── create_traffic_light()
                    └── info_panel(current_frame)
                        └── ui.timer(0.5, update_ui)
                            └── update_ui() [called every 500ms]
                                ├── start_traffic_light() [if needed]
                                ├── get_current_color()
                                ├── should_trigger_detection()
                                ├── count_cars_from_frame() [if needed]
                                ├── update_vehicle_count()
                                ├── calculate_and_store_max_time()
                                ├── clear_detection_flag()
                                ├── get_congestion()
                                ├── get_time_remaining()
                                ├── get_max_time()
                                └── UI refresh calls

Background Tasks (Running concurrently)
├── traffic_light_state_machine()
│   ├── get_max_time()
│   │   ├── get_congestion()
│   │   └── calculate_and_store_max_time()
│   ├── set_color_red() / set_color_green() / set_color_yellow()
│   └── [loops every 100ms]
│
└── process_video_frames() / process_rtsp_frames()
    ├── cap.read()
    ├── current_frame['value'] = frame
    └── [loops every 100ms or 33ms]
```

---

## Key Code Patterns

### 1. Dictionary-Based State
```python
# Pattern: Using dictionaries with 'value' key for mutable state
state = {'value': initial_value}

# Access
current = state['value']

# Update
state['value'] = new_value
```

**Why:** Allows passing references that can be modified across function boundaries.

### 2. Async Task Creation
```python
# Pattern: Create background tasks
asyncio.create_task(async_function())

# Pattern: Get running loop
loop = asyncio.get_running_loop()
loop.create_task(async_function())
```

**Why:** Allows concurrent execution of multiple async operations.

### 3. UI Element References
```python
# Pattern: Store UI elements in dictionary
ui_refs = {}
ui_refs['element'] = ui.button(...)

# Later access
element = ui_refs['element']
element.on('click', handler)
```

**Why:** Allows event handlers defined later to access UI elements created earlier.

### 4. Refreshable UI Components
```python
# Pattern: Use @ui.refreshable decorator
@ui.refreshable
def component():
    # UI code

# Refresh
component.refresh()
```

**Why:** Efficiently updates specific UI components without full page refresh.

### 5. Flag-Based Detection Trigger
```python
# Pattern: Set flag, check later
detection_needed['value'] = True

# Later
if should_trigger_detection():
    run_detection()
    clear_detection_flag()
```

**Why:** Decouples state transitions from detection execution, allowing flexible timing.

---

## Summary

The application follows an **event-driven, async architecture** with:

1. **Multiple concurrent async tasks** for state management and frame processing
2. **Timer-based UI updates** for responsive user interface
3. **Flag-based coordination** between state machine and detection system
4. **Dictionary-based state management** for shared mutable state
5. **Component-based UI** with refreshable elements

The code flow is designed for:
- **Efficiency:** Detection runs only when needed
- **Responsiveness:** UI updates frequently (500ms)
- **Reliability:** Graceful error handling and cleanup
- **Maintainability:** Clear separation of concerns

