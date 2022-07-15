import os
import re
from os.path import normpath


class ExecutableProvider:
    @staticmethod
    def qgis():
        if os.name == 'posix':
            return 'qgis_process'
        if os.name == 'nt':
            root_dir = r'C:/Program Files'
            regex = re.compile('QGIS.*')
            qgis_folder = ''
            for root, dirs, _ in os.walk(root_dir):
                for dir in dirs:
                    if regex.match(dir):
                        qgis_folder = dir
            if qgis_folder == '':
                raise Exception('QGIS not installed')
            return r"{}/{}/bin/qgis_process-qgis.bat".format(root_dir, qgis_folder)
        raise Exception('Unsupported OS')

    @staticmethod
    def cloud_compare():
        if os.name == 'posix':
            return 'cloudcompare.CloudCompare'
        if os.name == 'nt':
            return r'"C:\\Program Files\\CloudCompare\\CloudCompare.exe"'
        raise Exception('Unsupported OS')
