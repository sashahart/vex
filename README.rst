Vex
###

Run a command in the named virtualenv.

vex is an alternative to virtualenv's ``source wherever/bin/activate``
and ``deactivate``, and virtualenvwrapper's ``workon``, and also
virtualenv-burrito if you use that.
It works in a more elegant way, though it does less.
You might find it nicer to use.
And it works with non-bash shells.


How it works
============

``vex`` just runs any command in a virtualenv, without modifying the current
shell environment.

To know why this is different, you have to understand a little about how
virtualenv normally works.
The normal way people use a virtualenv (other than virtualenvwrapper,
which does this for them) is to open a shell and source
a file called ``whatever/bin/activate``.
Sourcing this shell script modifies the environment in the current shell.
It saves the old values and sets up a shell function named ``deactivate``
which restores those old values. When you run ``deactivate`` it restores
its saved values.
This is also the way virtualenvwrapper's ``workon`` functions - after all, it
is a wrapper for virtualenv.
If you want to use a virtualenv inside a script you probably don't use
activate, though, you just run the python that is inside the virtualenv's
bin/ directory.

The way virtualenv's activate works isn't elegant, but it usually works fine.
It's just specific to the shell, and sometimes gets a little fiddly, because of
that decision to modify the current shell environment.

The principle of ``vex`` is much simpler, and it doesn't care what shell you
use, because it does not modify the current environment. It only sets up the
environment of the new process, and those environment settings just go away
when the process does. So no ``deactivate`` or restoration of environment is
necessary.

For example, if you run ``vex foo bash`` then that bash shell has the right
environment setup, but specifically "deactivating the virtualenv" is
unnecessary; the virtualenv "deactivates" when the process ends,
e.g. if you use ``exit`` or Ctrl-D as normal to leave bash. That's just
an example with bash, it works the same with anything.
(More examples in the Examples section.)


Examples
========

vex should work with most commands you can think of.
Try it out.

``vex foo bash``
    Launch a bash shell with virtualenv foo activated in it.
    To deactivate, just exit the shell (using "exit" or Ctrl-D).

``vex foo python``
    Launch a Python interpreter inside virtualenv foo.

``vex foo which python``
    Verify the path to python from inside virtualenv foo.

``vex foo pip freeze``
    See what's installed in virtualenv foo.

``vex foo pip install ipython``
    Install ipython inside virtualenv foo.

``vex foo ipython``
    Launch the ipython interpreter you have installed inside virtualenv foo.

``vex foo``
    Launch your shell (as specified in SHELL or ~/.vexrc) in virtualenv foo
    (this is like a direct replacement for 'workon').

``vex foo cmd``
    On Windows, this launches a "DOS" shell using virtualenv foo.
    (Try that with virtualenvwrapper!)

``vex foo powershell``
    On Windows, this launches a PowerShell instance using virtualenv foo.

``vex -mr ephemeral``
    In one command, this creates a virtualenv named ephemeral, then runs
    a shell (since there was no argument), then after that shell exits, vex
    removes the virtualenv named ephemeral.


If you break things by doing weird fun things with vex, you get to keep all the
pieces left over.


How to install vex
==================

You can just 'pip install vex,' but for convenience it's recommended to install
vex with the user scheme as follows::

    pip install --user vex

Though --user requires a little initial setup, this setup occurs once for all
tools (see the next section), experienced Python developers have already done
it, and there are two reasons for using it despite the small extra trouble.

First, it is not that convenient to use vex only from a virtualenv (though you
can) because then you need to use some other technique to activate the
virtualenv in which you have vex installed, in order to get access to it.
That would usually be an unnecessary waste of time.

Second, it does not require root privileges and does not make any system-wide
messes. Installing Python libraries system-wide is something you should
normally leave to your OS package manager; you are probably doing yourself
a favor if you learn never to use ``sudo pip`` or ``sudo easy_install``.
``pip install --user`` mostly substitutes for the purposes which would
otherwise use ``sudo``.
As an added benefit, you can use ``pip install --user`` on systems where you
are not allowed to make global modifications, or voluntarily refrain in order
to protect the global configuration.

You shouldn't normally have to separately install virtualenv; pip should drag
that in if you don't already have it.

If you don't have pip, `learn to install pip <http://pip.readthedocs.org/en/latest/installing.html>`_.

To uninstall, just use ``pip uninstall vex -y``.


First-time setup for Python beginners
=====================================

The PATH problem
----------------

