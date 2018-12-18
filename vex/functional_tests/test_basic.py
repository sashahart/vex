from __future__ import unicode_literals
import os
import sys
import re
import logging
from threading import Timer
from subprocess import Popen, PIPE
from vex.tests import path_type
from vex.tests.tempdir import TempDir, EmptyTempDir
from vex.tests.tempvenv import TempVenv
from vex.tests.tempvexrcfile import TempVexrcFile

if sys.version_info < (3, 0):
    FileNotFoundError = OSError


HERE = os.path.dirname(os.path.abspath(__file__))


logging.basicConfig(level=logging.DEBUG)


class Run(object):
    """Boilerplate for running a vex process with given parameters.

    Context manager to ensure cleanup.
    Timeout to try to prevent hung tests.
    Can fake arguments and environment.
    Normally expect tests to wait until process finishes,
    but this is left to them for now.
    """
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

    def start(self):
        env = self.env.copy()
        path = os.environ['PATH']
        if isinstance(path, bytes):
            path = path.decode('utf-8')
        env['PATH'] = path
        process = None
        try:
            args = ['vex'] + self.args
            logging.debug("ARGS %r env %r", args, env)
            process = Popen(
                args, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=env)
        except FileNotFoundError as error:
            if error.errno != 2:
                raise
            self.command_found = False
            process = None
        else:
            if self.timeout is not None:
                self.timer = Timer(self.timeout, self.kill)
                self.timer.start()
            self.command_found = True
            self.process = process

    def __enter__(self):
        self.start()
        return self

    def kill(self):
        self.process.kill()

    def poll(self):
        self.process.poll()
        self.returned = self.process.returncode

    def finish(self, inp=None):
        assert inp is None or isinstance(inp, bytes)
        if self.process:
            out, err = self.process.communicate(inp)
            self.out = out
            self.err = err
            logging.debug("OUT %s", out.decode('utf-8'))
            logging.debug("ERR %s", err.decode('utf-8'))
            self.returned = self.process.returncode

    def __exit__(self, exc_type, exc_value, traceback):
        if self.timer:
            self.timer.cancel()
            self.timer = None
        if self.process and self.process.poll() is None:
            self.kill()


def test_runs_without_args():
    """vex

    Runs, but emits an error, proving that the test environment actually does
    have a vex executable on $PATH (as when run in a virtualenv after 'pip
    install vex').
    """
    with Run([], timeout=0.5) as run:
        run.finish()
        assert run.command_found is True, run.command_found
        assert run.returned == 1


def test_help():
    """vex --help

    Emits stuff containing at least '--help', not an error.
    """
    with Run(['--help'], timeout=0.5) as run:
        run.finish()
        assert run.out is not None
        assert run.out.startswith(b'usage'), "unexpected output on stdout"
        assert b'--help' in run.out, "unexpected output on stdout"
        assert not run.err, "unexpected presence of output on stderr"


def test_version():
    """vex --version

    Emits a string of numbers and periods, one newline
    """
    with Run(['--version'], timeout=0.5) as run:
        run.finish()
        assert run.out is not None
        match = re.match(br'^\d+\.\d+\.\d+\n$', run.out)
        assert match


def test_list():
    """vex --list

    Emits a list of directories in ve_base separated by newline
    """
    ve_base = TempDir()
    os.mkdir(os.path.join(ve_base.path, b"foo"))
    os.mkdir(os.path.join(ve_base.path, b"bar"))
    os.mkdir(os.path.join(ve_base.path, b"-nope"))
    env = {'WORKON_HOME': ve_base.path}
    with ve_base, Run(['--list'], env=env, timeout=0.5) as run:
        run.finish()
        assert not run.err
        assert run.out == b'bar\nfoo\n'


def test_list_no_ve_base():
    nonexistent = os.path.join('/tmp/whatever/foo/bar')
    assert not os.path.exists(nonexistent)
    env = {'WORKON_HOME': nonexistent}
    with Run(['--list'], env=env, timeout=0.5) as run:
        run.finish()
        assert run.returned == 1
        assert not run.out
        assert run.err
        assert nonexistent.encode("ascii") in run.err


