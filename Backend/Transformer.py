from pyproj import Transformer as Tr


class SingletonTransformer(type):
    _instances = {}

    def __call__(cls, from_crs="epsg:4326", to_crs="epsg:3346"):
        key = str(from_crs).lower() + str(to_crs).lower()
        if key not in cls._instances:
            cls._instances[key] = super(SingletonTransformer, cls).__call__(from_crs, to_crs)
        return cls._instances[key]


class Transformer(metaclass=SingletonTransformer):
    def __init__(self, from_crs="epsg:4326", to_crs="epsg:3346"):
        self.transformer = Tr.from_crs(str(from_crs).lower(), str(to_crs).lower())
