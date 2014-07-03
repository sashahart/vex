import os
from io import BytesIO
import argparse
from pytest import raises
from mock import patch
from vex import main
from vex.config import Vexrc
from . fakes import Object


def test_make_arg_parser():
    # just exercises code for coverage
    parser = main.make_arg_parser()
    assert parser


class TestGetOptions(object):
    def test_get_options(self):
        options = main.get_options(['--cwd', 'whatever'])
        assert options.cwd == 'whatever'

    def test_get_options_unknown(self):
        try:
            main.get_options(['--unlikely-to-be-used'])
        except main.UnknownArguments as error:
            assert "--unlikely-to-be-used" in str(error)


class TestGetVexrc(object):
    def test_get_vexrc_nonexistent(self):
        options = main.get_options(['--config', 'unlikely_to_exist'])
        try:
            main.get_vexrc(options, {})
        except main.InvalidVexrc as error:
            assert 'unlikely_to_exist' in str(error)


    def test_get_vexrc(self):
        options = main.get_options(['--config', 'pretends_to_exist'])

        def fake_open(name, mode):
            assert name == 'pretends_to_exist'
            assert mode == 'rb'
            return BytesIO(b'a=b\n')

        with patch('os.path.exists', return_value=True), \
             patch('vex.config.open', create=True, new=fake_open):
            vexrc = main.get_vexrc(options, {})
            assert vexrc


class TestGetCwd(object):

    def test_get_cwd_no_option(self):
        options = argparse.Namespace(cwd=None)
        assert main.get_cwd(options) is None

    def test_get_cwd_nonexistent(self):
        options = argparse.Namespace(cwd="unlikely_to_exist")
        with patch('os.path.exists', return_value=False):
            try:
                main.get_cwd(options)
            except main.InvalidCwd:
                pass

    def test_get_cwd(self):
        options = argparse.Namespace(cwd="foo")
        with patch('os.path.exists', return_value=True):
            cwd = main.get_cwd(options)
        assert cwd == "foo"


class TestGetVirtualenvPath(object):
    # def test_path_is_None(self):
        # options = argparse.Namespace(path=None)

    def test_path_not_given_no_virtualenvs_directory(self):
        options = argparse.Namespace(path=None)
        vexrc = Vexrc()
        environ = {'WORKON_HOME': '', 'HOME': ''}
        with patch('vex.config.Vexrc.get_ve_base', return_value=''), \
           raises(main.NoVirtualenvsDirectory):
            assert vexrc.get_ve_base(environ) == ''
            main.get_virtualenv_path(options, vexrc, environ)

    def test_path_not_given_nonexistent_virtualenvs_directory(self):
        options = argparse.Namespace(path=None)
        vexrc = Vexrc()
        environ = {'WORKON_HOME': 'very_unlikely_to_exist', 'HOME': ''}
        with raises(main.NoVirtualenvsDirectory):
            main.get_virtualenv_path(options, vexrc, environ)

    def test_path_given_in_rest(self):
        options = argparse.Namespace(path=None, rest=['moo'])
        vexrc = Vexrc()
        ve_base = '/tmp'  # urgh
        environ = {'WORKON_HOME': ve_base}
        assert vexrc.get_ve_base(environ) == ve_base
        assert os.path.exists(ve_base)
        with patch('os.path.exists', return_value=True):
            path = main.get_virtualenv_path(options, vexrc, environ)
        assert path.endswith(os.path.join('tmp', 'moo'))

    def test_path_not_given_no_rest(self):
        options = argparse.Namespace(path=None, rest=[])
        vexrc = Vexrc()
        environ = {}
        with raises(main.NoVirtualenvName):
            main.get_virtualenv_path(options, vexrc, environ)

    def test_path_given_but_nonexistent(self):
        options = argparse.Namespace(path='very_unlikely_to_exist', rest=[])
        vexrc = Vexrc()
        environ = {}
        with raises(main.InvalidVirtualenv):
            main.get_virtualenv_path(options, vexrc, environ)

    def test_path_given_and_exists(self):
        pretends_to_exist = os.sep + os.path.join('tmp', 'pretends_to_exist')
        options = argparse.Namespace(path=pretends_to_exist, rest=[])
        vexrc = Vexrc()
        environ = {}
        with patch('os.path.exists', return_value=True):
            path = main.get_virtualenv_path(options, vexrc, environ)
            assert path == pretends_to_exist

    def test_path_given_and_relative(self):
        pretends_to_exist = 'pretends_to_exist'
        options = argparse.Namespace(path=pretends_to_exist)
        vexrc = Vexrc()
        environ = {}
        with patch('os.path.exists', return_value=True):
            path = main.get_virtualenv_path(options, vexrc, environ)
            abspath = os.path.abspath(pretends_to_exist)
            assert path == abspath


class TestGetCommand(object):

    def test_shell_options(self):
        vexrc = Vexrc()
        vexrc[vexrc.default_heading]['shell'] = '/bin/dish'
        options = Object(rest=['given', 'command'])
        environ = {'SHELL': 'wrong'}
        assert main.get_command(options, vexrc, environ) == ['given', 'command']

    def test_shell_vexrc(self):
        vexrc = Vexrc()
        vexrc[vexrc.default_heading]['shell'] = '/bin/dish'
        options = Object(rest=None)
        environ = {'SHELL': 'wrong'}
        assert main.get_command(options, vexrc, environ) == ['/bin/dish']

    def test_shell_environ(self):
        vexrc = Vexrc()
        options = Object(rest=None)
        environ = {'SHELL': '/bin/dish'}
        assert main.get_command(options, vexrc, environ) == ['/bin/dish']

    def test_nothing(self):
        vexrc = Vexrc()
        options = argparse.Namespace(rest=None)
        environ = {}
        with raises(main.InvalidCommand):
            main.get_command(options, vexrc, environ)

    def test_flag(self):
        vexrc = Vexrc()
        options = argparse.Namespace(rest=['--foo'])
        environ = {}
        with raises(main.InvalidCommand):
            main.get_command(options, vexrc, environ)
