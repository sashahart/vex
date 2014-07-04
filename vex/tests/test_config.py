import os
from io import BytesIO
from mock import patch
from pytest import raises
from vex import config
from . fakes import FakeEnviron, PatchedModule


TYPICAL_VEXRC = """
shell=bash

env:
    ANSWER=42

arbitrary:
    x=y
""".lstrip().encode('utf-8')

EXPAND_VEXRC = """
a="{SHELL}"
b='{SHELL}'
""".lstrip().encode('utf-8')


def make_fake_exists(accepted_paths):
    """Make functions which only return true for a particular string.
    """
    # Easy mistake to make, don't want to handle multiple signatures
    assert not isinstance(accepted_paths, str)

    def fake_exists(path):
        if path in accepted_paths:
            return True
        return False

    return fake_exists


def test_make_fake_exists():
    """Test that make_fake_exists itself works as intended.
    """
    fake_exists = make_fake_exists(['/special'])
    assert fake_exists('/special')
    assert not fake_exists('/dev')


class TestExtractHeading(object):
    """Make sure extract_heading works as intended.
    """
    def test_normal(self):
        assert config.extract_heading("foo:") == "foo"

    def test_trailing_space(self):
        assert config.extract_heading("foo: ") == "foo"

    def test_trailing_nonspace(self):
        assert config.extract_heading("foo: a") is None

    def test_no_colon(self):
        assert config.extract_heading("foo") is None


class TestExtractKeyValue(object):
    def test_normal(self):
        assert config.extract_key_value("foo=bar", {}) == ("foo", "bar")

    def test_no_equals(self):
        assert config.extract_key_value("foo", {}) is None


class TestParseVexrc(object):
    def test_error(self):
        stream = BytesIO(b'foo\n')
        stream.name = 'fred'
        it = config.parse_vexrc(stream, {})
        try:
            next(it)
        except config.InvalidConfigError as error:
            rendered = str(error)
        assert rendered == "errors in 'fred', lines [0]"

    def test_close(self):
        stream = BytesIO(b'a=b\nc=d\n')
        it = config.parse_vexrc(stream, {})
        next(it)
        it.close()


class TestVexrc(object):

    def test_read_nonexistent(self):
        vexrc = config.Vexrc()
        vexrc.read('unlikely_to_exist_1293', {})

    def test_read_empty(self):
        with patch('vex.config.open', create=True) as mock_open:
            mock_open.return_value = BytesIO(b'')
            vexrc = config.Vexrc.from_file('stuff', {})
            assert vexrc['food'] is None

    def test_read_typical(self):
        with patch('vex.config.open', create=True) as mock_open:
            mock_open.return_value = BytesIO(TYPICAL_VEXRC)
            vexrc = config.Vexrc.from_file('stuff', {})
            assert list(vexrc['root'].items()) == [('shell', 'bash')]
            assert list(vexrc['env'].items()) == [('ANSWER', '42')]
            assert list(vexrc['arbitrary'].items()) == [('x', 'y')]

    def test_read_expand(self):
        environ = {'SHELL': 'smash'}
        with patch('vex.config.open', create=True) as mock_open:
            mock_open.return_value = BytesIO(EXPAND_VEXRC)
            vexrc = config.Vexrc.from_file('stuff', environ)
            assert vexrc['root'] == {
                'a': 'smash',
                'b': '{SHELL}',
            }

    def test_get_ve_base_in_vexrc_file(self):
        vexrc = config.Vexrc()
        root = vexrc.headings[vexrc.default_heading]

        fake_exists = make_fake_exists(['/specific/override'])
        root['virtualenvs'] = '/specific/override'
        with FakeEnviron(WORKON_HOME='tempting', HOME='nonsense'), \
                PatchedModule(os.path, exists=fake_exists):
            environ = {'WORKON_HOME': '/bad1', 'HOME': '/bad2'}
            assert vexrc.get_ve_base(environ) == '/specific/override'

    def test_get_ve_base_not_in_vexrc_file_rather_workon_home(self):
        vexrc = config.Vexrc()
        root = vexrc.headings[vexrc.default_heading]
        assert 'virtualenvs' not in root

        fake_exists = make_fake_exists(['/workon/home'])
        with FakeEnviron(WORKON_HOME='tempting', HOME='nonsense'), \
                PatchedModule(os.path, exists=fake_exists):
            environ = {'WORKON_HOME': '/workon/home', 'HOME': '/bad'}
            assert vexrc.get_ve_base(environ) == '/workon/home'

    def test_get_ve_base_not_in_vexrc_file_rather_home(self):
        vexrc = config.Vexrc()
        root = vexrc.headings[vexrc.default_heading]
        assert 'virtualenvs' not in root

        fake_exists = make_fake_exists(['/home/user', '/home/user/.virtualenvs'])
        with FakeEnviron(WORKON_HOME='tempting', HOME='nonsense'), \
                PatchedModule(os.path, exists=fake_exists):
            environ = {'HOME': '/home/user'}
            assert vexrc.get_ve_base(environ) == '/home/user/.virtualenvs'

    def test_get_ve_base_not_in_vexrc_no_keys(self):
        vexrc = config.Vexrc()
        root = vexrc.headings[vexrc.default_heading]
        assert 'virtualenvs' not in root
        with FakeEnviron(WORKON_HOME='tempting', HOME='nonsense'), \
                PatchedModule(os.path, expanduser=lambda p: ''):
            environ = {}
            assert vexrc.get_ve_base(environ) == ''

    def test_get_ve_base_not_in_vexrc_no_values(self):
        vexrc = config.Vexrc()
        root = vexrc.headings[vexrc.default_heading]
        assert 'virtualenvs' not in root
        with FakeEnviron(WORKON_HOME='tempting', HOME='nonsense'), \
        PatchedModule(os.path, expanduser=lambda p: ''):
            environ = {'WORKON_HOME': '', 'HOME': ''}
            assert vexrc.get_ve_base(environ) == ''

    def test_ve_base_fake_windows(self):
        vexrc = config.Vexrc()
        environ = {'HOMEDRIVE': 'C:', 'HOMEPATH': 'foo', 'WORKON_HOME': ''}
        with patch('platform.system', return_value='Windows'), \
             patch('os.name', new='nt'), \
             patch('os.path.exists', return_value=True), \
            patch('os.path.isfile', return_value=False):
            path = vexrc.get_ve_base(environ)
            import platform
            assert platform.system() == 'Windows'
            assert os.name == 'nt'
            import logging
            logging.error("path is %r", path)
            assert path
            assert path.startswith('C:')
