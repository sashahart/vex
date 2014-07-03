"""
This is not needed to use vex.
It just lets us provide a convenient mechanism for people
with popular shells to set up autocompletion.
"""
import os
import re

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError
    # (OSError, IOError)


NOT_SCARY = re.compile(br'[~]?(?:[/]+[\w _,.][\w _\-,.]+)*\Z')


def scary_path(path):
    """Whitelist the WORKON_HOME strings we're willing to substitute in
    to strings that we provide for user's shell to evaluate.

    If it smells at all bad, return True.
    """
    if not path:
        return True
    assert isinstance(path, bytes)
    return not NOT_SCARY.match(path)


def shell_config_for(shell, vexrc, environ):
    """return completion config for the named shell.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'shell_configs', shell)
    try:
        with open(path, 'rb') as inp:
            data = inp.read()
    except FileNotFoundError as error:
        if error.errno != 2:
            raise
        return b''
    ve_base = vexrc.get_ve_base(environ).encode('ascii')
    if ve_base and not scary_path(ve_base):
        assert os.path.exists(ve_base)
        data = data.replace(b'$WORKON_HOME', ve_base)
    return data
