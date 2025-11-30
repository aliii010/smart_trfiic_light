import time
import asyncio


congestion_multipliers = {
    'low': 0,
    'medium': 0.2,
    'high': 0.5,
    'very_high': 0.8
}

lights = {
    "red": 10,
    "yellow": 3,
    "green": 5,
}

active_color = {'value': "red"}
state_start_time = {'value': time.time()}
count = {'value': 0}
traffic_light_running = {'value': False}
stored_max_time = {'value': None}
detection_needed = {'value': False}

def set_active_color(color: str):
    active_color['value'] = color
    state_start_time['value'] = time.time()

def get_congestion(counter):
    if counter > 15:
        return 'very_high'
    elif counter > 10:
        return 'high'
    elif counter > 5:
        return 'medium'
    else:
        return 'low'

def update_vehicle_count(vehicle_count: int):
    count['value'] = vehicle_count

def get_max_time():
    if stored_max_time['value'] is not None:
        return stored_max_time['value']

    return calculate_and_store_max_time()

def calculate_and_store_max_time():
    state = active_color['value']
    congestion = get_congestion(count['value'])
    multiplier = congestion_multipliers.get(congestion, 0)
    base_time = lights.get(state, 5)
    i = int(base_time * multiplier)
    max_time = base_time - i if state == "red" else i + base_time
    stored_max_time['value'] = max_time
    return max_time

def get_current_color():
    return active_color['value']

def set_color_red():
    active_color['value'] = "red"
    state_start_time['value'] = time.time()
    stored_max_time['value'] = None
    detection_needed['value'] = True

def set_color_yellow():
    active_color['value'] = "yellow"
    state_start_time['value'] = time.time()
    stored_max_time['value'] = None
    detection_needed['value'] = False

def set_color_green():
    active_color['value'] = "green"
    state_start_time['value'] = time.time()
    stored_max_time['value'] = None
    detection_needed['value'] = True

def get_time_remaining():
    elapsed = time.time() - state_start_time['value']
    max_time = get_max_time()
    remaining = max(0, max_time - elapsed)
    return int(remaining)

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
        
        await asyncio.sleep(0.1)

def start_traffic_light():
    if not traffic_light_running['value']:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(traffic_light_state_machine())
        except RuntimeError:
            asyncio.create_task(traffic_light_state_machine())

def stop_traffic_light():
    traffic_light_running['value'] = False

def should_trigger_detection():
    return detection_needed['value']

def clear_detection_flag():
    detection_needed['value'] = False