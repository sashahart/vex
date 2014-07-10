import sys


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


class BadConfig(InvalidArgument):
    """raised to halt on fatal conditions on the way to run.
    """
    pass


class VirtualenvAlreadyMade(InvalidArgument):
    """could not make virtualenv as one already existed.
    """
    pass


class VirtualenvNotMade(InvalidArgument):
    """could not make virtualenv.
    """
    pass


class VirtualenvNotRemoved(InvalidArgument):
    """raised when virtualenv could not be removed.
    """
    pass


if sys.version_info > (3, 3):
    CommandNotFoundError = FileNotFoundError
else:
    CommandNotFoundError = OSError
