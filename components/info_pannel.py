import asyncio

from nicegui import ui

from core.controller import get_time_remaining, get_max_time, get_current_color, traffic_light_running, \
    traffic_light_state_machine, should_trigger_detection, count, update_vehicle_count, calculate_and_store_max_time, \
    clear_detection_flag, get_congestion
from core.model import count_cars_from_frame
from components.traffic_lights import yellow_blink_state, create_traffic_light


@ui.refreshable
def light_text():
    max_time = get_max_time()
    with ui.row().classes('justify-between items-center').style(
            'padding: 0.75rem; background-color: #f9fafb; border-radius: 0.5rem;'):
        current_color = get_current_color()
        ui.label(f'{current_color.capitalize()} Time:').classes('text-body2 text-weight-medium')
        ui.label(f'{max_time}s').classes('text-body2 text-weight-bold')


@ui.refreshable
def vehicle_detected_label(count: int = 0):
    with ui.row().classes('justify-between items-center').style(
            'padding: 0.75rem; background-color: #f9fafb; border-radius: 0.5rem;'):
        ui.label('Vehicles Detected:').classes('text-body2 text-weight-medium')
        ui.label(f"{count}").classes('text-h6 text-weight-bold')


def info_panel(current_frame):
    with ui.column().classes('q-mt-lg q-gutter-md').style('width: 100%;'):

        vehicle_detected_label(count["value"])

        congestion_row = ui.row().classes('justify-between items-center').style(
            'padding: 0.75rem; background-color: #f9fafb; border-radius: 0.5rem;')
        with congestion_row:
            ui.label('Congestion Level:').classes('text-body2 text-weight-medium')
            congestion_badge = ui.badge('Low', color='green')

        with ui.row().classes('justify-between items-center').style(
                'padding: 0.75rem; background-color: #f9fafb; border-radius: 0.5rem;'):
            ui.label('Time Remaining:').classes('text-body2 text-weight-medium')
            remaining_label = ui.label('0s').classes('text-h6 text-weight-bold').style('color: #2563eb;')

        light_text()

        # Track previous color to detect transitions
        previous_color = {'value': None}

        # Timer to update UI components
        def update_ui():
            # Start traffic light if not already running
            if not traffic_light_running['value']:
                asyncio.create_task(traffic_light_state_machine())
            current_color = get_current_color()

            # Trigger detection on color change for red and green
            if should_trigger_detection() and current_frame['value'] is not None:
                # Run detection only when color changes to red or green
                vehicle_count, _ = count_cars_from_frame(current_frame['value'])
                update_vehicle_count(vehicle_count)
                # Calculate and store max time based on detected count
                calculate_and_store_max_time()
                # Clear the detection flag
                clear_detection_flag()

            congestion = get_congestion(count['value'])

            # Reset blink state when transitioning to yellow (starts visible)
            if current_color == 'yellow' and previous_color['value'] != 'yellow':
                yellow_blink_state['value'] = True
            # Toggle blink state for yellow light while it's active
            elif current_color == 'yellow':
                yellow_blink_state['value'] = not yellow_blink_state['value']

            previous_color['value'] = current_color

            # Update traffic light
            create_traffic_light.refresh(current_color)

            # Update vehicle count
            vehicle_detected_label.refresh(count['value'])

            # Update congestion badge
            congestion_colors = {
                'low': 'green',
                'medium': 'yellow',
                'high': 'orange',
                'very_high': 'red'
            }
            congestion_text = congestion.replace('_', ' ').title()
            congestion_badge.text = congestion_text
            congestion_badge.props(f'color={congestion_colors.get(congestion, "green")}')

            # Update time remaining
            remaining = get_time_remaining()
            remaining_label.text = f'{remaining}s'

            # Update light text
            light_text.refresh()

        # Use faster update interval for blinking effect (250ms for smooth blinking)
        ui.timer(0.5, update_ui)  # Update every 250ms for smooth blinking
