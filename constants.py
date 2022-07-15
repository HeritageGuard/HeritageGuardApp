from enum import Enum

DATASETS_TABLE = 'dataset'
FILES_TABLE = 'file'
ELEMENTS_TABLE = 'element'


class FRAME_TYPES(Enum):
    DATASET = 0
    DETECT_360 = 1
    COMPARE = 2
    PANORAMAS = 3
    DEM_COMPARE = 4
