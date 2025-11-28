"""
Traffic Light Dashboard - Modern UI Design
Recreates the design with video container on left and traffic light on right
"""

from nicegui import ui

from ME.controller import get_current_color


def create_traffic_light(state: str = 'red'):
    """Create a visual traffic light component with proper NiceGUI styling"""
    
    # Define colors for each state
    red_active = '#ef4444'
    red_inactive = '#4b5563'
    yellow_active = '#eab308'
    yellow_inactive = '#4b5563'
    green_active = '#22c55e'
    green_inactive = '#4b5563'
    
    # Traffic light container
    with ui.column().classes('items-center gap-4'):
        # Traffic light housing - dark background
        with ui.card().style('background-color: #1f2937; padding: 2rem; border-radius: 1rem;'):
            # Red light
            red_bg = red_active if state == 'red' else red_inactive
            red_opacity = '1' if state == 'red' else '0.3'
            red_shadow = '0 0 20px rgba(239, 68, 68, 0.8)' if state == 'red' else 'none'
            
            red_light = ui.element('div').style(
                f'width: 80px; height: 80px; border-radius: 50%; '
                f'background-color: {red_bg}; opacity: {red_opacity}; '
                f'box-shadow: {red_shadow}; margin-bottom: 1rem;'
            )
            
            # Yellow light
            yellow_bg = yellow_active if state == 'yellow' else yellow_inactive
            yellow_opacity = '1' if state == 'yellow' else '0.3'
            yellow_shadow = '0 0 20px rgba(234, 179, 8, 0.8)' if state == 'yellow' else 'none'
            
            yellow_light = ui.element('div').style(
                f'width: 80px; height: 80px; border-radius: 50%; '
                f'background-color: {yellow_bg}; opacity: {yellow_opacity}; '
                f'box-shadow: {yellow_shadow}; margin-bottom: 1rem;'
            )
            
            # Green light
            green_bg = green_active if state == 'green' else green_inactive
            green_opacity = '1' if state == 'green' else '0.3'
            green_shadow = '0 0 20px rgba(34, 197, 94, 0.8)' if state == 'green' else 'none'
            
            green_light = ui.element('div').style(
                f'width: 80px; height: 80px; border-radius: 50%; '
                f'background-color: {green_bg}; opacity: {green_opacity}; '
                f'box-shadow: {green_shadow};'
            )
        
        # State label
        ui.label(f'State: {state.upper()}').classes('text-h6 text-weight-bold')


@ui.page('/')
def main_page():
    """Main dashboard page"""
    
    # Set page background
    ui.query('body').style('background-color: #f5f5f5; margin: 0; padding: 0;')
    
    # Header bar
    with ui.header().style('background-color: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); width: 100%; height: 64px;'):

            with ui.row().style('position: relative;'):
                ui.label("Smart Traffic Flow Optimization Using Computer Vision").classes('text-h5 text-weight-bold text-primary')



    # Main content area
    with ui.row().style('width: 100%; height: calc(100vh - 64px); padding: 1.5rem; gap: 1.5rem;'):
        # Left side - Video container
        with ui.column().style('flex: 1; height: 100%;'):
            with ui.card().style('width: 100%; height: 100%; background-color: white; border-radius: 0.75rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; display: flex; flex-direction: column;'):
                # Video container
                with ui.column().classes('items-center justify-center').style('flex: 1; width: 100%; background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);'):
                    # Placeholder for video
                    with ui.column().classes('items-center q-gutter-md'):
                        ui.icon('videocam', size='4xl').style('color: #9ca3af; font-size: 4rem;')
                        ui.label('Video Feed').classes('text-h5 text-weight-medium')
                        ui.label('Traffic camera feed will be displayed here').classes('text-body2')
                    
                    # Video element (can be replaced with actual video source)
                    # Example: ui.video('path/to/video.mp4').style('width: 100%; height: 100%; object-fit: contain;')
                
                # Caption bar
                with ui.row().classes('items-center').style('width: 100%; padding: 1rem; background-color: white; border-top: 1px solid #e5e7eb;'):
                    ui.icon('info', size='sm').style('color: #6b7280; margin-right: 0.5rem;')
                    ui.label('Traffic details go here').classes('text-body2 text-weight-medium')
        
        # Right side - Traffic light
        with ui.column().classes('items-center justify-center').style('width: 400px; height: 100%;'):
            with ui.card().style('width: 100%; background-color: white; border-radius: 0.75rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 2rem;'):
                ui.label('Traffic Light Status').classes('text-h4 text-weight-bold q-mb-lg text-center')
                color = get_current_color()
                # Traffic light visualization
                create_traffic_light(color)
                
                # Status information panel
                with ui.column().classes('q-mt-lg q-gutter-md').style('width: 100%;'):
                    ui.separator()
                    
                    with ui.row().classes('justify-between items-center').style('padding: 0.75rem; background-color: #f9fafb; border-radius: 0.5rem;'):
                        ui.label('Vehicles Detected:').classes('text-body2 text-weight-medium')
                        ui.label('12').classes('text-h6 text-weight-bold')
                    
                    with ui.row().classes('justify-between items-center').style('padding: 0.75rem; background-color: #f9fafb; border-radius: 0.5rem;'):
                        ui.label('Congestion Level:').classes('text-body2 text-weight-medium')
                        ui.badge('Medium', color='yellow')
                    
                    with ui.row().classes('justify-between items-center').style('padding: 0.75rem; background-color: #f9fafb; border-radius: 0.5rem;'):
                        ui.label('Time Remaining:').classes('text-body2 text-weight-medium')
                        ui.label('15s').classes('text-h6 text-weight-bold').style('color: #2563eb;')
                    
                    with ui.row().classes('justify-between items-center').style('padding: 0.75rem; background-color: #f9fafb; border-radius: 0.5rem;'):
                        ui.label('Green Time:').classes('text-body2 text-weight-medium')
                        ui.label('30s').classes('text-body2 text-weight-bold')


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(port=8183, title='Traffic Light Dashboard')

