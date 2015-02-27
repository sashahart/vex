"""Main command-line entry-point and any code tightly coupled to it.
"""
import sys
import os
from vex import config
from vex.options import get_options
from vex.run import get_environ, run
from vex.shell_config import handle_shell_config
from vex.make import handle_make
from vex.remove import handle_remove
from vex import exceptions
from vex._version import VERSION


def get_vexrc(options, environ):
    """Get a representation of the contents of the config file.

    :returns:
        a Vexrc instance.
    """
    # Complain if user specified nonexistent file with --config.
    # But we don't want to complain just because ~/.vexrc doesn't exist.
    if options.config and not os.path.exists(options.config):
        raise exceptions.InvalidVexrc("nonexistent config: {0!r}".format(options.config))
    filename = options.config or os.path.expanduser('~/.vexrc')
    vexrc = config.Vexrc.from_file(filename, environ)
    return vexrc


def get_cwd(options):
    """Discover what directory the command should run in.
    """
    if not options.cwd:
        return None
    if not os.path.exists(options.cwd):
        raise exceptions.InvalidCwd(
            "can't --cwd to invalid path {0!r}".format(options.cwd))
    return options.cwd


def get_virtualenv_name(options):
    if options.path:
        return os.path.dirname(options.path)
    else:
        ve_name = options.rest.pop(0) if options.rest else ''
    if not ve_name:
        raise exceptions.NoVirtualenvName(
            "could not find a virtualenv name in the command line."
        )
    return ve_name


def get_virtualenv_path(ve_base, ve_name):
    """Check a virtualenv path, raising exceptions to explain problems.
    """
    if not ve_base:
        raise exceptions.NoVirtualenvsDirectory(
            "could not figure out a virtualenvs directory. "
            "make sure $HOME is set, or $WORKON_HOME,"
            " or set virtualenvs=something in your .vexrc")

    # Using this requires get_ve_base to pass through nonexistent dirs
    if not os.path.exists(ve_base):
        message = (
            "virtualenvs directory {0!r} not found. "
            "Create it or use vex --make to get started."
        ).format(ve_base)
        raise exceptions.NoVirtualenvsDirectory(message)

    if not ve_name:
        raise exceptions.InvalidVirtualenv("no virtualenv name")

    # n.b.: if ve_name is absolute, ve_base is discarded by os.path.join,
    # and an absolute path will be accepted as first arg.
    # So we check if they gave an absolute path as ve_name.
    # But we don't want this error if $PWD == $WORKON_HOME,
    # in which case 'foo' is a valid relative path to virtualenv foo.
    ve_path = os.path.join(ve_base, ve_name)
    if ve_path == ve_name and os.path.basename(ve_name) != ve_name:
        raise exceptions.InvalidVirtualenv(
            'To run in a virtualenv by its path, '
            'use "vex --path {0}"'.format(ve_path))

    ve_path = os.path.abspath(ve_path)
    if not os.path.exists(ve_path):
        raise exceptions.InvalidVirtualenv(
            "no virtualenv found at {0!r}.".format(ve_path))
    return ve_path


def get_command(options, vexrc, environ):
    """Get a command to run.

    :returns:
        a list of strings representing a command to be passed to Popen.
    """
    command = options.rest
    if not command:
        command = vexrc.get_shell(environ)
    if command and command[0].startswith('--'):
        raise exceptions.InvalidCommand(
            "don't put flags like '%s' after the virtualenv name."
            % command[0])
    if not command:
        raise exceptions.InvalidCommand("no command given")
    return command


def handle_version():
    sys.stdout.write(VERSION + "\n")
    return 0


def handle_list(ve_base, prefix=""):
    if not os.path.isdir(ve_base):
        sys.stderr.write("no virtualenvs directory at {0!r}\n".format(ve_base))
        return 1
    text = "\n".join(
        sorted(
            relative_path for relative_path in os.listdir(ve_base)
            if (not relative_path.startswith("-"))
            and relative_path.startswith(prefix)
            and os.path.isdir(os.path.join(ve_base, relative_path))
        )
    )
    sys.stdout.write(text + "\n")
    return 0


def _main(environ, argv):
    """Logic for main(), with less direct system interaction.

    Routines called here raise InvalidArgument with messages that
    should be delivered on stderr, to be caught by main.
    """
    options = get_options(argv)
    if options.version:
        return handle_version()
    vexrc = get_vexrc(options, environ)
    # Handle --shell-config as soon as its arguments are available.
    if options.shell_to_configure:
        return handle_shell_config(options.shell_to_configure, vexrc, environ)
    if options.list is not None:
        return handle_list(vexrc.get_ve_base(environ), options.list)

    # Do as much as possible before a possible make, so errors can raise
    # without leaving behind an unused virtualenv.
    # get_virtualenv_name is destructive and must happen before get_command
    cwd = get_cwd(options)
    ve_base = vexrc.get_ve_base(environ)
    ve_name = get_virtualenv_name(options)
    command = get_command(options, vexrc, environ)
    # Either we create ve_path, get it from options.path or find it
    # in ve_base.
    if options.make:
        if options.path:
            make_path = os.path.abspath(options.path)
        else:
            make_path = os.path.abspath(os.path.join(ve_base, ve_name))
        handle_make(environ, options, make_path)
        ve_path = make_path
    elif options.path:
        ve_path = os.path.abspath(options.path)
        if not os.path.exists(ve_path) or not os.path.isdir(ve_path):
            raise exceptions.InvalidVirtualenv(
                "argument for --path is not a directory")
    else:
        try:
            ve_path = get_virtualenv_path(ve_base, ve_name)
        except exceptions.NoVirtualenvName:
            options.print_help()
            raise
    # get_environ has to wait until ve_path is defined, which might
    # be after a make; of course we can't run until we have env.
    env = get_environ(environ, vexrc['env'], ve_path)
    returncode = run(command, env=env, cwd=cwd)
    if options.remove:
        handle_remove(ve_path)
    if returncode is None:
        raise exceptions.InvalidCommand(
            "command not found: {0!r}".format(command[0]))
    return returncode


def main():
    """The main command-line entry point, with system interactions.
    """
    argv = sys.argv[1:]
    returncode = 1
    try:
        returncode = _main(os.environ, argv)
    except exceptions.InvalidArgument as error:
        if error.message:
            sys.stderr.write("Error: " + error.message + '\n')
        else:
            raise
    sys.exit(returncode)
