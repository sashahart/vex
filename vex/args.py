"""Command-line argument processing.
"""
import os
import argparse
import textwrap


def make_arg_parser():
    """Return a standard ArgumentParser object.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        usage="vex [OPTIONS] VIRTUALENV_NAME COMMAND_TO_RUN ...",
        description=textwrap.dedent("""
            Examples:
                vex foo ls -l
                (runs 'ls -l' in virtualenv 'foo' found e.g. in ~/.virtualenvs)

                vex foo pip install ipython
                (installs ipython in virtualenv 'foo')

                vex --path env pip freeze
                (shows what's installed in virtualenv placed at ./env)
        """)
    )

    make = parser.add_argument_group(title='To make a virtualenv')
    make.add_argument(
        '-m', '--make',
        action="store_true",
        help="make the named virtualenv before running command"
    )
    make.add_argument(
        '--python',
        help="specify python executable for the new virtualenv",
        action="store",
        default="python",
    )
    make.add_argument(
        '--site-packages',
        help="let the new virtualenv use site packages",
        action="store_true",
    )
    remove = parser.add_argument_group(title='To remove a virtualenv')
    remove.add_argument(
        '-r', '--remove',
        action="store_true",
        help="remove the named virtualenv after running command"
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--virtualenv",
        nargs="?",
        help=argparse.SUPPRESS  # "name of virtualenv to run in"
    )
    group.add_argument(
        "--path",
        help="absolute path to virtualenv to use",
        action="store"
    )
    parser.add_argument(
        '--cwd',
        action="store",
        default='.',
        help="path to run command in (default: '.' aka $PWD)",
    )
    parser.add_argument(
        "--config",
        default=os.path.expanduser('~/.vexrc'),
        action="store",
        help="path to config file to read (default: '~/.vexrc')"
    )
    parser.add_argument(
        "rest",
        nargs=argparse.REMAINDER,
        help=argparse.SUPPRESS)

    return parser
