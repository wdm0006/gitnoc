from gitnoc.services import metrics as metrics_service


class _Values:
    def __init__(self, rows):
        self.rows = rows

    def tolist(self):
        return self.rows


class _GroupedFrame:
    def __init__(self, rows):
        self.values = _Values(rows)

    def agg(self, *args, **kwargs):
        return self

    def reset_index(self, *args, **kwargs):
        return self

    def sort_values(self, *args, **kwargs):
        self.values.rows.sort(key=lambda row: row[1], reverse=True)
        return self


class _NetColumn:
    def __init__(self, total):
        self.total = total

    def sum(self):
        return self.total


class _HistoryFrame:
    def __init__(self, net, grouped=None):
        self.net = net
        self.grouped = grouped or {}

    def groupby(self, columns):
        return _GroupedFrame(list(self.grouped[columns[0]]))

    def __getitem__(self, key):
        assert key == "net"
        return _NetColumn(self.net)


def test_week_leader_board_ranks_each_extension_from_its_own_history(settings_env, monkeypatch):
    settings_env.write([
        {"profile_name": "a", "current_profile": True,
         "project_dir": "/tmp/code", "extensions": ["py", "js"],
         "ignore_dir": ["vendor"], "branch": "main"},
    ])
    calls = []

    class FakeProjectDirectory:
        def __init__(self, working_dir=None, cache_backend=None):
            pass

        def commit_history(self, **kwargs):
            calls.append(kwargs)
            include_globs = kwargs["include_globs"]
            if include_globs == ["*.py", "*.js"]:
                return _HistoryFrame(12, {
                    "committer": [("alice", 8), ("bob", 4)],
                    "repository": [("api", 9), ("web", 3)],
                })
            return _HistoryFrame({("*.py",): 5, ("*.js",): 7}[tuple(include_globs)])

    monkeypatch.setattr(metrics_service, "ProjectDirectory", FakeProjectDirectory)

    result = metrics_service.week_leader_board(n=5)

    assert [call["include_globs"] for call in calls] == [
        ["*.py", "*.js"],
        ["*.py"],
        ["*.js"],
    ]
    assert result == {
        "top_committers": [
            {"label": "alice", "net": 8, "rank": 1},
            {"label": "bob", "net": 4, "rank": 2},
        ],
        "top_repositories": [
            {"label": "api", "net": 9, "rank": 1},
            {"label": "web", "net": 3, "rank": 2},
        ],
        "top_extensions": [
            {"label": "js", "net": 7, "rank": 1},
            {"label": "py", "net": 5, "rank": 2},
        ],
    }
