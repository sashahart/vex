import os
from io import BytesIO
import argparse
from pytest import raises
from mock import patch
from vex import main
from vex.config import Vexrc
from vex import exceptions
from . fakes import Object, make_fake_exists


class TestGetVexrc(object):
    def test_get_vexrc_nonexistent(self):
        options = main.get_options(['--config', 'unlikely_to_exist'])
        try:
            main.get_vexrc(options, {})
        except exceptions.InvalidVexrc as error:
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
            except exceptions.InvalidCwd:
                pass

    def test_get_cwd(self):
        options = argparse.Namespace(cwd="foo")
        with patch('os.path.exists', return_value=True):
            cwd = main.get_cwd(options)
        assert cwd == "foo"


class TestGetVirtualenvPath(object):

    def test_no_ve_base(self):
        with raises(exceptions.NoVirtualenvsDirectory):
            main.get_virtualenv_path("", "anything")

    def test_nonexistent_ve_base(self):
        with raises(exceptions.NoVirtualenvsDirectory):
            main.get_virtualenv_path("/unlikely_to_exist1", "anything")

    def test_no_ve_name(self):
        fake_path = os.path.abspath(os.path.join('pretends_to_exist'))
        fake_exists = make_fake_exists([fake_path])
        with patch('os.path.exists', wraps=fake_exists), \
          raises(exceptions.InvalidVirtualenv):
            main.get_virtualenv_path(fake_path, "")

    def test_nonexistent_ve_path(self):
        fake_path = os.path.abspath(os.path.join('pretends_to_exist'))
        fake_exists = make_fake_exists([fake_path])
        with patch('os.path.exists', wraps=fake_exists), \
          raises(exceptions.InvalidVirtualenv):
            main.get_virtualenv_path(fake_path, "/unlikely_to_exist2")

    def test_happy(self):
        fake_base = os.path.abspath(os.path.join('pretends_to_exist'))
        fake_name = 'also_pretend'
        fake_path = os.path.join(fake_base, fake_name)
        fake_exists = make_fake_exists([fake_base, fake_path])
        with patch('os.path.exists', wraps=fake_exists):
            path = main.get_virtualenv_path(fake_base, fake_name)
            assert path == fake_path


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
        with raises(exceptions.InvalidCommand):
            main.get_command(options, vexrc, environ)

    def test_flag(self):
        vexrc = Vexrc()
        options = argparse.Namespace(rest=['--foo'])
        environ = {}
        with raises(exceptions.InvalidCommand):
            main.get_command(options, vexrc, environ)
