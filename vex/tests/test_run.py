from __future__ import unicode_literals
import os
import os.path
import subprocess
from vex import run
from . fakes import FakeEnviron, PatchedModule, FakePopen, Object


def test_make_env():
    options = Object(path='thing')
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
        result = run.make_env(passed_environ, defaults, options)
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
    # and VIRTUAL_ENV is options.path
    assert result['VIRTUAL_ENV'] == options.path


def test_run():
    # mock subprocess.Popen because we are cowards
    with PatchedModule(subprocess, Popen=FakePopen(returncode=888)) as mod:
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
