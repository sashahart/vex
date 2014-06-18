"""
This is not needed to use vex.
It just lets us provide a convenient mechanism for people
with popular shells to set up autocompletion.
"""
import os
import re

NOT_SCARY = re.compile(br'[~]?(?:[/]+[\w _,.][\w _\-,.]+)*\Z')


_HERE = os.path.dirname(os.path.abspath(__file__))

_BASH_CONFIG = b""
with open(os.path.join(_HERE, 'shell_configs', 'bash'), 'rb') as inp:
    _BASH_CONFIG = inp.read()

_ZSH_CONFIG = b""
with open(os.path.join(_HERE, 'shell_configs', 'zsh'), 'rb') as inp:
    _ZSH_CONFIG = inp.read()


_FISH_CONFIG = b""
with open(os.path.join(_HERE, 'shell_configs', 'fish'), 'rb') as inp:
    _FISH_CONFIG = inp.read()


def scary_path(path):
    """Whitelist the WORKON_HOME strings we're willing to substitute in
    to strings that we provide for user's shell to evaluate.

    If it smells at all bad, return True.
    """
    if not path:
        return True
    assert isinstance(path, bytes)
    return not NOT_SCARY.match(path)


def zsh_config(vexrc, environ):
    """return completion config for zsh.
    """
    ve_base = vexrc.get_ve_base(environ).encode('ascii')
    if ve_base and not scary_path(ve_base):
        assert os.path.exists(ve_base)
        data = _ZSH_CONFIG.replace(b'$WORKON_HOME', ve_base)
    else:
        data = _ZSH_CONFIG
    return data


def bash_config(vexrc, environ):
    """return completion config for bash.
    """
    ve_base = vexrc.get_ve_base(environ).encode('ascii')
    if ve_base and not scary_path(ve_base):
        assert os.path.exists(ve_base)
        data = _BASH_CONFIG.replace(b'$WORKON_HOME', ve_base)
    else:
        data = _BASH_CONFIG
    return data


def fish_config(vexrc, environ):
    """return completion config for fish.
    """
    ve_base = vexrc.get_ve_base(environ).encode('ascii')
    if ve_base and not scary_path(ve_base):
        assert os.path.exists(ve_base)
        data = _FISH_CONFIG.replace(b'$WORKON_HOME', ve_base)
    else:
        data = _FISH_CONFIG
    return data


_SHELLS = {
    'bash': bash_config,
    'zsh': zsh_config,
    'fish': fish_config,
}


def shell_config_for(shell, vexrc, environ):
    """return completion config for the named shell.
    """
    function = _SHELLS.get(shell)
    if function:
        return function(vexrc, environ)
    return ""
