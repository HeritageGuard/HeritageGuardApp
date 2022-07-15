from functools import partial
from multiprocessing import Pool
from os import popen, rename
from os.path import exists, normpath, abspath

import numpy as np
import pdal
from geojson import Point

from Backend.DirectoryHelper import DirectoryHelper
from Backend.ExecutableProvider import ExecutableProvider
from Backend.Helpers import area_from_bbox
from Backend.Transformer import Transformer


class PointCloudTools:
    @staticmethod
    def crop(file_name, lat, lon, height, distance, radius=5, transformer=None):
        bounds, point = PointCloudTools._get_data(lat, lon, height, radius=radius, transformer=transformer)

        pool = Pool(1)
        results = pool.map(partial(PointCloudTools.execute_pipeline, file_name, bounds, distance), [point])
        pool.close()
        pool.join()
        return results[0]

    @staticmethod
    def crop_to_file(file_name, output_file_name, lat, lon, height, distance, radius=5, transformer=None):
        output_file_name = normpath(output_file_name)
        bounds, point = PointCloudTools._get_data(lat, lon, height, radius=radius, transformer=transformer)
        pool = Pool(1)
        results = pool.map(partial(PointCloudTools.execute_pipeline_and_write, file_name, bounds, distance, output_file_name),
                 [point])
        pool.close()
        pool.join()
        return results[0] != 0

    @staticmethod
    def _get_data(lat, lon, height, radius=5, transformer=None):
        if transformer is None:
            transformer = Transformer().transformer

        coords = transformer.transform(lat, lon)
        point = Point((coords[1], coords[0], float(height)))
        bounds = f"([{coords[1] - radius}, {coords[1] + radius}], [{coords[0] - radius}, {coords[0] + radius}])"
        return bounds, point

    @staticmethod
    def execute_pipeline_and_write(file_name, bounds, distance, output_file_name, point):
        output_file_name = output_file_name.replace('\\', '/')
        json = '[{{ "type": "readers.ept", "filename": "{}", "bounds": "{}" }}, {{ "type": "filters.crop", "point":"POINT({} {} {})", "distance": {} }}, {{ "type": "writers.las", "filename": "{}" }} ]'.format(file_name, bounds, point["coordinates"][0], point["coordinates"][1], point["coordinates"][2], distance, output_file_name)
        pipeline = pdal.Pipeline(json)
        pipeline.execute()
        return len(pipeline.arrays[0]) > 0

    @staticmethod
    def execute_pipeline(file_name, bounds, distance, point):
        xyz = np.empty((3, 0), dtype='float')
        json = '[{{ "type": "readers.ept", "filename": "{}", "bounds": "{}" }}, {{ "type": "filters.crop", "point":"POINT({} {} {})", "distance": {} }}]'.format(file_name, bounds, point["coordinates"][0], point["coordinates"][1], point["coordinates"][2], distance)
        pipeline = pdal.Pipeline(json)
        pipeline.execute()
        for points in pipeline.arrays:
            xyz = np.insert(xyz, 0, [[float(p[0]), float(p[1]), float(p[2])] for p in points], axis=1)
        return xyz

    @staticmethod
    def compare_point_clouds(element_a, element_b, dataset_a, dataset_b):
        report_output = abspath("./temp/{}_{}.asc".format(element_a.id, element_b.id))
        report_output_alt = abspath("./temp/{}_{}.asc".format(element_b.id, element_a.id))
        if exists(report_output) or exists(report_output_alt):
            if not exists(report_output):
                report_output = report_output_alt
        else:
            output_filename_a = PointCloudTools.get_point_cloud_path(element_a, dataset_a)
            output_filename_b = PointCloudTools.get_point_cloud_path(element_b, dataset_b)

            command = '{} -SILENT -NO_TIMESTAMP -C_EXPORT_FMT ASC -O -GLOBAL_SHIFT AUTO "{}" -O -GLOBAL_SHIFT AUTO "{}" -c2c_dist -max_dist 1 -model LS SPHERE 0.1'\
                .format(ExecutableProvider.cloud_compare(), output_filename_a, output_filename_b)
            print(command)
            stream = popen(command)
            output = stream.read().splitlines()
            if output[len(output) - 2].endswith('successfully'):
                report_file = output[len(output) - 2].split("'")[1]
                if exists(report_file):
                    rename(report_file, report_output)
        return PointCloudTools.compute_histograms(report_output)
    @staticmethod
    def compute_histograms(data_path):
        if not exists(data_path):
            return (-100000000, '')
        data = np.genfromtxt(data_path, delimiter=" ", usecols=(-1))
        histograms = np.histogram(data, bins=(0.05, 0.1, 0.15, 0.2, 0.25, 0.35, 0.45, 1, 10000), density=False)
        histograms = histograms[0]
        histograms = np.around(histograms * (100 / np.sum(histograms)), decimals=2).tolist()
        return (
            np.sum(histograms[:3]) - np.sum(histograms[3:]),
            str(histograms)
        )
    @staticmethod
    def get_point_cloud_path(element, dataset):
        default_path = abspath('./data/{}/{}.las'.format(dataset.id, element.id))
        if exists(default_path):
            return default_path
        else:
            dataset_path = DirectoryHelper.ensure_exists('./temp/' + str(dataset.id))
            output_filename = normpath(dataset_path + '/' + str(element.id) + '.las')
            if exists(output_filename):
                return output_filename
            else:
                area = area_from_bbox(element.bbox)
                distance = area / 5000
                if distance < 2:
                    distance = 2
                if distance > 5:
                    distance = 5

                print('Cropping point cloud with distance {} and area {}'.format(distance, area))

                PointCloudTools.crop_to_file(dataset.point_cloud_path, output_filename, element.lat, element.lon, element.height, distance)

                return output_filename
