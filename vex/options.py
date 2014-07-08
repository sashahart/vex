import argparse
from vex import exceptions


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
        raise exceptions.UnknownArguments(
            "unknown args: {0!r}".format(unknown))
    options.print_help = arg_parser.print_help
    return options
