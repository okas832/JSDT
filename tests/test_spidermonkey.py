import pytest

from spidermonkey import Spidermonkey


def test_command_line_code():
    """Test that command line code is executed."""

    proc = Spidermonkey(code='print("Hello")')
    stdout, stderr = proc.communicate()

    assert (stdout, stderr) == (b'Hello\n', b'')
    assert proc.returncode == 0


@pytest.mark.parametrize('file', ('-',
                                  ('/dev/null', '-'),
                                  ('-', '/dev/null')))
def test_early_script_file(file):
    """Test that an early script file is executed as expected."""

    proc = Spidermonkey(early_script_file=file)
    stdout, stderr = proc.communicate(b'print("World")')

    assert (stdout, stderr) == (b'World\n', b'')
    assert proc.returncode == 0


def test_script_file():
    """Test that a script file is executed as expected."""

    proc = Spidermonkey(script_file='-')
    stdout, stderr = proc.communicate(b'print("World")')

    assert (stdout, stderr) == (b'World\n', b'')
    assert proc.returncode == 0


def test_multi_scripts():
    """Test that when multiple scripts are passed, they're all executed."""

    CODE = (""" function makeSave() {
                    let save = 0;
                    function clo(val) {
                        if (val === undefined) return save;
                        else save = val;
                    }
                    return clo;
                }
                test = makeSave();
            """
            'print(test())',
            'test(185)',
            'print(test())',
            'print("Hello")')

    proc = Spidermonkey(early_script_file='-', code=CODE)
    stdout, stderr = proc.communicate(b'print("World")')

    print(stderr)

    assert (stdout, stderr) == (b'0\n185\nHello\nWorld\n', b'')
    assert proc.returncode == 0


def test_script_args():
    """Test that script args are set as expected."""

    proc = Spidermonkey(code='print(scriptArgs)',
                        script_args=('Hello', 'World'))
    stdout, stderr = proc.communicate(b'')

    assert (stdout, stderr) == (b'Hello,World\n', b'')
    assert proc.returncode == 0


def test_extra_flags():
    """Test that extra flags are processed as expected."""

    proc = Spidermonkey(extra_flags=('-e', 'print(scriptArgs)'),
                        script_args=('Hello', 'World'))
    stdout, stderr = proc.communicate(b'')

    assert (stdout, stderr) == (b'Hello,World\n', b'')
    assert proc.returncode == 0


def test_compileonly():
    """Test that compileonly returns a status but no output."""

    # Valid code: no output, returns 0.
    proc = Spidermonkey(compile_only=True, script_file='-')
    stdout, stderr = proc.communicate(b'print("Hello")')

    assert not stdout
    assert not stderr
    assert proc.returncode == 0

    # Invalid code: only stderr output, returns > 0.
    proc = Spidermonkey(compile_only=True, script_file='-')
    stdout, stderr = proc.communicate(b'print("Hello"')

    assert stdout == b''
    assert stderr != b''
    assert proc.returncode > 0

    # The compile-only flag is not applied to code passed on the
    # command line, so it should not be accepted.
    with pytest.raises(AssertionError):
        Spidermonkey(compile_only=True, code="print('Hello')")
