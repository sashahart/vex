from pytest import raises
from vex.tests import fakes


class TestObject(object):
    def test_simple(self):
        obj = fakes.Object(foo="bar", baz=2)
        assert obj.foo == "bar"
        assert obj.baz == 2

    def test_private(self):
        obj = fakes.Object(foo="bar", _baz=2)
        assert obj.foo == "bar"
        with raises(AttributeError):
            obj._baz


def test_make_fake_exists():
    """Test that make_fake_exists itself works as intended.
    """
    fake_exists = fakes.make_fake_exists(['/special'])
    assert fake_exists('/special')
    assert not fake_exists('/dev')
