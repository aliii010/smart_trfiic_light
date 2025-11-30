from nicegui import ui, app
import cv2
import asyncio
from pathlib import Path
import urllib.parse
from fastapi import Response
from fastapi.responses import FileResponse

from prometheus_client.decorator import contextmanager

from components.header import header
from components.info_pannel import info_panel
from components.traffic_lights import create_traffic_light
from core.controller import (
    get_current_color, update_vehicle_count,
    start_traffic_light, traffic_light_running, calculate_and_store_max_time
)
from core.model import count_cars_from_frame
from utils.streaming_utils import frame_to_base64, open_media_source

media_capture = {'value': None}
is_streaming = {'value': False}
current_frame = {'value': None}






async def stream_media(media_image, media_static_image, media_video, source_type: str, source_path: str):
    global media_capture, is_streaming, current_frame

    if media_capture['value'] is not None and isinstance(media_capture['value'], cv2.VideoCapture):
        is_streaming['value'] = False
        await asyncio.sleep(0.1)  # Give time for loop to exit
        media_capture['value'].release()
        media_capture['value'] = None

    is_streaming['value'] = False

    if source_type == 'image':
        try:
            frame = cv2.imread(source_path)
            if frame is not None:
                current_frame['value'] = frame
                vehicle_count, annotated_frame = count_cars_from_frame(frame)
                update_vehicle_count(vehicle_count)
                # Calculate and store max time based on detected count
                calculate_and_store_max_time()
                # Use annotated frame for display (static image, not streaming)
                if annotated_frame is not None:
                    img_base64 = frame_to_base64(annotated_frame)
                    media_static_image.source = f'data:image/jpeg;base64,{img_base64}'
                else:
                    img_base64 = frame_to_base64(frame)
                    media_static_image.source = f'data:image/jpeg;base64,{img_base64}'
                media_static_image.style('display: block;')
                media_image.style('display: none;')
                media_video.style('display: none;')
                ui.notify('Image loaded successfully', type='positive')
            else:
                ui.notify('Failed to load image. Please check the file path.', type='negative')
        except Exception as e:
            ui.notify(f'Error loading image: {e}', type='negative')
            print(f"Error loading image: {e}")
        return

    if source_type == 'video':
        try:
            video_path = Path(source_path)
            if not video_path.exists():
                ui.notify('Video file not found. Please check the path.', type='negative')
                return

            # Convert absolute path to URL path (serve through HTTP)
            # Use the video route we created
            encoded_path = urllib.parse.quote(source_path, safe='')
            video_url = f'/video?file_path={encoded_path}'

            media_video.source = video_url
            media_video.style('display: block;')
            media_image.style('display: none;')
            media_static_image.style('display: none;')

            # Start background processing for vehicle detection on video
            # We'll process frames in the background for vehicle counting
            cap = cv2.VideoCapture(str(video_path))
            if cap.isOpened():
                media_capture['value'] = cap
                is_streaming['value'] = True

                # Start traffic light state machine if not already running
                if not traffic_light_running['value']:
                    start_traffic_light()

                # Background frame processing - just store frames for detection on color change
                async def process_video_frames():
                    try:
                        while is_streaming['value']:
                            ret, frame = cap.read()
                            if not ret:
                                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                                continue

                            # Store current frame for detection (will be used when color changes)
                            current_frame['value'] = frame

                            await asyncio.sleep(0.1)  # Process every 100ms
                    except Exception as e:
                        print(f"Error processing video frames: {e}")
                    finally:
                        if isinstance(cap, cv2.VideoCapture):
                            cap.release()

                asyncio.create_task(process_video_frames())
                ui.notify('Video loaded successfully', type='positive')
            else:
                ui.notify('Failed to open video file.', type='negative')
        except Exception as e:
            ui.notify(f'Error loading video: {e}', type='negative')
            print(f"Error loading video: {e}")
        return

    # Handle RTSP stream (use interactive_image for efficient frame updates)
    cap = open_media_source(source_type, source_path)
    if cap is None:
        media_image.source = ''
        ui.notify(f'Failed to open {source_type} source. Please check the path/URL.', type='negative')
        return

    media_capture['value'] = cap
    is_streaming['value'] = True

    # Show interactive_image element, hide video and static image elements for RTSP
    media_image.style('display: block;')
    media_static_image.style('display: none;')
    media_video.style('display: none;')

    # Start traffic light state machine if not already running
    if not traffic_light_running['value']:
        start_traffic_light()

    # Background frame processing - ui.interactive_image handles updates efficiently
    async def process_rtsp_frames():
        try:
            while is_streaming['value']:
                ret, frame = cap.read()
                if not ret:
                    # RTSP connection lost, try to reconnect
                    await asyncio.sleep(1)
                    continue

                # Store current frame for detection (will be used when color changes)
                current_frame['value'] = frame

                # Update interactive_image - it automatically adapts frame rate to bandwidth
                img_base64 = frame_to_base64(frame)
                media_image.source = f'data:image/jpeg;base64,{img_base64}'

                await asyncio.sleep(0.033)  # ~30 FPS
        except Exception as e:
            ui.notify(f'Error streaming RTSP: {e}', type='negative')
            print(f"Error streaming RTSP: {e}")
        finally:
            if isinstance(cap, cv2.VideoCapture):
                cap.release()
            is_streaming['value'] = False
            media_capture['value'] = None

    asyncio.create_task(process_rtsp_frames())
    ui.notify('RTSP stream started successfully', type='positive')


