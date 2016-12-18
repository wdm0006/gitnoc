from .settings import get_settings
from gitpandas import ProjectDirectory
import numpy as np
import os

__author__ = 'willmcginnis'


def week_leader_board(n=5):
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    extensions = settings.get('extensions', None)
    ignore_dir = settings.get('ignore_dir', None)
    repo = ProjectDirectory(working_dir=project_dir)
    ch = repo.commit_history(branch='master', extensions=extensions, ignore_dir=ignore_dir, limit=None, days=21)

    metric = 'net'
    print(ch)
    leader_board = {
        'top_committers': [],
        'top_repositories': [],
        'top_extensions': []
    }

    committers = ch.groupby(['committer']).agg({metric: np.sum})
    committers.reset_index(inplace=True)
    committers = committers.sort_values(by=[metric], ascending=False)
    leader_board['top_committers'] = [{'label': x[0], 'net': int(x[1]), 'rank': idx + 1} for idx, x in enumerate(committers.values.tolist()[:n])]

    repos = ch.groupby(['repository']).agg({metric: np.sum})
    repos.reset_index(inplace=True)
    repos = repos.sort_values(by=[metric], ascending=False)
    leader_board['top_repositories'] = [{'label': x[0], 'net': int(x[1]), 'rank': idx + 1} for idx, x in enumerate(repos.values.tolist()[:n])]

    if extensions is not None:
        ext_ranks = []
        for ext in extensions:
            ch = repo.commit_history(branch='master', extensions=[ext], ignore_dir=ignore_dir, days=21)
            ext_ranks.append((ch[metric].sum(), ext))
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


def get_repo_details(repo_name):
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    extensions = settings.get('extensions', None)
    ignore_dir = settings.get('ignore_dir', None)
    repos = ProjectDirectory(working_dir=project_dir)
    out = []
    for repo in repos.repos:
        if repo._repo_name() == repo_name:
            df = repo.file_detail(extensions=extensions, ignore_dir=ignore_dir)
            df = df.reset_index(level=2)
            df = df.sort_values(by=['loc'], ascending=False)
            df.reset_index(inplace=True)
            for idx in range(df.shape[0]):
                out.append({
                    'file_name': df.loc[idx, 'file'],
                    'loc': df.loc[idx, 'loc'],
                    'owner': df.loc[idx, 'file_owner'],
                    'extension': df.loc[idx, 'ext'],
                    'last_edit': df.loc[idx, 'last_edit_date'].strftime('%H:%M %d-%m-%Y'),
                    'clean_file_name': df.loc[idx, 'file'].replace('/', '-')
                })
    return out


def get_repo_names():
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    repos = ProjectDirectory(working_dir=project_dir)
    repo_names = [str(x._repo_name()) for x in repos.repos]
    return repo_names