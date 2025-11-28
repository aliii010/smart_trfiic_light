import supervision as sv
import cv2
from ultralytics import YOLO

model = YOLO("../yolov8n.pt")

def count_cars_from_img(file_path):
    file = cv2.imread(file_path)

    res = model(file)

    annotated = file.copy()
    detections = sv.Detections.from_ultralytics(res[0])
    detections = detections[detections.class_id == 2]

    car_counts = len(detections.class_id)

    labels = [
        f"{class_id} {class_name}"
        for class_id, class_name
        in zip(detections['class_name'], detections.class_id)
    ]

    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()

    annotated = box_annotator.annotate(annotated, detections)
    annotated = label_annotator.annotate(annotated, detections, labels)

    return car_counts, annotated

