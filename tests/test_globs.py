"""The ignore globs handed to git-pandas must actually exclude what they name.

git-pandas filters with a plain ``fnmatch.fnmatch(<repo-relative path>, glob)``
per pattern, so the shape of each pattern is the whole behavior.  The matching
test below reproduces that filter over a fixed list of representative paths and
pins exactly which ones an entry excludes.
"""
import fnmatch

import pytest

from gitnoc.services.globs import ignore_globs, include_globs


# The same paths git-pandas would hand to its filter: repo-relative, no leading
# slash, mixing root-level files/directories with nested ones.
REPO_PATHS = [
    'a-b.py',
    'main.py',
    'tests/t.py',
    'tests/sub/deep.py',
    'tests_helper.py',
    'src/vendor/v.py',
    'src/vendor',
    'src/app.py',
    'lib/tests/t.py',
]


def excluded(entries, paths=REPO_PATHS):
    """Reproduce git-pandas' exclude vote: any matching glob drops the path."""
    globs = ignore_globs(entries)
    return [p for p in paths if any(fnmatch.fnmatch(p, g) for g in globs)]


# --- exact glob lists -------------------------------------------------------

def test_top_level_directory_globs():
    assert ignore_globs(['tests']) == ['tests/*', '*/tests/*', 'tests', '*/tests']


def test_nested_directory_globs():
    assert ignore_globs(['src/vendor']) == [
        'src/vendor/*', '*/src/vendor/*', 'src/vendor', '*/src/vendor',
    ]


def test_file_path_globs():
    assert ignore_globs(['a-b.py']) == ['a-b.py/*', '*/a-b.py/*', 'a-b.py', '*/a-b.py']


def test_multiple_entries_are_expanded_in_order():
    assert ignore_globs(['tests', 'docs']) == [
        'tests/*', '*/tests/*', 'tests', '*/tests',
        'docs/*', '*/docs/*', 'docs', '*/docs',
    ]


@pytest.mark.parametrize('entries', [None, [], [''], ['  '], ['/']])
def test_empty_entries_produce_no_globs(entries):
    assert ignore_globs(entries) == []


def test_surrounding_slashes_and_whitespace_are_trimmed():
    assert ignore_globs([' tests/ ']) == ignore_globs(['tests'])


# --- what the globs actually match ------------------------------------------

def test_top_level_directory_is_excluded_without_over_matching():
    # 'tests' catches the root dir, its nested contents and a nested 'tests' dir,
    # but NOT the sibling file whose name merely starts with 'tests'.
    assert excluded(['tests']) == ['tests/t.py', 'tests/sub/deep.py', 'lib/tests/t.py']


def test_nested_directory_is_excluded():
    assert excluded(['src/vendor']) == ['src/vendor/v.py', 'src/vendor']


def test_exact_file_path_is_excluded():
    assert excluded(['a-b.py']) == ['a-b.py']


def test_nothing_is_excluded_without_entries():
    assert excluded([]) == []


# --- include globs ----------------------------------------------------------

def test_include_globs_per_extension():
    assert include_globs(['py', 'js']) == ['*.py', '*.js']


@pytest.mark.parametrize('extensions', [None, []])
def test_include_globs_empty_means_include_everything(extensions):
    # git-pandas turns an empty include list into ['*'], so passing [] through
    # unchanged is what keeps an unconfigured profile analyzing every file.
    assert include_globs(extensions) == []
