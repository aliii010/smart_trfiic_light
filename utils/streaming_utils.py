import base64
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


def frame_to_base64(frame: np.ndarray) -> str:
    """Convert OpenCV frame to base64 encoded image"""
    if frame is None:
        return ''
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buffer).decode('utf-8')



def open_media_source(source_type: str, source_path: str) -> Optional[cv2.VideoCapture]:
    """Open media source based on type"""
    if not source_path:
        return None

    try:
        if source_type == 'rtsp':
            # RTSP stream
            cap = cv2.VideoCapture(source_path, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                return None
            # Set buffer size to reduce latency
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return cap
        elif source_type == 'video':
            # Video file
            if not Path(source_path).exists():
                return None
            cap = cv2.VideoCapture(source_path)
            return cap if cap.isOpened() else None
        elif source_type == 'image':
            # Image file
            if not Path(source_path).exists():
                return None
            # For images, we'll read it directly, not as VideoCapture
            return source_path
    except Exception as e:
        print(f"Error opening media source: {e}")
        return None