class TestShellConfig(object):

    def test_no_ve_base(self):
        """vex --shell-config bash with e.g. no ~/.virtualenvs
        """
        env = {'WORKON_HOME': '/totally/nonexistent'}
        assert not os.path.exists(env['WORKON_HOME'])
        with Run(['--shell-config', 'bash'], env=env, timeout=0.5) as run:
            run.finish()
            assert run.out
            assert not run.err

    def test_no_arg(self):
        """vex --shell-config

        Non-traceback error.
        """
        with Run(['--shell-config'], timeout=0.5) as run:
            run.finish()
            assert not run.out
            assert run.err
            assert not run.err.startswith(b'Traceback')

    def test_bash(self):
        """vex --shell-config bash

        Emits something and doesn't crash
        """
        env = {'WORKON_HOME': os.getcwd()}
        with Run(['--shell-config', 'bash'], env=env, timeout=0.5) as run:
            run.finish()
            assert run.out
            assert not run.err

    def test_zsh(self):
        """vex --shell-config zsh

        Emits something and doesn't crash
        """
        env = {'WORKON_HOME': os.getcwd()}
        with Run(['--shell-config', 'zsh'], env=env, timeout=0.5) as run:
            run.finish()
            assert run.out
            assert not run.err

    def test_fish(self):
        """vex --shell-config fish

        Emits something and doesn't crash
        """
        env = {'WORKON_HOME': os.getcwd()}
        with Run(['--shell-config', 'fish'], env=env, timeout=0.5) as run:
            run.finish()
            assert run.out
            assert not run.err


