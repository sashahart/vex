path_type = bytes

try:
    unicode
    str_type = unicode
except NameError:
    str_type = str
