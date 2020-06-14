import requests
import time
import csv

headers = {"Authorization": "token ###"}


class Repository:
    def __init__(self, owner, name, assignable_users, created_at, forkCount,
                 hasIssuesEnabled, url, homepageUrl, isPrivate,
                 total_issues, total_closed_issues, closed_issues,
                 languages, primaryLanguage, total_pull_requests, merged_pull_requests,
                 releases, stargazers, updated_at, vulnerability_alerts, watchers):
        self.owner = owner
        self.name = name
        self.assignable_users = assignable_users
        self.created_at = created_at
        self.forkCount = forkCount
        self.hasIssuesEnabled = hasIssuesEnabled
        self.url = url
        self.homepageUrl = homepageUrl
        self.isPrivate = isPrivate
        self.total_issues = total_issues
        self.total_closed_issues = total_closed_issues
        self.closed_issues = closed_issues
        self.languages = languages
        self.primaryLanguage = primaryLanguage
        self.total_pull_requests = total_pull_requests
        self.merged_pull_requests = merged_pull_requests
        self.releases = releases
        self.stargazers = stargazers
        self.updated_at = updated_at
        self.vulnerability_alerts = vulnerability_alerts
        self.watchers = watchers


class Issue:
    def __init__(self, number, title, created_at, closed_at):
        self.number = number
        self.title = title
        self.created_at = created_at
        self.closed_at = closed_at


def run_query(query):
    request = requests.post('https://api.github.com/graphql',
                            json={'query': query}, headers=headers)
    while (request.status_code == 502):
        time.sleep(2)
        request = requests.post(
            'https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(
            request.status_code, query))

# Minera os repositórios


def mine(owner, name):
    # 1) Buscar os dados base que não precisam de loop
    queryBase = """
    {
    repository(owner: "%s", name: "%s") {
        assignableUsers {
        totalCount
        }
        createdAt
        forkCount
        hasIssuesEnabled
        url
        homepageUrl
        isPrivate
        issues_totais: issues {
        totalCount
        }
        issues_fechadas: issues(states: CLOSED) {
        totalCount
        }
        languages {
        totalCount
        }
        primaryLanguage {
        name
        }
        total_pull_requests: pullRequests {
        totalCount
        }
        merged_pull_requests: pullRequests(states: MERGED) {
        totalCount
        }
        releases {
        totalCount
        }
        stargazers {
        totalCount
        }
        updatedAt
        vulnerabilityAlerts {
        totalCount
        }
        watchers {
        totalCount
        }       
     }
    }""" % (owner, name)

    queryResultBase = run_query(queryBase)

    assignable_users = queryResultBase['data']['repository']['assignableUsers']['totalCount']
    created_at = queryResultBase['data']['repository']['createdAt']
    fork_count = queryResultBase['data']['repository']['forkCount']
    hasIssuesEnabled = queryResultBase['data']['repository']['hasIssuesEnabled']
    url = queryResultBase['data']['repository']['url']
    homepageUrl = queryResultBase['data']['repository']['homepageUrl']
    isPrivate = queryResultBase['data']['repository']['isPrivate']
    total_issues = queryResultBase['data']['repository']['issues_totais']['totalCount']
    total_closed_issues = queryResultBase['data']['repository']['issues_fechadas']['totalCount']
    languages = queryResultBase['data']['repository']['languages']['totalCount']
    primaryLanguage = queryResultBase['data']['repository']['primaryLanguage']['name']
    total_pull_requests = queryResultBase['data']['repository']['total_pull_requests']['totalCount']
    total_merged_pull_requests = queryResultBase['data']['repository']['merged_pull_requests']['totalCount']
    total_releases = queryResultBase['data']['repository']['releases']['totalCount']
    stargazers = queryResultBase['data']['repository']['stargazers']['totalCount']
    updatedAt = queryResultBase['data']['repository']['updatedAt']
    vulnerabilityAlerts = queryResultBase['data']['repository']['vulnerabilityAlerts']['totalCount']
    watchers = queryResultBase['data']['repository']['watchers']['totalCount']

    repo = Repository(owner, name, assignable_users,
                      created_at, fork_count, hasIssuesEnabled, url,
                      homepageUrl, isPrivate, total_issues, total_closed_issues, [],
                      languages, primaryLanguage, total_pull_requests, total_merged_pull_requests, total_releases,
                      stargazers, updatedAt, vulnerabilityAlerts, watchers)

    # 2) Buscar as issues do repository (loop)

    endCursor = "null"  # Proxima pagina
    closed_issues = []

    interval = total_closed_issues//50
    if interval == 0:
        interval = 1

    print('Iniciando buscas das issues do repositorio: %s, numero de repeticoes:' %
          repo.name + str(interval))
    for x in range(interval):
        # GraphQL query
        queryIssue = """
    {
        repository(owner: "%s", name: "%s") {
            issues(states: CLOSED, first: 50, after: %s) {
            pageInfo {
                endCursor
            }
            nodes {
                number
                title
                createdAt
                closedAt
            }
            }
         }
    }
    """ % (owner, name, endCursor)

        # O resultado da query que contem a proxima pagina e os nodes
        queryResultIssue = run_query(queryIssue)
        querySize = len(queryResultIssue['data']
                        ['repository']['issues']['nodes'])
        # Pega o endCursor aka proxima pagina
        endCursor = '"{}"'.format(
            queryResultIssue['data']['repository']['issues']['pageInfo']['endCursor'])

        # Monta e adiciona o obj de issue em uma lista
        for y in range(querySize):
            number = queryResultIssue['data']['repository']['issues']['nodes'][y]['number']
            title = queryResultIssue['data']['repository']['issues']['nodes'][y]['title']
            created_at = queryResultIssue['data']['repository']['issues']['nodes'][y]['createdAt']
            closed_at = queryResultIssue['data']['repository']['issues']['nodes'][y]['closedAt']

            # Filtra as issues apenas de um ano atrás
            if(int(created_at.rsplit('-')[0]) >= 2019):
                new_issue_from_query = Issue(
                    number, title, created_at, closed_at)

                # Salva os nodes no array de nodes
                closed_issues.append(new_issue_from_query)

        if x % 10 == 0:
            print('Loop:' + str(x))
    repo.closed_issues = closed_issues
    return repo

