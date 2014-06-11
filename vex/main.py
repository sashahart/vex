"""Main command-line entry-point and any code tightly coupled to it.
"""
import sys
import os
import argparse
from vex import config
from vex.run import get_environ, run


class Barf(Exception):
    """Raised by anything under main() to propagate errors to user.
    """
    def __init__(self, message):
        self.message = message
        Exception.__init__(self, message)


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
        help="print optional config for evaluation by the specified shell"
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
        raise Barf("unknown args: {0!r}".format(unknown))
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
        raise Barf("nonexistent config: {0!r}".format(options.config))
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
        raise OtherShell(options.shell_to_configure)
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
        raise Barf("can't --cwd to invalid path {0!r}".format(options.cwd))
    return options.cwd


def get_virtualenv_path(options, vexrc, environ):
    """Find a virtualenv path.
    """
    ve_path = options.path
    ve_name = None
    if ve_path:
        ve_name = os.path.basename(os.path.normpath(ve_path))
    else:
        ve_base = vexrc.get_ve_base(environ)
        if not ve_base:
            raise Barf(
                "could not figure out a virtualenvs directory. "
                "make sure $HOME is set, or $WORKON_HOME,"
                " or set virtualenvs=something in your .vexrc")
        if not os.path.exists(ve_base):
            raise Barf("virtualenvs directory {0!r} not found."
                        .format(ve_base))
        ve_name = options.rest.pop(0) if options.rest else ''
        if not ve_name:
            return None

        # n.b.: if ve_name is absolute, ve_base is discarded by os.path.join,
        # and an absolute path will be accepted as first arg.
        # So we check if they gave an absolute path as ve_name.
        # But we don't want this error if $PWD == $WORKON_HOME,
        # in which case 'foo' is a valid relative path to virtualenv foo.
        ve_path = os.path.join(ve_base, ve_name)
        if ve_path == ve_name and os.path.basename(ve_name) != ve_name:
            raise Barf(
                'To run in a virtualenv by its path, '
                'use "vex --path {0}"'.format(ve_path))

    if not ve_path:
        raise Barf("could not find a virtualenv name in the command line.")
    ve_path = os.path.abspath(ve_path)
    if not os.path.exists(ve_path):
        raise Barf("no virtualenv found at {0!r}.".format(ve_path))
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
        raise Barf("don't put flags like '%s' after the virtualenv name."
                    % command[0])
    if not command:
        raise Barf("no command")
    return command


def _main(environ, argv):
    """Logic for main(), with less direct system interaction.
    """
    options = get_options(argv)
    vexrc = get_vexrc(options, environ)
    if options.shell_to_configure:
        return handle_shell_config(options, vexrc, environ)
    cwd = get_cwd(options)
    ve_path = get_virtualenv_path(options, vexrc, environ)
    command = get_command(options, vexrc, environ)
    env = get_environ(environ, vexrc['env'], ve_path)
    returncode = run(command, env=env, cwd=cwd)
    if returncode is None:
        raise Barf("command not found: {0!r}".format(command[0]))
    return returncode


def main():
    """The main command-line entry point, with system interactions.
    """
    argv = sys.argv[1:]
    returncode = 1
    try:
        returncode = _main(os.environ, argv)
    except Barf as error:
        if error.message:
            sys.stderr.write("Error: " + error.message + '\n')
    sys.exit(returncode)
