"""Config file processing (.vexrc).
"""
import sys
import re
from collections import defaultdict

_IDENTIFIER_PATTERN = '[a-zA-Z][_a-zA-Z0-9]*'
_SQUOTE_RE = re.compile("'([^']*)'\Z") # NO squotes inside
_DQUOTE_RE = re.compile('"([^"]*)"\Z') # NO dquotes inside
_HEADING_RE = re.compile(
    r'^(' + _IDENTIFIER_PATTERN + r'):[ \t\n\r]*\Z')
_VAR_RE = re.compile(
    r'[ \t]*(' + _IDENTIFIER_PATTERN + r') *= *(.*)[ \t\n\r]*$')


if sys.version_info < (3, 0):
    FileNotFoundError = OSError


class InvalidConfigError(Exception):
    """Raised when there is an error during a .vexrc file parse.
    """
    def __init__(self, errors):
        Exception.__init__(self)
        self.errors = errors

    def __str__(self):
        return "errors on lines {0!r}".format(
            list(tup[0] for tup in self.errors)
        )


def read_vexrc(full_path, environ=None):
    """Read and parse a .vexrc file.
    """
    headings = defaultdict(dict)
    headings[None] = {}
    errors = []
    environ = environ or {}

    try:
        inp = open(full_path, 'rb')
    except FileNotFoundError:
        return headings
    with inp:
        heading = None
        for i, line in enumerate(inp):
            line = line.decode('utf-8')
            match = _HEADING_RE.match(line)
            if match:
                heading = match.group(1)
                continue
            segments = line.split("=", 1)
            if len(segments) == 2:
                key, value = segments
                value = value.strip()
                # foo passes through as-is (with spaces stripped)
                # '{foo}' passes through literally
                # "{foo}" substitutes from environ's foo
                if value[0] == "'" and _SQUOTE_RE.match(value):
                    value = value[1:-1]
                elif value[0] == '"' and _DQUOTE_RE.match(value):
                    template = value[1:-1]
                    value = template.format(**environ)
                key = key.strip()
                value = value.strip()
                headings[heading][key] = value
                continue
            errors.append((i, line))
    if errors:
        raise InvalidConfigError(errors)
    return headings
