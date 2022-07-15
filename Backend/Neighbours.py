from math import radians, sqrt

import numpy as np
from sklearn.neighbors import BallTree

from Backend.Helpers import area_from_bbox


def prepare_data(data, dataset_id=0):
    if dataset_id > 0:
        data = data.loc[data["dataset_id"] == dataset_id]

    list_of_coords = data[["id", "lat", "lon", "bbox", "element_type"]]
    modified = list_of_coords.apply(
        lambda x: x.apply(radians) if x.name == "lat" or x.name == "lon" else x
    )
    return modified


class Neighbours:
    def __init__(self):
        self.earth_radius = 6371000

    def Process(self, data, deviation=0.1, test_radius=2):
        lat_lon_as_radians = [[radians(x.lat), radians(x.lon)] for x in data]
        tree = BallTree(lat_lon_as_radians, metric="haversine")

        indexes, results = tree.query_radius(
            lat_lon_as_radians, r=test_radius / self.earth_radius,
            return_distance=True)
        correlation_id = 1
        correlation_dictionary = {1: []}
        for (i, r) in enumerate(indexes):
            data[i].area = area_from_bbox(data[i].bbox)
            if len(r) > 0:
                related_ids = [
                    self._from_index_to_id(x, data)
                    for (j, x) in enumerate(r)
                    if x != i
                       and results[i][j] * self.earth_radius
                       < sqrt(data[i].area) * deviation
                ]

                for (j, x) in enumerate(r):
                    if (
                            x != i
                            and hasattr(data[x], "correlation_id")
                            and results[i][j] * self.earth_radius
                            < sqrt(data[i].area) * deviation
                            and data[x].element_type == data[i].element_type
                    ):
                        data[i].correlation_id = data[x].correlation_id
                        correlation_dictionary[correlation_id].append(data[i])
                    elif (
                            x != i
                            and not hasattr(data[x], "correlation_id")
                            and hasattr(data[i], "correlation_id")
                            and results[i][j] * self.earth_radius
                            < sqrt(data[i].area) * deviation
                            and data[x].element_type == data[i].element_type
                    ):
                        data[x].correlation_id = data[i].correlation_id
                        correlation_dictionary[correlation_id].append(data[x])

                if not hasattr(data[i], "correlation_id"):
                    data[i].correlation_id = correlation_id
                    correlation_dictionary[correlation_id] = [data[i]]
                    correlation_id += 1
                    if correlation_id not in correlation_dictionary:
                        correlation_dictionary[correlation_id] = []
                data[i].related_ids = " ".join(str(e) for e in related_ids)
        return [max(x, key=lambda o: o.area) for x in correlation_dictionary.values() if len(x) > 0]

    def Compare(self, data_A, data_B, deviation=0.1, test_radius=1):
        lat_lon_as_radians_A = [[radians(x.lat), radians(x.lon)] for x in data_A]
        tree_A = BallTree(lat_lon_as_radians_A, metric="haversine")

        lat_lon_as_radians_B = [[radians(x.lat), radians(x.lon)] for x in data_B]
        tree_B = BallTree(lat_lon_as_radians_B, metric="haversine")

        indexes_A_in_B, results_A_in_B = tree_B.query_radius(
            lat_lon_as_radians_A, r=test_radius / self.earth_radius,
            return_distance=True)

        indexes_B_in_A, results_B_in_A = tree_A.query_radius(
            lat_lon_as_radians_B, r=test_radius / self.earth_radius,
            return_distance=True)

        items_not_in_A = []
        items_not_in_B = []
        differing_items = []
        other_elements = []

        for a in range(len(data_A)):
            if len(indexes_A_in_B[a]) == 0:
                items_not_in_B.append(self._get_best_element(data_A[a], data_A, tree_A, allow_returning_self=True))
            else:
                item_in_A = self._get_best_element(data_A[a], data_A, tree_A, allow_returning_self=True)
                item_in_B = self._get_best_element(item_in_A, data_B, tree_B,
                                                   elements=[data_B[x] for x in indexes_A_in_B[a]],
                                                   distances=results_A_in_B[a], use_closest_area=True)

                if item_in_A.element_type != item_in_B.element_type:
                    differing_items.append((item_in_A, item_in_B))
                else:
                    other_elements.append((item_in_A, item_in_B))

        for b in range(len(data_B)):
            if len(indexes_B_in_A[b]) == 0:
                items_not_in_A.append(self._get_best_element(data_B[b], data_B, tree_B, allow_returning_self=True))

        return items_not_in_A, items_not_in_B, differing_items, other_elements

    def _get_best_element(self, element, dataset, tree, test_radius=1, elements=None, distances=None,
                          allow_returning_self=False, use_closest_area=False):
        if elements is None:
            indexes, results = tree.query_radius([[radians(element.lat), radians(element.lon)]],
                                                 r=test_radius / self.earth_radius,
                                                 return_distance=True)
            elements = [dataset[x] for x in indexes[0]]
            distances = results[0]

        areas = np.array([area_from_bbox(x.bbox) for x in elements])
        min_distance_index = np.ma.masked_equal(distances, 0, copy=False).argmin()
        element_area = area_from_bbox(element.bbox)
        abs_areas = np.abs(areas - element_area)
        closest_area_index = abs_areas.argmin()

        scores = np.zeros(np.shape(elements))
        for index, _ in np.ndenumerate(scores):
            index = index[0]
            scores[index] = scores[index] + int(elements[index].score * 10)
            if use_closest_area and index == closest_area_index:
                scores[index] = scores[index] + 10
            if not use_closest_area:
                scores[index] = scores[index] + (1 - (100 / (areas[index] * 1000))) * 10
            if index == min_distance_index:
                scores[index] = scores[index] + 10
            if elements[index].element_type == element.element_type:
                scores[index] = scores[index] + 10
            if elements[index].id == element.id and not allow_returning_self:
                scores[index] = 0.0
        max_score_index = np.argmax(scores)

        if elements[max_score_index].element_type != element.element_type:
            print('RETURNING WRONG TYPE', elements[max_score_index].id, elements[max_score_index].element_type,
                  element.id, element.element_type)
        if elements[max_score_index].id == element.id and allow_returning_self is False:
            print('RETURNING SELF')
            return None
        return elements[max_score_index]

    @staticmethod
    def _from_index_to_id(index, data):
        return data[index].id