def test_find_with_HOME():
    """vex venvname echo foo

    with HOME set to a path containing a .virtualenvs dir
    containing a directory named venvname,
    resolve venvname as that directory and run without error.
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
        # It's not ideal that we make a virtualenv only once,
        # but I'd rather do this than use a fake virtualenv
        # or wait an hour for tests to finish most of the time
        self.parent = TempDir()
        self.venv = TempVenv(self.parent.path, 'vex_tests', [])
        self.venv.open()

    def teardown_class(self):
        try:
            self.venv.close()
        finally:
            self.parent.close()

    def test_virtualenv_created(self):
        """Spurious test showing the 'test fixture' set up
        """
        bin_path = os.path.join(self.venv.path, b'bin')
        assert isinstance(bin_path, path_type)
        assert os.path.exists(bin_path)

    def test_inappropriate_abspath(self):
        """vex /stupid/absolute/path echo foo

        This should be rejected with a non-traceback error
        """
        assert self.venv.path != self.venv.name
        assert len(self.venv.path) > len(self.venv.name)
        assert os.path.abspath(self.venv.path) == self.venv.path
        with Run([self.venv.path, 'echo', 'foo']) as run:
            run.finish()
            assert run.command_found
            assert run.returned == 1
            assert run.out != b'foo\n'
            assert b'Traceback' not in run.err
            assert b'AssertionError' not in run.err

    def test_find_with_vexrc(self):
        """vex venvname echo foo

        with $HOME pointing to a directory containing a .vexrc file
        which contains a virtualenvs= line,
        resolve first positional argument as virtualenv name under the path
        given in the .vexrc.
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
        """vex --config somefile venvname echo foo

        with arbitrary path passed as --config,
        being the location of a .vexrc containing a virtualenvs= line,
        resolve first positional argument as virtualenv name under the path
        given in the .vexrc.
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
        """vex venvname echo foo

        with $WORKON_HOME set and nothing else,
        resolve first positional argument as virtualenv name under
        $WORKON_HOME/
        """
        # This one is easier, we just point WORKON_HOME
        # at the directory containing our venv
        env = {'HOME': 'ignore', 'WORKON_HOME': self.parent.path.decode('utf-8')}
        with Run([self.venv.name, 'echo', 'foo'], env=env) as run:
            run.finish()
            assert run.command_found
            assert run.returned == 0
            assert run.out == b'foo\n'

    def test_find_with_path_option(self):
        """vex --path venvpath echo foo

        no error, echoes foo
        """
        with Run(["--path", self.venv.path, 'echo', 'foo']) as run:
            run.finish()
            assert os.path.abspath(self.venv.path) == self.venv.path
            assert not run.err, "unexpected stderr output: %r" % run.err
            assert run.command_found
            assert run.returned == 0
            assert run.out == b'foo\n'

    def test_cwd_option(self):
        """vex --cwd cwdpath venvname pwd

        prints out the value of cwdpath, no errors
        """
        env = {'HOME': 'ignore', 'WORKON_HOME': self.parent.path.decode('utf-8')}
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

    def test_invalid_cwd(self):
        """vex --cwd nonexistentpath venvname pwd

        error but no traceback
        """
        env = {'WORKON_HOME': self.parent.path.decode('utf-8')}
        cwd = os.path.join('tmp', 'reallydoesnotexist')
        assert not os.path.exists(cwd)
        with Run(['--cwd', cwd, self.venv.name, 'pwd'], env=env) as run:
            run.finish()
            assert run.command_found
            assert run.err
            assert not run.err.startswith(b'Traceback')
            assert run.returned == 1



class TestMakeAndRemove(object):
    def test_make(self):
        parent = TempDir()
        venv_name = b'make_test'
        venv_path = os.path.join(parent.path, venv_name)
        assert not os.path.exists(venv_path)
        assert os.path.exists(parent.path)
        env = {'WORKON_HOME': parent.path.decode('utf-8')}
        with Run(['--make', venv_name, 'echo', '42'], env=env) as run:
            run.finish()
            assert run.out is not None
            assert b'42' in run.out
            assert run.command_found
            assert run.returned == 0
            assert not run.err
            assert os.path.exists(venv_path)
        parent.close()

    def test_make_with_vexrc_python(self):
        parent = TempDir()
        venv_name = b'make_test_vexrc_python'
        venv_path = os.path.join(parent.path, venv_name)
        assert not os.path.exists(venv_path)
        assert os.path.exists(parent.path)
        home = TempDir()
        env = {
            'HOME': home.path,
            'WORKON_HOME': parent.path.decode('utf-8')
        }
        not_python = os.path.join(HERE, "not_python")
        vexrc = TempVexrcFile(
            home.path,
            virtualenvs=parent.path.decode('utf-8'),
            python=not_python,
        )
        run = Run(['--make', venv_name, 'echo', '42'], env=env)
        with home, vexrc, run:
            run.finish()
            assert run.out is not None
            assert b'not python' in run.out
            assert b'42' in run.out
            assert run.command_found
            assert run.returned == 0
            assert not run.err
        parent.close()

    def test_remove(self):
        parent = TempDir()
        venv = TempVenv(parent.path, 'vex_tests', [])
        venv.open()
        assert os.path.exists(venv.path)
        assert os.path.exists(parent.path)
        env = {'WORKON_HOME': parent.path.decode('utf-8')}
        with Run(['--remove', venv.name, 'echo', '42'], env=env) as run:
            run.finish()
            assert run.out is not None
            assert b'42' in run.out
            assert run.command_found
            assert run.returned == 0
            assert not run.err
            assert not os.path.exists(venv.path)
            assert os.path.exists(parent.path)
        venv.close()
        parent.close()

    def test_make_and_remove(self):
        parent = TempDir()
        env = {'WORKON_HOME': parent.path.decode('utf-8')}
        venv_name = b"make_and_remove"
        venv_path = os.path.join(parent.path, venv_name)
        assert os.path.exists(parent.path)
        assert not os.path.exists(venv_path)
        with Run(['--make', '--remove', venv_name,
                  'python', '-c',
                  'import os; print(os.environ.get("VIRTUAL_ENV"))'
                  ], env=env) as run:
            run.finish()
            assert run.out
            lines = [line.strip() for line in run.out.strip().split(b'\n')]
            assert b'make_and_remove' in lines[-2], lines
            assert b'remove' in lines[-1].lower(), lines
            assert b'make_and_remove' in lines[-1], lines
            assert run.command_found
            assert run.returned == 0
            assert not run.err
            assert not os.path.exists(venv_path)
            assert os.path.exists(parent.path)
        parent.close()

    def test_pydoc(self):
        parent = TempDir()
        env = {'WORKON_HOME': parent.path.decode('utf-8')}
        venv_name = b'test_pydoc'
        venv_path = os.path.join(parent.path, venv_name)
        assert not os.path.exists(venv_path)
        with Run(['--make', '--remove', venv_name,
                  'pydoc', 'pip'], env=env) as run:
            run.finish(b'q')
            assert run.command_found
            assert run.returned == 0
            assert not run.err
            assert b"no Python documentation found for 'pip'" not in run.out
            start = run.out.find(b'FILE')
            assert start > -1
            chunk = run.out[start:].strip()
            lines = chunk.split(b'\n')
            assert lines
            assert lines[0] == b'FILE'
            assert venv_path in lines[1]
