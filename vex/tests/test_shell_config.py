from vex.config import Vexrc
from vex.shell_config import scary_path as scary, shell_config_for
from mock import patch


class TestShellConfigFor(object):
    def test_unknown_shell(self):
        vexrc = Vexrc()
        output = shell_config_for('unlikely_name', vexrc, {})
        assert output.strip() == b''

    def test_bash_config(self):
        vexrc = Vexrc()
        output = shell_config_for("bash", vexrc, {})
        assert output

    def test_zsh_config(self):
        vexrc = Vexrc()
        output = shell_config_for("zsh", vexrc, {})
        assert output

    def test_fish_config(self):
        vexrc = Vexrc()
        output = shell_config_for("fish", vexrc, {})
        assert output

    def test_bash_config_not_scary(self):
        vexrc = Vexrc()
        with patch('os.path.exists', returnvalue=True):
            output = shell_config_for("bash", vexrc, {'WORKON_HOME': '/hoorj'})
        assert output
        assert b'/hoorj' in output

    def test_zsh_config_not_scary(self):
        vexrc = Vexrc()
        with patch('os.path.exists', returnvalue=True):
            output = shell_config_for("zsh", vexrc, {'WORKON_HOME': '/hoorj'})
        assert output
        assert b'/hoorj' in output

    def test_fish_config_not_scary(self):
        vexrc = Vexrc()
        with patch('os.path.exists', returnvalue=True):
            output = shell_config_for("fish", vexrc, {'WORKON_HOME': '/hoorj'})
        assert output
        assert b'/hoorj' in output

    def test_bash_config_scary(self):
        vexrc = Vexrc()
        output = shell_config_for("bash", vexrc, {'WORKON_HOME': '$x'})
        assert output
        assert b'$x' not in output

    def test_zsh_config_scary(self):
        vexrc = Vexrc()
        output = shell_config_for("zsh", vexrc, {'WORKON_HOME': '$x'})
        assert output
        assert b'$x' not in output

    def test_fish_config_scary(self):
        vexrc = Vexrc()
        output = shell_config_for("fish", vexrc, {'WORKON_HOME': '$x'})
        assert output
        assert b'$x' not in output


class TestNotScary(object):
    """Test that scary_path does not puke on expected cases.

    The implementation is not expected to look for special patterns
    but to use general mechanisms like \w.
    """
    def test_normal(self):
        assert not scary(b"/home/user/whatever")
        assert not scary(b"/opt/weird/user/whatever")
        assert not scary(b"/foo")

    def test_underscore(self):
        assert not scary(b"/home/user/ve_place")

    def test_hyphen(self):
        assert not scary(b"/home/user/ve-place")

    def test_space(self):
        assert not scary(b"/home/user/ve place")

    def test_comma(self):
        assert not scary(b"/home/user/python,ruby/virtualenvs")

    def test_period(self):
        assert not scary(b"/home/user/.virtualenvs")


class TestScary(object):
    """Test that scary_path pukes on some known frightening cases.

    It isn't expected that the implementation specifically forbids
    these, it should err on the side of strictness/whitelisting;
    this just tests whether the given 'whitelist' is obviously
    not strict enough.
    """

    # def test_tilde_expansion(self):
    #     assert scary(b'~')

    def test_empty(self):
        """Empty variables can combine in surprising ways in shell

        and occur in a huge number of ways, intentional or not.
        So this is one of the first things to check.
        """
        assert scary(b'')

    def test_subshell(self):
        """prevent most obvious way of executing arbitrary cmds
        """
        assert scary(b'$(rm anything)')

    def test_subshell_with_backticks(self):
        """also most obvious way, slightly different notation
        """
        assert scary(b'`pwd`')

    def test_leading_double_quote(self):
        """prevent the most obvious way of breaking out of variable ref
        """
        assert scary(b'"; rm anything; echo')
        assert scary(b'"')

    def test_variable_expansion(self):
        """prevent second-pass substitution of variable etc.
        """
        assert scary(b'$HOME')

    def test_variable_expansion_with_braces(self):
        """also with braces style
        """
        assert scary(b'${HOME}')

    def test_variable_expansion_with_slash(self):
        """leading slash doesn't fool us
        """
        assert scary(b'/${HOME}')

    def test_variable_expansion_with_slash_and_suffix(self):
        """suffix doesn't fool us either
        """
        assert scary(b'/${HOME}/bar')

    def test_leading_single_quote(self):
        """prevent a less obvious way of messing with completion scripts
        """
        assert scary(b"' 'seems bad")
        assert scary(b"'")

    def test_trailing_backslash(self):
        """prevent making outside char literal or continuing line
        """
        assert len("\\") == 1
        assert scary(b"prefix\\")

    def test_leading_hyphen(self):
        """prevent passing switches (e.g. for find) instead of dir
        """
        assert scary(b"-delete")
        assert scary(b"--delete")

    def test_root(self):
        """Using bare root seems inherently wrong
        """
        assert scary(b"/")
        assert scary(b"C:")
        assert scary(b"C:\\")

    def test_null(self):
        """Anything maybe using C strings MIGHT screw up ASCII NUL
        """
        assert scary(b"\0")
        assert scary(b"\0b")
        assert scary(b"a\0b")
        assert scary(b"a\0")

    def test_newline(self):
        """shell can easily mess up newlines
        """
        assert scary(b"/foo\nbar")
        assert scary(b"/foo\n/bar")

    def test_comment(self):
        """Don't want to ignore to end of shell line
        """
        assert scary(b'#foo')
        assert scary(b'stuff  # foo')

    def test_arithmetic_expansion(self):
        assert scary(b'$(( 2 + 2 ))')

    def test_integer_expansion(self):
        assert scary(b'$[ 2 + 2 ]')

    def test_lt(self):
        assert scary(b'<foo')

    def test_gt(self):
        assert scary(b'>foo')

    def test_star(self):
        assert scary(b'*')

    def test_question_mark(self):
        assert scary(b'?')

    def test_here(self):
        assert scary(b"<<<")
        assert scary(b">>>")

    def test_semicolon(self):
        assert scary(b";")

    def test_or(self):
        assert scary(b"foo ||")

    def test_and(self):
        assert scary(b"foo &&")

    def test_background(self):
        assert scary(b"sleep 10 &")

    def test_pipeline(self):
        assert scary(b"| bar")