Though ``pip install --user`` is the way I recommend to install command-line
Python tools like vex, it won't necessarily give you immediate results if your
machine is not fully set up for Python development. The reason is that
``pip install --user`` puts the script in a directory which isn't on the
default ``$PATH`` (Windows: ``%PATH%``; PowerShell: ``$env:path``).

For example, a Linux user named sam might see the script installed at::

    /home/sam/.local/bin/vex

(the exact path may vary); typing 'vex' will result in a 'command not
found', though inconveniently typing the absolute path will work.
Similarly, a Windows user named sam might see the script installed at::

    c:\users\sam\appdata\roaming\python\scripts\vex

and typing 'vex' will result in 'is not recognized' ... but again, giving
an absolute path will work, it's just inconvenient.
This is not that hard to solve, if you have it then PLEASE take a few minutes
to walk through the next section.

The PATH solution
-----------------

**The solution is to adjust your PATH to include the appropriate directory.**

For example, on Linux, sam might edit his shell config (e.g., ~/.profile) at
the end, to read::

    PATH=$PATH:/home/sam/.local/bin

while on Windows, sam might go into the 'Environment Variables' control panel
(Control Panel > System > Advanced System Settings > Environment Variables)
and in the upper box under 'User variables for sam', double-click 'PATH',
and append the following to its current value (semicolon and all)::

    ;c:\users\sam\appdata\roaming\python\scripts

This will allow Windows to know what you mean when you type 'vex' (or the name
of any Python command-line tool which supports Windows and which you have
wisely installed with ``pip install --user``).

Another PATH problem
--------------------

Unless you already know better, if you need to adjust PATH for the benefit
of your shell or installing some utility, you probably want to do that
with changes in ~/.profile or equivalent (e.g. ~/.bash_profile, ~/.zprofile),
which will take effect the next time you start a login shell.
Otherwise, you might break a whole class of things that includes vex,
in a way that cannot be reasonably automatically corrected. 

If you understood that, then you don't have to read the rest of this section
which is just for explanation. Here's the longer story:

Apparently some command-line tools have recommended in their docs that you
stick things on the front of $PATH from ~/.bashrc (equivalently .zshrc, etc.)
But this can cause problems for other utilities and scripts, if you do not
understand the meaning of doing it this way instead of another way.
The meaning of making these changes in files like ~/.bashrc instead of
other files is this: "I want this directory to be searched for executables
before ANY other directory, EVERY time. This is VERY important to me. It's 
my favorite directory to find executables in."

This might not normally be a problem for you. 
But it means that any other script or utility which puts another directory at
the front of PATH is going to be overruled. For example, vex helpfully puts the
bin/ directory of the relevant virtualenv at the head of PATH. It's the only
reasonable way to achieve this effect. But if your ~/.bashrc says "SMASH PATH"
then when you run bash under vex, vex will hand off a perfectly good
virtualenv-activated environment for bash to use, and then after vex hands off
bash will smash PATH as you instructed, and something else will have priority
before your virtualenv stuff. 

There's nothing bash or vex can do about this because, first, it's impossible
to determine whether this was a mistake or something you literally intended,
and not okay to squash the people who might literally intend this; and second,
the only way that vex could override what you told bash to do would be for me
to give you more shell-specific crap for you to source in ~/.bashrc that
mutates the current environment, which is exactly what vex is getting away
from. There is literally no way for vex to stop processes from messing up their
own environments, the best it can do is hand off the right thing.

So instead of telling bash to do something that breaks vex, then wanting vex to
do something which breaks everything else to override what you told bash to do,
just don't make this change in ~/.bashrc unless you WANT other things to take
precedence over your virtualenvs whenever you start bash. 

A good solution is to use ~/.profile (or similar files your shell uses like
~/.bash_profile, ~/.zprofile) to make changes in PATH. Because this only runs
at the creation of a login shell, e.g. when you log in to X, it is possible
for vex and other utilities to make the right adjustment without something
in ~/.bashrc squishing it immediately afterward. And when the subprocess goes
away, there is no environmental residue, and vex doesn't have to couple to
specific shells or depend on shell at all, and you don't have to put any more
crap in ~/.bashrc unless it's specifically what you mean to have there.

A detail pertaining to shell environment variables like WORKON_HOME
-------------------------------------------------------------------

In shell, putting a tilde in quotes like '~' or "~" means you want
to suppress expansion of that into the path of your home directory.
Therefore, if you set WORKON_HOME to some quoted value, it won't be
expanded, and vex will have no way to know whether you mean a path
with a tilde in it, but will have to assume that you do.

