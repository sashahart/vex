from setuptools import setup

setup(
    name="vex",
    version="0.0.0",
    author="Sasha Hart",
    author_email="s@sashahart.net",
    url="http://github.com/sashahart/vex",
    description="Run one command in a virtualenv",
    license="MIT",
    keywords="virtualenv virtualenvwrapper workon",
    install_requires=['virtualenv'],
    packages=['vex'],
    scripts=['scripts/vex'],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.4",
    ]
)
