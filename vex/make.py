import os
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
    args = ['virtualenv', make_path]
    if options.python:
        args += ['--python', options.python]
    if options.site_packages:
        args += ['--site-packages']
    if options.always_copy:
        args+= ['--always-copy']
    returncode = run(args, env=environ, cwd=ve_base)
    if returncode != 0:
        raise exceptions.VirtualenvNotMade("error creating virtualenv")
