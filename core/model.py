import supervision as sv
import numpy as np
from numpy import ndarray
from ultralytics import YOLO

model = YOLO("../models/yolov8n.pt")


def count_cars_from_frame(frame: np.ndarray) -> tuple[int, None] | tuple[int, ndarray]:
    if frame is None:
        return 0, None

    try:
        res = model(frame, verbose=False)
        detections = sv.Detections.from_ultralytics(res[0])
        detections = detections[(detections.class_id == 2) | (detections.class_id == 5) | (detections.class_id == 7)]

        car_count = len(detections.class_id)

        annotated = frame.copy()
        labels = [
            f"{class_id} {class_name}"
            for class_id, class_name
            in zip(detections['class_name'], detections.class_id)
        ]

        box_annotator = sv.BoxAnnotator()
        label_annotator = sv.LabelAnnotator()

        annotated = box_annotator.annotate(annotated, detections)
        annotated = label_annotator.annotate(annotated, detections, labels)

        return car_count, annotated
    except Exception as e:
        print(f"Error detecting cars: {e}")
        return 0, frame
