from gitnoc.services.settings import get_settings
from gitpandas import ProjectDirectory
import numpy as np
import pandas as pd
import json
import os

__author__ = 'willmcginnis'


def week_leader_board(n=5):
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    extensions = settings.get('extensions', None)
    ignore_dir = settings.get('ignore_dir', None)
    repo = ProjectDirectory(working_dir=project_dir)
    ch = repo.commit_history(branch='master', extensions=extensions, ignore_dir=ignore_dir, limit=None, days=7)

    print(ch)
    leader_board = {
        'top_committers': [],
        'top_repositories': [],
        'top_extensions': []
    }

    committers = ch.groupby(['committer']).agg({'net': np.sum})
    committers.reset_index(inplace=True)
    committers = committers.sort_values(by=['net'], ascending=False)
    leader_board['top_committers'] = [{'label': x[0], 'net': int(x[1]), 'rank': idx + 1} for idx, x in enumerate(committers.values.tolist()[:n])]

    repos = ch.groupby(['repository']).agg({'net': np.sum})
    repos.reset_index(inplace=True)
    repos = repos.sort_values(by=['net'], ascending=False)
    leader_board['top_repositories'] = [{'label': x[0], 'net': int(x[1]), 'rank': idx + 1} for idx, x in enumerate(repos.values.tolist()[:n])]

    if extensions is not None:
        ext_ranks = []
        for ext in extensions:
            ch = repo.commit_history(branch='master', extensions=[ext], ignore_dir=ignore_dir, days=7)
            ext_ranks.append((ch['net'].sum(), ext))
        ext_ranks = sorted(ext_ranks, key=lambda x: x[0], reverse=True)[:n]
        leader_board['top_extensions'] = [{'label': x[1], 'net': int(x[0]), 'rank': idx + 1} for idx, x in enumerate(ext_ranks)]

    return leader_board


def get_punchcard():
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    extensions = settings.get('extensions', None)
    ignore_dir = settings.get('ignore_dir', None)
    repo = ProjectDirectory(working_dir=project_dir)

    pc = repo.punchcard(branch='master', extensions=extensions, ignore_dir=ignore_dir)

    data_set = []
    for idx in range(pc.shape[0]):
        data_set.append([pc.loc[idx, 'day_of_week'], pc.loc[idx, 'hour_of_day'], pc.loc[idx, 'net']])

    return data_set
