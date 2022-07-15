import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patches
from mrcnn.config import Config
from mrcnn.model import MaskRCNN
from mrcnn.visualize import random_colors


class PredictOrto:
    def __init__(self):
        self.image_titles = []
        self.rcnn = None
        self.class_names = [
            "BG",
            "objects",
            "Stoglangiai",
            "Tūriniai stoglangiai",
            "Kaminai",
            "classifications",
        ]

    def initRCNN(self):
        class TestConfig(Config):
            NAME = "test"
            GPU_COUNT = 1
            BATCH_SIZE = 1
            IMAGES_PER_GPU = 1
            NUM_CLASSES = len(self.class_names)
            PRE_NMS_LIMIT = 6000

        config = TestConfig()
        # define the model
        self.rcnn = MaskRCNN(mode="inference", model_dir=".", config=config)
        self.rcnn.load_weights("./Models/model.h5", by_name=True)

    def detect_instances_single(self, image):
        return self.rcnn.detect([image])
