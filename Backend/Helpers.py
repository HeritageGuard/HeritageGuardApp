import numpy as np


def area_from_bbox(bbox):
    if type(bbox) is str:
        bbox = np.fromstring(bbox[1:-1], dtype=np.int, sep=" ")
    return (int(bbox[3]) - int(bbox[1])) * (int(bbox[2]) - int(bbox[0]))
