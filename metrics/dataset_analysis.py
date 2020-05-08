import datetime
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

_repos_csv = []
_issues_csv = []

CSV_FPATH = Path('/home/lucas.rotsen/Git_Repos/benchmark_frameworks/csv_github')
METRICS_FPATH = Path('/home/lucas.rotsen/Git_Repos/benchmark_frameworks/metrics/raw')


def load_csv(file):
    return pd.read_csv(file, sep=',')


def get_files():
    global _repos_csv, _issues_csv
    csv_files = list(CSV_FPATH.glob('*.csv'))

    for file in csv_files:
        if 'issues' in file.name:
            _issues_csv.append(file)
        else:
            _repos_csv.append(file)


# TODO: avaliar e calcular métricas para o CSV consolidado
def consolidate_repos_csv():
    dfs = [load_csv(repo_csv) for repo_csv in _repos_csv]
    consolidated_df = pd.concat(dfs)
    consolidated_df.to_csv(METRICS_FPATH.joinpath('repos.csv'), encoding='utf-8', index=False)
    consolidated_df.describe().to_csv(METRICS_FPATH.joinpath('repos-metrics.csv'), encoding='utf-8', index=True)


def subtract_dates(closed_at, created_at):
    return (datetime.datetime.strptime(closed_at.split('T')[0], '%Y-%m-%d') -
            datetime.datetime.strptime(created_at.split('T')[0], '%Y-%m-%d')).days


def add_lifetime_col(df):
    df_len = df.shape[0]
    df['lifetime'] = [0] * df_len

    for i in range(df_len):
        df.at[i, 'lifetime'] = subtract_dates(df.loc[i, 'closed_at'], df.loc[i, 'created_at'])

    return df


def process_issues_csv(file):
    name = file.name.split('.')[0].split('_')[2]

    df = load_csv(file)
    df = add_lifetime_col(df)

    metrics = {
        'framework': name,
        'lft_median': [df['lifetime'].median()],
        'lft_mean': [df['lifetime'].mean()],
        'lft_stddev': [df['lifetime'].std()]
    }

    return pd.DataFrame(metrics)


def consolidate_issues_csv():
    """

    1. Get framework name
    2. Get framework lifetime
    3. Generate metrics with framework lifetime
    4. Save CSV with metrics

    framework_name|issues_lifetime_median|issues_lifetime_average|issues_lifetime_standard_deviation
    """
    metrics = [process_issues_csv(file) for file in _issues_csv]
    metrics = pd.concat(metrics)

    metrics.to_csv(METRICS_FPATH.joinpath('issues-metrics.csv'), encoding='utf-8', index=False)


if __name__ == '__main__':
    get_files()
    consolidate_repos_csv()
    consolidate_issues_csv()
