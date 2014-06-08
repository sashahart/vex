import os
import shutil
from subprocess import Popen
from vex.tests import path_type, str_type


class TempVenv(object):
    def __init__(self, parent, name, args):
        assert isinstance(parent, path_type)
        assert isinstance(name, str_type)
        assert os.path.abspath(parent) == parent
        self.parent = parent
        self.name = name
        self.args = args or []
        self.path = os.path.join(parent, name.encode('utf-8'))
        self.open()

    def open(self):
        assert isinstance(self.parent, path_type)
        assert os.path.exists(self.parent)
        args = ['virtualenv', '--quiet', self.path] + self.args
        if not os.path.exists(self.path):
            process = Popen(args)
            process.wait()
            assert process.returncode == 0
        assert os.path.exists(self.path)
        bin_path = os.path.join(self.path, b'bin')
        assert os.path.exists(bin_path)

    def close(self):
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
        assert not os.path.exists(self.path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
