import os
import sys
from vex.run import run
from vex import exceptions


def handle_make(environ, options, make_path):
    if os.path.exists(make_path):
        # Can't ignore existing virtualenv happily because existing one
        # might have different parameters and --make implies nonexistent
        raise exceptions.VirtualenvAlreadyMade(make_path)
    ve_base = os.path.dirname(make_path)
    if not os.path.exists(ve_base):
        os.mkdir(ve_base)
    elif not os.path.isdir(ve_base):
        raise exceptions.VirtualenvNotMade(
            "could not make virtualenv: "
            "{0!r} already exists but is not a directory. "
            "Choose a different virtualenvs path using ~/.vexrc "
            "or $WORKON_HOME, or remove the existing file; "
            "then rerun your vex --make command.".format(ve_base)
        )
    # TODO: virtualenv is usually not on PATH for Windows,
    # but finding it is a terrible issue.
    if os.name == 'nt' and not os.environ.get('VIRTUAL_ENV', ''):
        ve = os.path.join(
            os.path.dirname(sys.executable),
            'Scripts',
            'virtualenv'
        )
    else:
        ve = 'virtualenv'
    args = [ve, make_path]
    if options.python:
        args += ['--python', options.python]
    if options.site_packages:
        args += ['--site-packages']
    if options.always_copy:
        args+= ['--always-copy']
    returncode = run(args, env=environ, cwd=ve_base)
    if returncode != 0:
        raise exceptions.VirtualenvNotMade("error creating virtualenv")