So when you set a variable like WORKON_HOME, use one of these styles::

    export WORKON_HOME=~/.virtualenvs
    export WORKON_HOME=$HOME/.virtualenvs
    export WORKON_HOME="$HOME/.virtualenvs"


Options
=======

vex is simple so there aren't a lot of options.

Since everyone seems to like workon more than specifying absolute
virtualenv paths, vex defaults to that kind of behavior.
But it may still be necessary to use an absolute path now and then.
So you can point vex at the absolute path of a virtualenv with ``--path``.
For example, if you made a virtualenv under the current directory
called env and don't want to type out ``source env/bin/activate``::

    vex --path env pip freeze

You can also set which directory the subprocess starts in,
like this shell which starts in ``/tmp``::

    vex --cwd /tmp foo bash

You can also have vex create the named virtualenv before running the command::

    vex --make foo bash

Or you can have vex remove the already-existing virtualenv after running the
command::

    vex --remove foo bash

Or you can create a previously nonexistent virtualenv, run the command
in it, then remove it once the command exits::

    vex --make --remove foo bash

This can also be abbreviated as ``'vex -mr foo bash'``.

For the benefit of people who do not use the shell completions,
you can also list available virtualenvs::

    vex --list

This should list the virtualenvs you have in the directory
specified by 'virtualenvs=' in .vexrc or by setting $WORKON_HOME. 
``--list`` does not combine with any other options.

Since you might have many virtualenvs or you might be looking
for something specific (or building your own completion),
you can also list virtualenvs beginning with a certain prefix::

    vex --list a

If you need more detailed filtering, pipe to grep or something.


Config
======

Like many user-oriented command line utilities, vex has an optional config
file to specify defaults. Its default location ``~/.vexrc``. Example::

    shell=bash
    virtualenvs=~/.my_virtualenvs
    env:
        ANSWER=42

This specifies that the result of running ``vex foo`` (no command)
is to run bash, as in ``vex foo bash``;
that the place to look for named virtualenvs
is ``~/.my_virtualenvs``; and that processes you launched with vex should all
get certain environment variables (in this case, ``ANSWER`` set to ``42``).

Thanks to `Nick Coghlan <https://github.com/ncoghlan>`_, there is also an
option to specify the default python you want to use, if you haven't specified
it. Here's an example line you could put in vexrc::

    python=python3

(Equivalent to always specifying ``--python python3`` when using ``vex -m``.)

If you want to use a config someplace other than ``~/.vexrc``::

    vex --config ~/.tempvexrc foo bash


Shell Prompts
=============

This section gives some simple examples of how you could customize your shell
to reflect the current virtualenv, since vex intentionally does not mess with
your shell's prompt (in order to stay shell-agnostic).

Beginner's note: don't put these in ``~/.vexrc``, that won't do anything!
If you don't know what you're doing, use the suggested filenames.


bash
----

Here is an example of what you could put in ``~/.bashrc``:

.. code-block:: bash

    function virtualenv_prompt() {
        if [ -n "$VIRTUAL_ENV" ]; then
            echo "(${VIRTUAL_ENV##*/}) "
        fi
    }

    export PS1='$(virtualenv_prompt)\u@\H> '


zsh
---

Here is an example of what you could put in ``~/.zshrc``:

.. code-block:: bash

    # zsh needs this option set to use $(virtualenv_prompt)
    setopt prompt_subst

    function virtualenv_prompt() {
        if [ -n "$VIRTUAL_ENV" ]; then
            echo "(${VIRTUAL_ENV##*/}) "
        fi
    }

    export PROMPT='$(virtualenv_prompt)%n@%m> '

ksh
---

Here is something you can start from in ``~/.kshrc``:

.. code-block:: ksh

    PS1='${VIRTUAL_ENV:+($( basename $VIRTUAL_ENV )) }${USER}@${HOSTNAME:=$(hostname)}:$PWD> '

This should also work for mksh in ``~/.mkshrc``.


fish
----

Here is some code you could put into ``~/.config/fish/functions/fish_prompt.fish``.

.. code-block:: text

    function fish_prompt
        if test -n "$VIRTUAL_ENV"
            set -l ve_tag (basename "$VIRTUAL_ENV")
            echo -n (set_color green)"($ve_tag) "(set_color normal)
        end
        printf '%s@%s %s%s%s> ' (whoami) (hostname|cut -d . -f 1) (set_color $fish_color_cwd) (prompt_pwd) (set_color normal)
    end


tcsh
----

