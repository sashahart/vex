from setuptools import setup

with open('README.rst', 'r') as inp:
    long_description = inp.read()

setup(
    name="vex",
    version="0.0.1",
    author="Sasha Hart",
    author_email="s@sashahart.net",
    url="http://github.com/sashahart/vex",
    description="Run commands in a virtualenv",
    license="MIT",
    long_description=long_description,
    keywords="virtualenv virtualenvwrapper workon installation deployment",
    install_requires=['virtualenv'],
    packages=['vex'],
    package_data={'vex': ['shell_configs/*']},
    scripts=['scripts/vex'],
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
    ]
)
