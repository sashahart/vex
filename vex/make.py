import os
from vex.run import run
from vex import exceptions


def handle_make(environ, options, make_path):
    if os.path.exists(make_path):
        # Can't ignore existing virtualenv happily because existing one
        # might have different parameters and --make implies nonexistent
        raise exceptions.VirtualenvAlreadyMade(make_path)
    args = ['virtualenv', make_path]
    if options.python:
        args += ['--python', options.python]
    if options.site_packages:
        args += ['--site-packages']
    if options.always_copy:
        args+= ['--always-copy']
    returncode = 1
    ve_base = os.path.dirname(make_path)
    returncode = run(args, env=environ, cwd=ve_base)
    if returncode != 0:
        raise exceptions.VirtualenvNotMade("error creating virtualenv")