@contextmanager
def loading_button(button: ui.button):
    button.set_visibility(False)
    spinner = ui.spinner(size="lg")
    try:
        yield
    finally:
        spinner.delete()
        button.set_visibility(True)


def scene_section():
    with ui.column().style('flex: 1; height: 100%;'):
        with ui.card().style(
                'width: 100%; height: 100%; background-color: white; border-radius: 0.75rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; display: flex; flex-direction: column;'):
            ui_refs = {}

            with ui.row().classes('justify-end').style(
                    'width: 100%; padding: 1rem; background-color: #f9fafb; border-bottom: 1px solid #e5e7eb; position: relative;'):
                open_popup_button = ui.button('Configure Media Source', icon='settings', color='primary')
                ui_refs['open_popup_button'] = open_popup_button

                popup_card = ui.card().style(
                    'position: absolute; top: 100%; right: 0; margin-top: 0.5rem; '
                    'min-width: 300px; padding: 1rem; z-index: 1000; '
                    'box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: none;'
                )
                ui_refs['popup_card'] = popup_card

                with popup_card:
                    source_type_select = ui.select(
                        ['image', 'video', 'rtsp'],
                        value='image',
                        label='Type',
                    ).style('width: 100%; margin-bottom: 0.75rem;')

                    ui_refs['source_type_select'] = source_type_select

                    source_path_input = ui.input(
                        label='URL',
                        placeholder='Enter path or URL'
                    ).style('width: 100%; margin-bottom: 0.75rem;')

                    ui_refs['source_path_input'] = source_path_input

                    with ui.row().classes('justify-end q-gutter-sm'):
                        load_button = ui.button('Load', icon='play_arrow', color='primary')
                        ui_refs['load_button'] = load_button

            def toggle_popup():
                current_display = popup_card.style.get('display', 'none')
                if current_display == 'none':
                    popup_card.style('display: block;')
                else:
                    popup_card.style('display: none;')

            open_popup_button.on('click', toggle_popup)

            with ui.column().classes('items-center justify-center').style(
                    'flex: 1; width: 100%; background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%); position: relative;'):

                media_video = ui.video(src='', autoplay=True, muted=True).style(
                    'max-width: 100%; max-height: 100%; object-fit: contain; display: none;')
                media_video.on("ended", lambda: ui.notify("Video ended"))
                ui_refs['media_video'] = media_video

                media_image = ui.interactive_image('').style(
                    'max-width: 100%; max-height: 100%; object-fit: contain; display: none;')
                ui_refs['media_image'] = media_image

                media_static_image = ui.image('').style(
                    'max-width: 100%; max-height: 100%; object-fit: contain; display: none;')
                ui_refs['media_static_image'] = media_static_image

                placeholder = ui.column().classes('items-center q-gutter-md').style(
                    'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); pointer-events: none;')

                ui_refs['placeholder'] = placeholder
                with placeholder:
                    ui.icon('videocam', size='4xl').style('color: #9ca3af; font-size: 4rem;')
                    ui.label('Video Feed').classes('text-h5 text-weight-medium')
                    ui.label('Select media source and click Load').classes('text-body2')

            async def load_media(button):
                with loading_button(button):
                    source_type_select = ui_refs['source_type_select']
                    source_path_input = ui_refs['source_path_input']
                    media_image = ui_refs['media_image']
                    media_static_image = ui_refs['media_static_image']
                    media_video = ui_refs['media_video']
                    placeholder = ui_refs['placeholder']
                    popup_card = ui_refs['popup_card']

                    source_type = source_type_select.value
                    source_path = source_path_input.value.strip()

                    if not source_path:
                        ui.notify('Please enter a source path', type='warning')
                        return

                    is_streaming['value'] = False
                    await asyncio.sleep(0.1)

                    if media_capture['value'] is not None:
                        if isinstance(media_capture['value'], cv2.VideoCapture):
                            media_capture['value'].release()
                        media_capture['value'] = None

                    current_frame['value'] = None

                    media_image.style('display: none;')
                    media_static_image.style('display: none;')
                    media_video.style('display: none;')

                    placeholder.style('display: none;')

                    popup_card.style('display: none;')

                    await stream_media(media_image, media_static_image, media_video, source_type, source_path)
                    ui.notify(f'Loaded {source_type}: {source_path}', type='positive')

            ui_refs['load_button'].on('click', lambda e: load_media(e.sender))


def traffic_section():
    with ui.column().classes('items-center justify-center').style('width: 400px; height: 100%;'):
        with ui.card().style(
                'width: 100%; background-color: white; border-radius: 0.75rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 2rem;'):
            ui.label('Traffic Light Status').classes('text-h4 text-weight-bold q-mb-lg text-center')

            color = get_current_color()

            create_traffic_light(color)

            ui.separator()

            info_panel(current_frame)


@app.get('/video')
async def serve_video(file_path: str):
    """Serve video files through HTTP"""
    try:
        video_path = Path(file_path)
        if video_path.exists() and video_path.is_file():
            return FileResponse(
                str(video_path),
                media_type='video/mp4',
                headers={'Accept-Ranges': 'bytes'}
            )
        else:
            return Response(status_code=404)
    except Exception as e:
        print(f"Error serving video: {e}")
        return Response(status_code=500)


@ui.page('/')
def main_page():
    ui.query('body').style('background-color: #f5f5f5; margin: 0; padding: 0;')

    header()

    with ui.row().style('width: 100%; height: calc(100vh); padding: 1.5rem; gap: 1.5rem;'):
        scene_section()
        traffic_section()



