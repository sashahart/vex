import os
from io import BytesIO
from mock import patch
from vex import config
from . fakes import FakeEnviron, PatchedModule


TYPICAL_VEXRC = """
shell=bash
env:
    ANSWER=42
""".lstrip().encode('utf-8')

EXPAND_VEXRC = """
a="{SHELL}"
b='{SHELL}'
""".lstrip().encode('utf-8')


def test_extract_heading():
    fn = config.extract_heading
    assert fn("foo:") == "foo"
    assert fn("foo: ") == "foo"
    assert fn("foo: a") is None
    assert fn("foo") is None


def test_read_vexrc_empty():
    with patch('vex.config.open', create=True) as mock_open:
        mock_open.return_value = BytesIO(b'')
        vexrc = config.Vexrc.from_file('stuff', {})
        assert vexrc['food'] is None


def test_read_vexrc_typical():
    with patch('vex.config.open', create=True) as mock_open:
        mock_open.return_value = BytesIO(TYPICAL_VEXRC)
        vexrc = config.Vexrc.from_file('stuff', {})
        assert list(vexrc['root'].items()) == [('shell', 'bash')]
        assert list(vexrc['env'].items()) == [('ANSWER', '42')]


def test_read_vexrc_expand():
    environ = {'SHELL': 'smash'}
    with patch('vex.config.open', create=True) as mock_open:
        mock_open.return_value = BytesIO(EXPAND_VEXRC)
        vexrc = config.Vexrc.from_file('stuff', environ)
        assert vexrc['root'] == {
            'a': 'smash',
            'b': '{SHELL}',
        }


def test_get_ve_base_in_vexrc():
    vexrc = config.Vexrc()
    root = vexrc.headings[vexrc.default_heading]

    def fake_exists(path):
        if path == '/specific/override':
            return True
        return False

    root['virtualenvs'] = '/specific/override'
    with FakeEnviron(WORKON_HOME='tempting', HOME='nonsense'), \
            PatchedModule(os.path, exists=fake_exists):
        environ = {'WORKON_HOME': '/bad1', 'HOME': '/bad2'}
        assert vexrc.get_ve_base(environ) == '/specific/override'


def test_get_ve_base_not_in_vexrc_workon_home():
    vexrc = config.Vexrc()
    root = vexrc.headings[vexrc.default_heading]
    assert 'virtualenvs' not in root

    def fake_exists(path):
        if path == '/workon/home':
            return True
        return False

    with FakeEnviron(WORKON_HOME='tempting', HOME='nonsense'), \
            PatchedModule(os.path, exists=fake_exists):
        environ = {'WORKON_HOME': '/workon/home', 'HOME': '/bad'}
        assert vexrc.get_ve_base(environ) == '/workon/home'


def test_get_ve_base_not_in_vexrc_home():
    vexrc = config.Vexrc()
    root = vexrc.headings[vexrc.default_heading]
    assert 'virtualenvs' not in root

    def fake_exists(path):
        if path in ('/home/user', '/home/user/.virtualenvs'):
            return True
        return False

    with FakeEnviron(WORKON_HOME='tempting', HOME='nonsense'), \
            PatchedModule(os.path, exists=fake_exists):
        environ = {'HOME': '/home/user'}
        assert vexrc.get_ve_base(environ) == '/home/user/.virtualenvs'


def test_get_ve_base_not_in_vexrc_no_keys():
    vexrc = config.Vexrc()
    root = vexrc.headings[vexrc.default_heading]
    assert 'virtualenvs' not in root
    with FakeEnviron(WORKON_HOME='tempting', HOME='nonsense'), \
            PatchedModule(os.path, expanduser=lambda p: ''):
        environ = {}
        assert vexrc.get_ve_base(environ) == ''


def test_get_ve_base_not_in_vexrc_no_values():
    vexrc = config.Vexrc()
    root = vexrc.headings[vexrc.default_heading]
    assert 'virtualenvs' not in root
    with FakeEnviron(WORKON_HOME='tempting', HOME='nonsense'), \
    PatchedModule(os.path, expanduser=lambda p: ''):
        environ = {'WORKON_HOME': '', 'HOME': ''}
        assert vexrc.get_ve_base(environ) == ''
