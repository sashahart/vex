import os
from setuptools import setup


with open('README.rst', 'r') as inp:
    LONG_DESCRIPTION = inp.read()


with open(os.path.join('vex', '_version.py'), 'r') as inp:
    _, VERSION = inp.read().split("=")
    VERSION = VERSION.strip(' "\n')


setup(
    name="vex",
    version=VERSION,
    author="Sasha Hart",
    author_email="s@sashahart.net",
    url="http://github.com/sashahart/vex",
    description="Run commands in a virtualenv",
    license="MIT",
    long_description=LONG_DESCRIPTION,
    keywords="virtualenv virtualenvwrapper workon installation deployment",
    install_requires=['virtualenv'],
    packages=['vex'],
    package_data={'vex': ['shell_configs/*', 'functional_tests/not_python']},
    scripts=['scripts/vex'],
    entry_points = {
        'console_scripts': ['vex = vex.main:main'],
    },
    classifiers=[
        "Topic :: Utilities",
        "Topic :: Software Development",
        "Topic :: System :: Shells",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: Implementation :: PyPy",
    ]
)
