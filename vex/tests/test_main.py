from vex.main import main, get_command
from vex.config import Vexrc
from . fakes import Object


def test_main():
    assert main  # I have no idea how to test this right now


def test_get_command_shell_options():
    vexrc = Vexrc()
    vexrc[vexrc.default_heading]['shell'] = '/bin/dish'
    options = Object(rest=['given', 'command'])
    environ = {'SHELL': 'wrong'}
    assert get_command(options, vexrc, environ) == ['given', 'command']


def test_get_command_shell_vexrc():
    vexrc = Vexrc()
    vexrc[vexrc.default_heading]['shell'] = '/bin/dish'
    options = Object(rest=None)
    environ = {'SHELL': 'wrong'}
    assert get_command(options, vexrc, environ) == ['/bin/dish']


def test_get_command_shell_environ():
    vexrc = Vexrc()
    options = Object(rest=None)
    environ = {'SHELL': '/bin/dish'}
    assert get_command(options, vexrc, environ) == ['/bin/dish']


def test_get_command_nothing():
    vexrc = Vexrc()
    options = Object(rest=None)
    environ = {}
    assert get_command(options, vexrc, environ) is None
