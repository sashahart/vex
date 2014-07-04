"""Config file processing (.vexrc).
"""
import os
import sys
import re
import shlex
import platform
from collections import OrderedDict

_IDENTIFIER_PATTERN = '[a-zA-Z][_a-zA-Z0-9]*'
_SQUOTE_RE = re.compile(r"'([^']*)'\Z")  # NO squotes inside
_DQUOTE_RE = re.compile(r'"([^"]*)"\Z')  # NO dquotes inside
_HEADING_RE = re.compile(
    r'^(' + _IDENTIFIER_PATTERN + r'):[ \t\n\r]*\Z')
_VAR_RE = re.compile(
    r'[ \t]*(' + _IDENTIFIER_PATTERN + r') *= *(.*)[ \t\n\r]*$')


if sys.version_info < (3, 3):
    FileNotFoundError = IOError


class InvalidConfigError(Exception):
    """Raised when there is an error during a .vexrc file parse.
    """
    def __init__(self, filename, errors):
        Exception.__init__(self)
        self.filename = filename
        self.errors = errors

    def __str__(self):
        return "errors in {0!r}, lines {1!r}".format(
            self.filename,
            list(tup[0] for tup in self.errors)
        )


class Vexrc(object):
    """Parsed representation of a .vexrc config file.
    """
    default_heading = "root"
    default_encoding = "utf-8"

    def __init__(self):
        self.encoding = self.default_encoding
        self.headings = OrderedDict()
        self.headings[self.default_heading] = OrderedDict()
        self.headings['env'] = OrderedDict()

    def __getitem__(self, key):
        return self.headings.get(key)

    @classmethod
    def from_file(cls, path, environ):
        """Make a Vexrc instance from given file in given environ.
        """
        instance = cls()
        instance.read(path, environ)
        return instance

    def read(self, path, environ):
        """Read data from file into this vexrc instance.
        """
        try:
            inp = open(path, 'rb')
        except FileNotFoundError as error:
            if error.errno != 2:
                raise
            return None
        parsing = parse_vexrc(inp, environ)
        for heading, key, value in parsing:
            heading = self.default_heading if heading is None else heading
            if heading not in self.headings:
                self.headings[heading] = OrderedDict()
            self.headings[heading][key] = value
        parsing.close()

    def get_ve_base(self, environ):
        """Find a directory to look for virtualenvs in.
        """
        # set ve_base to a path we can look for virtualenvs:
        # 1. .vexrc
        # 2. WORKON_HOME (as defined for virtualenvwrapper's benefit)
        # 3. $HOME/.virtualenvs
        # (unless we got --path, then we don't need it)
        ve_base_value = self.headings[self.default_heading].get('virtualenvs')
        if ve_base_value:
            ve_base = os.path.expanduser(ve_base_value)
        else:
            ve_base = environ.get('WORKON_HOME', '')
        if not ve_base:
            # On Cygwin os.name == 'posix' and we want $HOME.
            if platform.system() == 'Windows' and os.name == 'nt':
                _win_drive = environ.get('HOMEDRIVE')
                home = environ.get('HOMEPATH', '')
                if home:
                    home = os.path.join(_win_drive, home)
            else:
                home = environ.get('HOME', '')
            if not home:
                home = os.path.expanduser('~')
            if not home:
                return ''
            ve_base = os.path.join(home, '.virtualenvs')
        # pass through invalid paths so messages can be generated
        # if not os.path.exists(ve_base) or os.path.isfile(ve_base):
            # return ''
        return ve_base or ''

    def get_shell(self, environ):
        """Find a command to run.
        """
        command = self.headings[self.default_heading].get('shell')
        if not command and os.name != 'nt':
            command = environ.get('SHELL', '')
        command = shlex.split(command) if command else None
        return command


def extract_heading(line):
    """Return heading in given line or None if it's not a heading.
    """
    match = _HEADING_RE.match(line)
    if match:
        return match.group(1)
    return None


def extract_key_value(line, environ):
    """Return key, value from given line if present, else return None.
    """
    segments = line.split("=", 1)
    if len(segments) < 2:
        return None
    key, value = segments
    # foo passes through as-is (with spaces stripped)
    # '{foo}' passes through literally
    # "{foo}" substitutes from environ's foo
    value = value.strip()
    if value[0] == "'" and _SQUOTE_RE.match(value):
        value = value[1:-1]
    elif value[0] == '"' and _DQUOTE_RE.match(value):
        template = value[1:-1]
        value = template.format(**environ)
    key = key.strip()
    value = value.strip()
    return key, value


def parse_vexrc(inp, environ):
    """Iterator yielding key/value pairs from given stream.

    yields tuples of heading, key, value.
    """
    heading = None
    errors = []
    with inp:
        for line_number, line in enumerate(inp):
            line = line.decode("utf-8")
            if not line.strip():
                continue
            extracted_heading = extract_heading(line)
            if extracted_heading is not None:
                heading = extracted_heading
                continue
            kv_tuple = extract_key_value(line, environ)
            if kv_tuple is None:
                errors.append((line_number, line))
                continue
            try:
                yield heading, kv_tuple[0], kv_tuple[1]
            except GeneratorExit:
                break
    if errors:
        raise InvalidConfigError(inp.name, errors)
