"""
This is not needed to use vex.
It just lets us provide a convenient mechanism for people
with popular shells to set up autocompletion.
"""
import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))

_SHELLS = {
}


def emit_shell_config_for(shell, vexrc, environ):
    function = _SHELLS.get(shell)
    if function:
        if hasattr(sys.stdout, 'buffer'):
            out = sys.stdout.buffer
        else:
            out = sys.stdout
        function(out, vexrc, environ)
