from __future__ import unicode_literals
import os
import sys
import tempfile
import shutil
from threading import Timer
from subprocess import Popen, PIPE

if sys.version_info < (3, 0):
    FileNotFoundError = OSError

try:
    unicode
    str_type = unicode
except NameError:
    str_type = str


path_type = bytes


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


class Run(object):
    def __init__(self, args=None, env=None, timeout=None):
        self.args = args or []
        self.env = env.copy() if env else {}
        self.timeout = timeout
        #
        self.timer = None
        self.process = None
        #
        self.command_found = None
        self.returned = None
        self.out = None
        self.err = None

    def __enter__(self):
        process = None
        env = self.env.copy()
        path = os.environ['PATH']
        if isinstance(path, bytes):
            path = path.decode('utf-8')
        env['PATH'] = path
        try:
            args = ['vex'] + self.args
            print("ARGS %r env %r" % (args, env))
            process = Popen(
                args, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=env)
        except FileNotFoundError as error:
            if error.errno != 2:
                raise
            self.command_found = False
            process = None
        else:
            if self.timer:
                self.timer = Timer(self.timeout, self.kill)
                self.timer.start()
            self.command_found = True
            self.process = process
        return self

    def kill(self):
        self.process.kill()

    def poll(self):
        self.returned = self.process.poll()

    def finish(self, inp=None):
        assert inp is None or isinstance(inp, bytes)
        if self.process:
            out, err = self.process.communicate(inp)
            self.out = out
            self.err = err
            print("OUT %s" % out.decode('utf-8'))
            print("ERR %s" % err.decode('utf-8'))
            self.returned = self.process.returncode

    def __exit__(self, exc_type, exc_value, traceback):
        if self.timer:
            self.timer.cancel()
            self.timer = None
        if self.process and self.process.poll() is None:
            self.kill()


def test_runs_without_args():
    """
    can be found on PATH, etc.
    (assuming test is run in a virtualenv after pip install vex)
    """
    with Run([], timeout=0.5) as run:
        run.finish()
        assert run.command_found is True, run.command_found
        assert run.returned != 0


def test_help():
    with Run(['--help'], timeout=0.5) as run:
        run.finish()
        assert run.out is not None
        assert run.out.startswith(b'usage'), "unexpected output on stdout"
        assert b'--help' in run.out, "unexpected output on stdout"
        assert not run.err, "unexpected presence of output on stderr"


def test_find_with_HOME():
    """Make sure we can find virtualenvs in $HOME/.virtualenvs/
    """
    # 1. Make a temp directory
    # 2. Point the HOME variable at that
    # 3. Make a .virtualenvs directory in it
    # 4. Make a tempvenv inside that (time-consuming though...)
    # 5. run vex, passing basename of the tempvenv
    home = TempDir()
    workon_home = os.path.join(home.path, b'.virtualenvs')
    assert isinstance(workon_home, path_type)
    os.mkdir(workon_home)
    name = 'vex_test_find_with_HOME'
    venv = TempVenv(workon_home, name, [])
    env = {'HOME': home.path}
    with home, venv, Run([name, 'echo', 'foo'], env=env) as run:
        run.finish()
        assert run.command_found
        assert run.returned == 0
        assert run.out == b'foo\n'


# TODO: won't work on windows: no echo, pwd, etc. mark xfail or something
class TestWithVirtualenv(object):
    def setup_class(self):
        self.parent = TempDir()
        self.venv = TempVenv(self.parent.path, 'vex_tests', [])
        self.venv.open()

    def teardown_class(self):
        try:
            self.venv.close()
        finally:
            self.parent.close()

    def test_virtualenv_created(self):
        bin_path = os.path.join(self.venv.path, b'bin')
        assert isinstance(bin_path, path_type)
        assert os.path.exists(bin_path)

    def test_inappropriate_abspath(self):
        assert self.venv.path != self.venv.name
        assert len(self.venv.path) > len(self.venv.name)
        with Run([self.venv.path, 'echo', 'foo']) as run:
            run.finish()
            assert run.command_found
            assert run.returned != 0
            assert run.out != b'foo\n'
            assert b'Traceback' not in run.err
            assert b'AssertionError' not in run.err

    def test_find_with_vexrc(self):
        """Make sure we can find virtualenvs in the location given in .vexrc
        """
        # 1. Make a temp directory to play the role as HOME
        # 2. Point the HOME environment variable at that directory
        # 3. Make a temp vexrc in that directory.
        #    This has a virtualenvs= line which points at
        #    the directory containing the temp virtualenv.
        # 4. run vex
        home = TempDir()
        env = {'HOME': home.path}
        vexrc = TempVexrcFile(
            home.path,
            virtualenvs=self.parent.path.decode('utf-8'))
        assert isinstance(home.path, path_type)
        assert isinstance(vexrc.file_path, path_type)
        assert os.path.exists(vexrc.file_path)
        run = Run([self.venv.name, 'echo', 'foo'], env=env)
        with home, vexrc, run:
            run.finish()
            assert run.command_found
            assert run.returned == 0
            assert run.out == b'foo\n'

    def test_find_with_config_option_vexrc(self):
        """Make sure we can find virtualenvs in the location given in .vexrc
        """
        # 1. Make a temp directory to play the role as HOME
        # 2. Point the HOME environment variable at that directory
        # 3. Make a temp vexrc in that directory.
        #    This has a virtualenvs= line which points at
        #    the directory containing the temp virtualenv.
        # 4. run vex
        home = TempDir()
        vexrc = TempVexrcFile(
            home.path,
            virtualenvs=self.parent.path.decode('utf-8'))
        assert isinstance(home.path, path_type)
        assert isinstance(vexrc.file_path, path_type)
        assert os.path.exists(vexrc.file_path)
        run = Run(['--config', vexrc.file_path, self.venv.name, 'echo', 'foo'])
        with home, vexrc, run:
            run.finish()
            assert run.command_found
            assert run.returned == 0
            assert run.out == b'foo\n'

    def test_find_with_WORKON_HOME(self):
        """Make sure we can find virtualenvs in $WORKON_HOME/
        """
        # This one is easier, we just point WORKON_HOME
        # at the directory containing our venv
        env = {'WORKON_HOME': self.parent.path.decode('utf-8')}
        with Run([self.venv.name, 'echo', 'foo'], env=env) as run:
            run.finish()
            assert run.command_found
            assert run.returned == 0
            assert run.out == b'foo\n'

    def test_find_with_path_option(self):
        with Run(["--path", self.venv.path, 'echo', 'foo']) as run:
            run.finish()
            assert not run.err, "unexpected stderr output: %r" % run.err
            assert run.command_found
            assert run.returned == 0
            assert run.out == b'foo\n'

    def test_cwd_option(self):
        env = {'WORKON_HOME': self.parent.path.decode('utf-8')}
        with EmptyTempDir() as cwd, \
             Run(['--cwd', cwd.path, self.venv.name, 'pwd'], env=env) as run:
            run.finish()
            assert run.command_found
            assert not run.err.startswith(b'Traceback')
            assert run.returned == 0
            assert cwd.path
            assert self.venv.path
            assert cwd.path != self.venv.path
            assert cwd.path != self.parent.path
            assert run.out == cwd.path + b'\n'
