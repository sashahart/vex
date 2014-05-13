"""Config file processing (.vexrc).
"""
import re
from collections import defaultdict

_IDENTIFIER_PATTERN = '[a-zA-Z][_a-zA-Z0-9]*'
_HEADING_RE = re.compile(
    r'^(' + _IDENTIFIER_PATTERN + r'):[ \t\n\r]*\Z')
_VAR_RE = re.compile(
    r'[ \t]*(' + _IDENTIFIER_PATTERN + r') *= *(.*)[ \t\n\r]*$')


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


def read_vexrc(full_path):
    """Read and parse a .vexrc file.
    """
    headings = defaultdict(dict)
    headings[None] = {}
    errors = []

    with open(full_path, 'rb') as inp:
        heading = None
        for i, line in enumerate(inp):
            line = line.decode('utf-8')
            match = _HEADING_RE.match(line)
            if match:
                heading = match.group(1)
                continue
            match = _VAR_RE.match(line)
            if match:
                key = match.group(1)
                value = match.group(2)
                headings[heading][key] = value
                continue
            if not line.strip():
                continue
            errors.append((i, line))
    if errors:
        raise InvalidConfigError(errors)
    return headings