# Escreve em um arquivo csv


def writeCsv(repo, name):
    file_infos = "/Users/Rafael/Desktop/benchmark_frameworks/github_metrics/repos_graphql_%s.csv" % name
    with open(file_infos, 'w', encoding="utf-8") as new_file_info:

        fnames = [
            'owner',
            'name',
            'assignable_users',
            'created_at',
            'fork_count',
            'has_issues_enabled',
            'url',
            'homepage_url',
            'is_private',
            'total_issues',
            'total_closed_issues',
            'languages',
            'primary_language',
            'total_pull_requests',
            'merged_pull_requests',
            'total_releases',
            'stargazers',
            'updated_at',
            'vulnerability_alerts',
            'watchers'
        ]

        csv_writer = csv.DictWriter(new_file_info, fieldnames=fnames)
        csv_writer.writeheader()
        csv_writer.writerow(
            {
                'owner': repo.owner,
                'name': repo.name,
                'assignable_users': repo.assignable_users,
                'created_at': repo.created_at,
                'fork_count': repo.forkCount,
                'has_issues_enabled': repo.hasIssuesEnabled,
                'url': repo.url,
                'homepage_url': repo.homepageUrl,
                'is_private': repo.isPrivate,
                'total_issues': repo.total_issues,
                'total_closed_issues': repo.total_closed_issues,
                'languages': repo.languages,
                'primary_language': repo.primaryLanguage,
                'total_pull_requests': repo.total_pull_requests,
                'merged_pull_requests': repo.merged_pull_requests,
                'total_releases': repo.releases,
                'stargazers': repo.stargazers,
                'updated_at': repo.updated_at,
                'vulnerability_alerts': repo.vulnerability_alerts,
                'watchers': repo.watchers,

            })

        print('Arquivo csv infos gerado com sucesso!')

    print('Iniciando geração do csv de issues')
    file_issues = "/Users/Rafael/Desktop/benchmark_frameworks/github_metrics/repos_graphql_%s_issues.csv" % name
    with open(file_issues, 'w', encoding="utf-8") as new_file_issues:
        fnames = [
            'number',
            'created_at',
            'closed_at']

        csv_writer = csv.DictWriter(new_file_issues, fieldnames=fnames)
        csv_writer.writeheader()

        for issue in repo.closed_issues:
            csv_writer.writerow(
                {
                    'number': issue.number,
                    'created_at': issue.created_at,
                    'closed_at': issue.closed_at,
                })

        print('Arquivo csv issues gerado com sucesso!')



# owners = ['angular', 'expressjs',  'dotnet', 'vuejs', 'angular', 'django', 'pallets', 'laravel', 'rails', 'symfony', 'gatsbyjs']
# names = ['angular', 'express',  'aspnetcore', 'vue','angular.js', 'django', 'flask', 'laravel', 'rails', 'symfony', 'gatsby']


owners = ['laravel']
names = ['laravel']

for x in range(len(owners)):
    repo = mine(owners[x], names[x])
    writeCsv(repo, names[x])
