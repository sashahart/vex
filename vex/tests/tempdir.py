import os
import tempfile
import shutil
from vex.tests import path_type


class TempDir(object):
    def __init__(self):
        self.path = None
        self.open()

    def __enter__(self):
        return self

    def _sanity(self):
        assert isinstance(self.path, path_type)
        assert b'..' not in self.path
        assert self.path not in (b'', b'/', b'//')
        assert os.path.exists(self.path)
        assert os.path.isdir(self.path)

    def open(self):
        self.path = tempfile.mkdtemp().encode('utf-8')
        self._sanity()

    def close(self):
        self._sanity()
        shutil.rmtree(self.path)

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class EmptyTempDir(TempDir):
    def close(self):
        self._sanity()
        os.rmdir(self.path)
