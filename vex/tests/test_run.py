from __future__ import unicode_literals
import os
import os.path
import subprocess
import platform
from mock import patch
from pytest import raises
from vex import run
from vex import exceptions
from . fakes import FakeEnviron, PatchedModule, FakePopen


def test_get_environ():
    path = 'thing'
    defaults = {'from_defaults': 'b'}
    original = {
        'PATH': os.path.pathsep.join(['crap', 'bad_old_ve/bin', 'junk']),
        'from_passed': 'x',
        'PYTHONHOME': 'removeme',
        'VIRTUAL_ENV': 'bad_old_ve',
    }
    passed_environ = original.copy()
    with FakeEnviron() as os_environ, \
         PatchedModule(os.path, exists=lambda path: True):
        result = run.get_environ(passed_environ, defaults, path)
        # os.environ should not be changed in any way.
        assert len(os_environ) == 0
    # nor should the passed environ be changed in any way.
    assert sorted(original.items()) == sorted(passed_environ.items())
    # but result should inherit from passed
    assert result['from_passed'] == 'x'
    # and should update from defaults
    assert result['from_defaults'] == 'b'
    # except with no PYTHONHOME
    assert 'PYTHONHOME' not in result
    # and PATH is prepended to. but without bad old ve's bin.
    assert result['PATH'] == os.path.pathsep.join(
        ['thing/bin', 'crap', 'junk']
    )
    assert result['VIRTUAL_ENV'] == path


def test_run():
    # mock subprocess.Popen because we are cowards
    with PatchedModule(os.path, exists=lambda path: True), \
       PatchedModule(subprocess, Popen=FakePopen(returncode=888)) as mod:
        assert not mod.Popen.waited
        command = 'foo'
        env = {'this': 'irrelevant'}
        cwd = 'also_irrelevant'
        returncode = run.run(command, env=env, cwd=cwd)
        assert mod.Popen.waited
        assert mod.Popen.command == command
        assert mod.Popen.env == env
        assert mod.Popen.cwd == cwd
        assert returncode == 888


def test_run_bad_command():
    env = os.environ.copy()
    returncode = run.run('blah_unlikely', env=env,  cwd='.')
    assert returncode is None


class TestGetEnviron(object):
    def test_ve_path_None(self):
        with raises(exceptions.BadConfig):
            run.get_environ({}, {}, None)

    def test_ve_path_empty_string(self):
        with raises(exceptions.BadConfig):
            run.get_environ({}, {}, '')

    def test_copies_original(self):
        original = {'foo': 'bar'}
        defaults = {}
        ve_path = 'blah'
        with patch('os.path.exists', return_value=True):
            environ = run.get_environ(original, defaults, ve_path)
        assert environ is not original
        assert environ.get('foo') == 'bar'

    def test_updates_with_defaults(self):
        original = {'foo': 'bar', 'yak': 'nope'}
        defaults = {'bam': 'pow', 'yak': 'fur'}
        ve_path = 'blah'
        with patch('os.path.exists', return_value=True):
            environ = run.get_environ(original, defaults, ve_path)
        assert environ.get('bam') == 'pow'
        assert environ.get('yak') == 'fur'

    def test_ve_path(self):
        original = {'foo': 'bar'}
        defaults = {}
        ve_path = 'blah'
        with patch('os.path.exists'):
            environ = run.get_environ(original, defaults, ve_path)
        assert environ.get('VIRTUAL_ENV') == ve_path

    def test_prefixes_PATH(self):
        original = {'foo': 'bar'}
        defaults = {}
        ve_path = 'fnood'
        bin_path = os.path.join(ve_path, 'bin')
        with patch('os.path.exists', return_value=True):
            environ = run.get_environ(original, defaults, ve_path)
        PATH = environ.get('PATH', '')
        paths = PATH.split(os.pathsep)
        assert paths[0] == bin_path

    def test_removes_old_virtualenv_bin_path(self):
        new = 'new'
        old = 'old'
        original = {'foo': 'bar', 'VIRTUALENV': old}
        defaults = {}
        new_bin = os.path.join(new, 'bin')
        old_bin = os.path.join(old, 'bin')
        with patch('os.path.exists', return_value=True):
            environ = run.get_environ(original, defaults, new)
        PATH = environ.get('PATH', '')
        paths = PATH.split(os.pathsep)
        assert paths[0] == new_bin
        assert old_bin not in paths

    def test_fake_windows_env(self):
        # does not simulate different os.pathsep, etc.
        # just tests using Script instead of bin, for coverage.
        original = {'foo': 'bar'}
        defaults = {}
        ve_path = 'fnard'
        bin_path = os.path.join(ve_path, 'Scripts')
        with patch('platform.system', return_value='Windows'), \
             patch('os.path.exists', return_value=True):
            assert platform.system() == 'Windows'
            environ = run.get_environ(original, defaults, ve_path)
        assert environ.get('VIRTUAL_ENV') == ve_path
        PATH = environ.get('PATH', '')
        paths = PATH.split(os.pathsep)
        assert paths[0] == bin_path
