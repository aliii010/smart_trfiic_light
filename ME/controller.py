import cv2

from ME.model import count_cars_from_img

congestion_multipliers = {
    'low': 1.0,
    'medium': 1.5,
    'high': 2.0,
    'very_high': 2.5
}

lights = {
    "red": 10,
    "yellow": 3,
    "green": 5,

}

active_color = "red"
def get_congestion(counter):
    if counter > 15:
        return 'very_high'
    elif counter > 10:
        return 'high'
    elif counter > 5:
        return 'medium'
    else:
        return 'low'


def start():
    state = "red"
    count, fig = count_cars_from_img("../img.png")
    congestion = get_congestion(count)

    multiplier = congestion_multipliers.get(congestion, 1.0)

    return lights[state] * multiplier

def get_current_color():
    return active_color


start()