If you're among the proud few who use tcsh, this kind of works
(and you may ridicule my terrible csh skills and propose a better solution!)
However, it relies on ``$VIRTUAL_ENV`` never changing, so in other words it's
really only usable if you stick to vex when using tcsh, and don't mess with
``$VIRTUAL_ENV`` yourself. There has to be a better solution...

.. code-block:: tcsh

    if ($?VIRTUAL_ENV == 0) then
        set VIRTUAL_ENV=""
    endif
    set prompt="`if ( "$VIRTUAL_ENV" != "" ) basename $VIRTUAL_ENV`|%N@%m:%~%# "


Shell Completion
================

vex provides a completely optional mechanism to set up
completion of the 'vex' command for several popular shells.
This allows you to do things like hitting the 'TAB' key
after 'vex mye' and getting it expanded to 'vex myenv'.
(Specific features depend on the shell.)
It's completely optional. vex will work without it. So if vex doesn't have
a completion configuration for your shell, don't worry, you can still use vex.
And if you want a completion config, please suggest or contribute one
on `Github <https://github.com/sashahart/vex>`_.


Since completion requires a modification of the current shell
state, and vex refuses to do this, it can be done by having the shell
evaluate some lines emitted by vex.

If you use these, use them EXACTLY as described here.
For example, omitting quotes may have confusing results.
And don't put these in ``~/.vexrc``, that won't do anything!

bash
----

This could be put in, e.g., ``~/.bashrc``.

.. code-block:: bash

   eval "$(vex --shell-config bash)"

OS X users may need to enable bash completion before this will work.

zsh
---

This could be put in, e.g., ``~/.zshrc``.

.. code-block:: bash

   eval "$(vex --shell-config zsh)"

If you did not already enable zsh completion, your .zshrc file should do that
before this will work, using e.g. 'autoload compinit; compinit'. The symptom of
this problem will be something like 'command not found: compdef'.

fish
----

This could be put in, e.g., ``~/.config/fish/config.fish``.

.. code-block:: text

    . (vex --shell-config fish|psub)


Caveats
=======

Put optional flags for vex right after ``vex``. If you put them in the
command, vex will naturally think they are meant for the command.
For example, ``vex foo mope -h`` cannot be understood as providing
an -h flag to vex; vex has to interpret it as part of the command.
Even ``vex foo -h mope`` must interpret '-h mope' as a command, because it is
possible that an executable name on ``$PATH`` begins with a dash.

vex won't use virtualenvs with names that start with a dash, because this is
the character which prefixes a command-line flag (option).

Don't be surprised if 'vex foo sudo bash' results in a shell that doesn't use
your virtualenv. Safe sudo policy often controls the environment, notably as
a default on Debian and Ubuntu. It's better not to mess with this policy,
especially if you knew little enough that you wondered why it didn't work.
As a workaround, you can use this:

.. code-block:: bash

    sudo env PATH="$PATH" vex foo bash

vex should not be particularly slow to mere mortals, but if you run it
a million times in a script then the effects of python startup might become
noticeable. If you have this problem, consider running your virtualenv's python
directly. (It works at least as well, it's just usually less convenient.)

If you run e.g. ``bash -c ls`` you may see that ls does not generate color,
because it decides whether to do that after detecting whether it is talking to
a terminal. Similarly, commands run through vex are liable to suppress their
color. Things like grep can be given options like --color=always, but then 
piped or redirected output will contain color codes. If you want to run Python
unit tests in virtualenvs, just use `tox <http://tox.readthedocs.org/en/latest/>`_, 
it's great.

As with other tools, if you want to use a virtualenv with spaces in the name,
your shell is probably going to force you to quote its name in order to make
the tool understand you are not providing more than one actual argument.
For example, ``vex foo bar baz`` will be interpreted by bash/zsh as running
'bar baz' in virtualenv foo, NOT as running baz in 'foo bar' or anything else.
Again, this isn't down to vex, it is just how these shells work.

Mind the results of asking to run commands with shell variables in them.
For example, you might expect this to print 'foo':

.. code-block:: bash

    vex foo echo $VIRTUAL_ENV

The reason it doesn't is that your current shell is interpreting $VIRTUAL_ENV
even before vex gets it or can pass it to the subprocess. You could quote it:

.. code-block:: bash

    vex foo echo '$VIRTUAL_ENV'

but then it literally prints $VIRTUAL_ENV, not the shell evaluation of the
variable, because that isn't the job of vex. That's a job for bash to do.

.. code-block:: bash

    vex foo bash -c 'echo $VIRTUAL_ENV'
