from os import path, makedirs


class DirectoryHelper:
    @staticmethod
    def ensure_exists(local_path):
        global_path = path.abspath(local_path)
        if not path.exists(global_path):
            makedirs(global_path)
        return global_path