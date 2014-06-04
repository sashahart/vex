"""Run subprocess.
"""
import os
import sys
import subprocess

if sys.version_info < (3, 0):
    FileNotFoundError = OSError


class BadConfigError(Exception):
    pass


def error(message):
    raise BadConfigError(message)


def make_env(environ, defaults, options):
    """Make an environment to run with.
    """
    # Copy the parent environment, add in defaults from .vexrc.
    env = os.environ.copy()
    env.update(defaults)

    # Leaving in existing PYTHONHOME can cause some errors
    if 'PYTHONHOME' in env:
        del env['PYTHONHOME']

    # Now we have to adjust PATH to find scripts for the virtualenv...
    # PATH being unset/empty is OK, but options.path must be set
    # or there is nothing for us to do here and it's bad.
    path = environ.get('PATH', '')
    if not options.path:
        error('options.path must be set')
        return None
    ve_bin = os.path.join(options.path, 'bin')
    if not ve_bin:
        error('ve_bin must be set')
        return None

    # I don't expect this to fail, but I'd rather be slightly paranoid and fail
    # early before putting a nonexistent path on PATH.
    if not os.path.exists(ve_bin):
        error('ve_bin %r does not exist' % ve_bin)
        return None

    # If user is currently in a virtualenv, DON'T just prepend
    # to its path (vex foo; echo $PATH -> " /foo/bin:/bar/bin")
    # but don't incur this cost unless we're already in one.
    # activate handles this by running 'deactivate' first, we don't
    # have that so we have to use other ways.
    # This would not be necessary and things would be simpler if vex
    # did not have to interoperate with a ubiquitous existing tool.
    # virtualenv doesn't...
    current_ve = env.get('VIRTUAL_ENV')
    if current_ve:
        # Since activate doesn't export _OLD_VIRTUAL_PATH, we are going to
        # manually remove the virtualenv's bin.
        # A virtualenv's bin should not normally be on PATH except
        # via activate or similar, so I'm OK with this solution.
        current_ve_bin = os.path.join(current_ve, 'bin')
        segments = path.split(os.pathsep)
        segments.remove(current_ve_bin)
        path = os.pathsep.join(segments)

    env['PATH'] = os.pathsep.join([ve_bin, path])
    env['VIRTUAL_ENV'] = options.path
    return env


def run(command, env, cwd):
    """Run the given command.
    """
    try:
        process = subprocess.Popen(command, env=env, cwd=cwd)
        process.wait()
    except FileNotFoundError:
        return None
    return process.returncode
