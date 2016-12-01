"""Run subprocess.
"""
import os
import platform
import subprocess
import distutils.spawn
from vex import exceptions


def get_environ(environ, defaults, ve_path):
    """Make an environment to run with.
    """
    # Copy the parent environment, add in defaults from .vexrc.
    env = environ.copy()
    env.update(defaults)

    # Leaving in existing PYTHONHOME can cause some errors
    if 'PYTHONHOME' in env:
        del env['PYTHONHOME']

    # Now we have to adjust PATH to find scripts for the virtualenv...
    # PATH being unset/empty is OK, but ve_path must be set
    # or there is nothing for us to do here and it's bad.
    if not ve_path:
        raise exceptions.BadConfig('ve_path must be set')
    if platform.system() == 'Windows':
        ve_bin = os.path.join(ve_path, 'Scripts')
    else:
        ve_bin = os.path.join(ve_path, 'bin')

    # If user is currently in a virtualenv, DON'T just prepend
    # to its path (vex foo; echo $PATH -> " /foo/bin:/bar/bin")
    # but don't incur this cost unless we're already in one.
    # activate handles this by running 'deactivate' first, we don't
    # have that so we have to use other ways.
    # This would not be necessary and things would be simpler if vex
    # did not have to interoperate with a ubiquitous existing tool.
    # virtualenv doesn't...
    current_ve = env.get('VIRTUAL_ENV', '')
    system_path = environ.get('PATH', '')

    # On Windows the separators can get squirrelly (a mix of / and \\)
    # Just enforce that they're all normalized before we match on them
    segments = map(os.path.normpath, system_path.split(os.pathsep))

    if current_ve:
        # Since activate doesn't export _OLD_VIRTUAL_PATH, we are going to
        # manually remove the virtualenv's bin.
        # A virtualenv's bin should not normally be on PATH except
        # via activate or similar, so I'm OK with this solution.
        if platform.system() == 'Windows':
            current_ve_bin = os.path.join(os.path.normpath(current_ve),
					  'Scripts')
        else:
            current_ve_bin = os.path.join(os.path.normpath(current_ve),
					  'bin')

        try:
            segments.remove(current_ve_bin)
        except ValueError:
            raise exceptions.BadConfig(
                "something set VIRTUAL_ENV prior to this vex execution, "
                "implying that a virtualenv is already activated "
                "and PATH should contain the virtualenv's bin directory. "
                "Unfortunately, it doesn't: it's {0!r}. "
                "You might want to check that PATH is not "
                "getting clobbered somewhere, e.g. in your shell's configs."
                .format(system_path)
            )

    segments.insert(0, ve_bin)
    env['PATH'] = os.pathsep.join(segments)
    env['VIRTUAL_ENV'] = ve_path
    return env


def run(command, env, cwd):
    """Run the given command.
    """
    assert command
    if cwd:
        assert os.path.exists(cwd)
    if platform.system() == "Windows":
        exe = distutils.spawn.find_executable(command[0], path=env['PATH'])
        if exe:
            command[0] = exe
    _, command_name = os.path.split(command[0])
    if (command_name in ('bash', 'zsh')
    and 'VIRTUALENVWRAPPER_PYTHON' not in env):
        env['VIRTUALENVWRAPPER_PYTHON'] = ':'
    try:
        process = subprocess.Popen(command, env=env, cwd=cwd)
        process.wait()
    except exceptions.CommandNotFoundError as error:
        if error.errno != 2:
            raise
        return None
    return process.returncode
