"""Main command-line entry-point and any code tightly coupled to it.
"""
import sys
import os
import argparse
from vex import config
from vex.run import get_environ, run


class InvalidArgument(Exception):
    """Raised by anything under main() to propagate errors to user.
    """
    def __init__(self, message):
        self.message = message
        Exception.__init__(self, message)


class NoVirtualenvName(InvalidArgument):
    """No virtualenv name was given (insufficient arguments).
    """
    pass


class NoVirtualenvsDirectory(InvalidArgument):
    """There is no directory to find named virtualenvs in.
    """
    pass


class OtherShell(InvalidArgument):
    """The given argument to --shell-config is not recognized.
    """
    pass


class UnknownArguments(InvalidArgument):
    """Unknown arguments were given on the command line.

    This is a byproduct of having to use parse_known_args.
    """
    pass


class InvalidVexrc(InvalidArgument):
    """config file specified or required but absent or unparseable.
    """
    pass


class InvalidVirtualenv(InvalidArgument):
    """No usable virtualenv was found.
    """
    pass


class InvalidCommand(InvalidArgument):
    """No runnable command was found.
    """
    pass


class InvalidCwd(InvalidArgument):
    """cwd specified or required but unusable.
    """
    pass


def make_arg_parser():
    """Return a standard ArgumentParser object.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        usage="vex [OPTIONS] VIRTUALENV_NAME COMMAND_TO_RUN ...",
    )

    parser.add_argument(
        "--path",
        metavar="DIR",
        help="absolute path to virtualenv to use",
        action="store"
    )
    parser.add_argument(
        '--cwd',
        metavar="DIR",
        action="store",
        default='.',
        help="path to run command in (default: '.' aka $PWD)",
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        default=None,
        action="store",
        help="path to config file to read (default: '~/.vexrc')"
    )
    parser.add_argument(
        '--shell-config',
        metavar="SHELL",
        dest="shell_to_configure",
        action="store",
        default=None,
        help="print optional config for the specified shell"
    )
    parser.add_argument(
        "rest",
        nargs=argparse.REMAINDER,
        help=argparse.SUPPRESS)

    return parser


def get_options(argv):
    """Called to parse the given list as command-line arguments.

    :returns:
        an options object as returned by argparse.
    """
    arg_parser = make_arg_parser()
    options, unknown = arg_parser.parse_known_args(argv)
    if unknown:
        arg_parser.print_help()
        raise UnknownArguments("unknown args: {0!r}".format(unknown))
    options.print_help = arg_parser.print_help
    return options


def get_vexrc(options, environ):
    """Get a representation of the contents of the config file.

    :returns:
            a Vexrc instance.
    """
    # Complain if user specified nonexistent file with --config.
    # But we don't want to complain just because ~/.vexrc doesn't exist.
    if options.config and not os.path.exists(options.config):
        raise InvalidVexrc("nonexistent config: {0!r}".format(options.config))
    filename = options.config or os.path.expanduser('~/.vexrc')
    vexrc = config.Vexrc.from_file(filename, environ)
    return vexrc


def handle_shell_config(options, vexrc, environ):
    """Carry out the logic of the --shell-config option.
    """
    from vex import shell_config
    data = shell_config.shell_config_for(
        options.shell_to_configure, vexrc, environ)
    if not data:
        raise OtherShell("unknown shell: " + options.shell_to_configure)
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout.buffer.write(data)
    else:
        sys.stdout.write(data)
    return 0


def get_cwd(options):
    """Discover what directory the command should run in.
    """
    if not options.cwd:
        return None
    if not os.path.exists(options.cwd):
        raise InvalidCwd(
            "can't --cwd to invalid path {0!r}".format(options.cwd))
    return options.cwd


def get_virtualenv_path(options, vexrc, environ):
    """Find a virtualenv path.
    """
    if options.path:
        ve_path = options.path
    else:
        ve_base = vexrc.get_ve_base(environ)
        if not ve_base:
            raise NoVirtualenvsDirectory(
                "could not figure out a virtualenvs directory. "
                "make sure $HOME is set, or $WORKON_HOME,"
                " or set virtualenvs=something in your .vexrc")
        # Using this requires get_ve_base to pass through nonexistent dirs
        if not os.path.exists(ve_base):
            raise NoVirtualenvsDirectory(
                "virtualenvs directory {0!r} not found.".format(ve_base))
        ve_name = options.rest.pop(0) if options.rest else ''
        if not ve_name:
            raise NoVirtualenvName(
                "could not find a virtualenv name in the command line."
            )

        # n.b.: if ve_name is absolute, ve_base is discarded by os.path.join,
        # and an absolute path will be accepted as first arg.
        # So we check if they gave an absolute path as ve_name.
        # But we don't want this error if $PWD == $WORKON_HOME,
        # in which case 'foo' is a valid relative path to virtualenv foo.
        ve_path = os.path.join(ve_base, ve_name)
        if ve_path == ve_name and os.path.basename(ve_name) != ve_name:
            raise InvalidVirtualenv(
                'To run in a virtualenv by its path, '
                'use "vex --path {0}"'.format(ve_path))

    ve_path = os.path.abspath(ve_path)
    if not os.path.exists(ve_path):
        raise InvalidVirtualenv("no virtualenv found at {0!r}.".format(ve_path))
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
        raise InvalidCommand(
            "don't put flags like '%s' after the virtualenv name."
            % command[0])
    if not command:
        raise InvalidCommand("no command given")
    return command


def _main(environ, argv):
    """Logic for main(), with less direct system interaction.
    """
    options = get_options(argv)
    vexrc = get_vexrc(options, environ)
    if options.shell_to_configure:
        return handle_shell_config(options, vexrc, environ)
    cwd = get_cwd(options)
    try:
        ve_path = get_virtualenv_path(options, vexrc, environ)
    except NoVirtualenvName:
        options.print_help()
        raise
    command = get_command(options, vexrc, environ)
    env = get_environ(environ, vexrc['env'], ve_path)
    returncode = run(command, env=env, cwd=cwd)
    if returncode is None:
        raise InvalidCommand("command not found: {0!r}".format(command[0]))
    return returncode


def main():
    """The main command-line entry point, with system interactions.
    """
    argv = sys.argv[1:]
    returncode = 1
    try:
        returncode = _main(os.environ, argv)
    except NoVirtualenvName:
        sys.stderr.write("\n")
        sys.stderr.write("Error: no virtualenv name found in command line.\n")
    except InvalidArgument as error:
        if error.message:
            sys.stderr.write("Error: " + error.message + '\n')
    sys.exit(returncode)
