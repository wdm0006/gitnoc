"""Glob construction shared by every analytics service.

git-pandas filters each candidate file with a plain
``fnmatch.fnmatch(<repo-relative path>, glob)`` per pattern, so a single
``*/<entry>/*`` pattern only ever matches a *nested* directory: repo-relative
paths carry no leading slash, and a file path is not a directory prefix.  Each
ignore entry is therefore expanded to cover a directory prefix and an exact
path, at the repository root and nested.
"""

__author__ = 'willmcginnis'


def ignore_globs(entries):
    """Build the git-pandas ``ignore_globs`` list for configured ignore entries.

    Each entry may name a directory (``tests``, ``src/vendor``) or an exact file
    path (``a-b.py``), at the repository root or nested anywhere below it.
    """
    globs = []
    for entry in entries or []:
        entry = str(entry).strip().strip('/')
        if not entry:
            continue
        globs.extend(['%s/*' % (entry, ), '*/%s/*' % (entry, ), entry, '*/%s' % (entry, )])

    return globs


def include_globs(extensions):
    """Build the git-pandas ``include_globs`` list for configured extensions.

    An empty list is passed through unchanged: git-pandas treats an empty
    include list as "include everything".
    """
    return ['*.%s' % (x, ) for x in extensions or []]
