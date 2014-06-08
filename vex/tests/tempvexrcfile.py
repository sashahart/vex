import os
from vex.tests import path_type


class TempVexrcFile(object):
    def __init__(self, path, virtualenvs=None):
        assert isinstance(path, path_type)
        self.path = path
        self.virtualenvs = virtualenvs
        self.file_path = None
        self.open()

    def open(self):
        file_path = os.path.join(self.path, b'.vexrc')
        assert isinstance(file_path, path_type)
        with open(file_path, 'wb') as out:
            if self.virtualenvs:
                assert not isinstance(self.virtualenvs, bytes)
                line = ("virtualenvs=%s\n" % self.virtualenvs)
                out.write(line.encode('utf-8'))
        assert os.path.exists(file_path)
        self.file_path = file_path

    def close(self):
        if self.file_path:
            os.remove(self.file_path)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
