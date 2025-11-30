from nicegui import ui

def light_component(bg: str, opacity: float, shadow: str, with_margin: bool = True):
    ui.button().style(
        f'width: 80px; height: 80px; border-radius: 50%; '
        f'background-color: {bg} !important; opacity: {opacity}; '
        f'box-shadow: {shadow}; {"margin-bottom: 1rem" if with_margin else ""};')


yellow_blink_state = {'value': False}

@ui.refreshable
def create_traffic_light(state: str = 'red'):
    red_active = '#ef4444'
    red_inactive = '#4b5563'
    yellow_active = '#eab308'
    yellow_inactive = '#4b5563'
    green_active = '#22c55e'
    green_inactive = '#4b5563'

    # Traffic light container
    with ui.column().classes('items-center gap-4'):
        with ui.card().style('background-color: #1f2937; padding: 2rem; border-radius: 1rem;'):

            red_bg = red_active if state == 'red' else red_inactive
            red_opacity = 1 if state == 'red' else 0.3
            red_shadow = '0 0 20px rgba(239, 68, 68, 0.8)' if state == 'red' else 'none'

            light_component(
                bg=red_bg,
                opacity=red_opacity,
                shadow=red_shadow,
            )

            yellow_bg = yellow_active if state == 'yellow' else yellow_inactive
            if state == 'yellow':
                yellow_opacity = 1.0 if yellow_blink_state['value'] else 0.3
                yellow_shadow = '0 0 20px rgba(234, 179, 8, 0.8)' if yellow_blink_state['value'] else 'none'
            else:
                yellow_opacity = 0.3
                yellow_shadow = 'none'

            light_component(
                bg=yellow_bg,
                opacity=yellow_opacity,
                shadow=yellow_shadow,
            )

            green_bg = green_active if state == 'green' else green_inactive
            green_opacity = 1 if state == 'green' else 0.3
            green_shadow = '0 0 20px rgba(34, 197, 94, 0.8)' if state == 'green' else 'none'

            light_component(
                bg=green_bg,
                opacity=green_opacity,
                shadow=green_shadow,
                with_margin=False
            )
