import os


class Object(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key.startswith('_'):
                continue
            setattr(self, key, value)


class FakePopen(object):
    def __init__(self, returncode=888):
        self.command = None
        self.env = None
        self.cwd = None
        self.waited = False
        self.expected_returncode = returncode
        self.returncode = None

    def __call__(self, command, env=None, cwd=None):
        self.command = command
        self.env = env
        self.cwd = cwd
        return self

    def wait(self):
        self.waited = True
        self.returncode = self.expected_returncode


class FakeEnviron(object):
    def __init__(self, **kwargs):
        self.original = None
        self.kwargs = kwargs

    def __enter__(self):
        self.original = os.environ
        fake_environ = self.kwargs.copy()
        os.environ = fake_environ
        return fake_environ

    def __exit__(self, typ, value, tb):
        os.environ = self.original
        self.original = None


class PatchedModule(object):
    def __init__(self, module, **kwargs):
        self.module = module
        self.originals = None
        self.kwargs = kwargs

    def __enter__(self):
        self.originals = {key: getattr(self.module, key, None)
                          for key in self.kwargs.keys()}
        for key, value in self.kwargs.items():
            setattr(self.module, key, value)
        return self.module

    def __exit__(self, typ, value, tb):
        for key, value in self.originals.items():
            setattr(self.module, key, value)
        self.originals = None
