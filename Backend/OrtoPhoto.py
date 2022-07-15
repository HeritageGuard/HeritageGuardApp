import numpy as np
import rasterio

from rasterio.windows import Window

from Backend.Transformer import Transformer


class OrtoImage:
    def __init__(self, filename, crs="epsg:3346"):
        self.raster = rasterio.open(filename, crs=crs)
        if self.raster.crs is None:
            raster_crs = "epsg:3346"
        else:
            raster_crs = str(self.raster.crs).lower()
        self.transformer = Transformer(raster_crs, "epsg:4326").transformer
        self.width = self.raster.width
        self.height = self.raster.height

    def xy(self, x, y):
        east, north = self.raster.xy(y, x)
        return self.transformer.transform(north, east)

    def xy_raw(self, x, y):
        return self.raster.xy(y, x)

    def xy_window(self, x, y, window):
        transform = self.raster.window_transform(window)
        east, north = rasterio.transform.xy(transform, round(x), round(y))

        return self.transformer.transform(north, east)

    def window_centered(self, lat, lon, w, h):
        x, y = Transformer().transformer.transform(lat, lon)
        a, b = self.raster.index(y, x)
        win = Window.from_slices((a - w / 2, a + w / 2), (b - h / 2, b + h / 2))
        return np.moveaxis(np.asarray(self.raster.read(window=win)), 0, 2)

    @staticmethod
    def crop(x1, y1, w, h):
        return Window.from_slices((x1, w), (y1, h))

    def cut_up_2(self, size, overlay=0):
        start_x = 0
        start_y = 0
        end_x = size
        end_y = size
        col_index = 0
        while end_x + size <= self.raster.height:
            col = []
            while end_y + size <= self.raster.width:
                col.append(self.crop(start_x, start_y, end_x, end_y))
                start_y = end_y - overlay
                end_y = end_y + size - overlay
            start_x = end_x - overlay
            end_x = end_x + size - overlay
            start_y = 0
            end_y = size
            col_index = col_index + 1
            yield col_index, col


class DEMImage:
    def __init__(self, filename, crs="epsg:3346"):
        self.raster = rasterio.open(filename, crs=crs)

    def get_elevation(self, lat, lon):
        x, y = Transformer("epsg:4326", self.raster.crs).transformer.transform(lat, lon)
        vals = self.raster.sample([(y, x)])
        return next(vals)[0]
