import argparse
from vex import exceptions


def make_arg_parser():
    """Return a standard ArgumentParser object.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        usage="vex [OPTIONS] VIRTUALENV_NAME COMMAND_TO_RUN ...",
    )

    make = parser.add_argument_group(title='To make a new virtualenv')
    make.add_argument(
        '-m', '--make',
        action="store_true",
        help="make named virtualenv before running command"
    )
    make.add_argument(
        '--python',
        help="specify which python for virtualenv to be made",
        action="store",
        default=None,
    )
    make.add_argument(
        '--site-packages',
        help="allow site package imports from new virtualenv",
        action="store_true",
    )
    make.add_argument(
        '--always-copy',
        help="use copies instead of symlinks in new virtualenv",
        action="store_true",
    )

    remove = parser.add_argument_group(title='To remove a virtualenv')
    remove.add_argument(
        '-r', '--remove',
        action="store_true",
        help="remove the named virtualenv after running command"
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
        '--list',
        metavar="PREFIX",
        nargs="?",
        const="",
        default=None,
        help="print a list of available virtualenvs [matching PREFIX]",
        action="store"
    )
    parser.add_argument(
        '--version',
        help="print the version of vex that is being run",
        action="store_true"
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
