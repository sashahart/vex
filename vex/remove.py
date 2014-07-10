import os
import shutil
from vex import exceptions


def obviously_not_a_virtualenv(path):
    include = os.path.join(path, 'include')
    bin = os.path.join(path, 'bin')
    scripts = os.path.join(path, 'Scripts')
    if not os.path.exists(bin) or os.path.exists(scripts):
        return True
    if not os.path.exists(include):
        return True
    if not any(filename.startswith('py') for filename in os.listdir(include)):
        return True
    return False


def handle_remove(ve_path):
    if not os.path.exists(ve_path):
        return
    if hasattr(os, "geteuid"):
        if os.geteuid() == 0 or os.environ.get('USER', '') == 'root':
            raise exceptions.VirtualenvNotRemoved(
                "not removing any directory as root user")
    if ve_path in ("/", "\\"):
        raise exceptions.VirtualenvNotRemoved(
            "not removing possible root directory {0!r}".format(ve_path))
    if ve_path == os.path.expanduser("~"):
        raise exceptions.VirtualenvNotRemoved(
            "not removing possible home directory {0!r}".format(ve_path))
    # last-minute checks
    if obviously_not_a_virtualenv(ve_path):
        raise exceptions.VirtualenvNotRemoved(
            "path {0!r} did not look like a virtualenv".format(ve_path))
    print("Removing {0!r}".format(ve_path))
    shutil.rmtree(ve_path)
