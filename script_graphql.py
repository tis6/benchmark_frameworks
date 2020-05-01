import requests
import time
import csv

headers = {"Authorization": "token ###"}


class Repository:
    def __init__(self, owner, name, merged_pull_requests, created_at, total_releases, total_closed_issues, closed_issues):
        self.owner = owner
        self.name = name
        self.merged_pull_requests = merged_pull_requests
        self.created_at = created_at
        self.total_releases = total_releases
        self.total_closed_issues = total_closed_issues
        self.closed_issues = closed_issues


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
  # TODO - Mudar pra pegar independente de repos
  queryBase = """
    {
    repository(owner: "%s", name: "%s") {
        mergedPullRequests: pullRequests(states: MERGED) {
        totalCount
        }
        createdAt
        releases {
        totalCount
        }
        totalIssuesFechada: issues(states:CLOSED){
            totalCount
        }
     }
    }""" % (owner, name)

  queryResultBase = run_query(queryBase)

  total_merged_pull_requests = queryResultBase['data']['repository']['mergedPullRequests']['totalCount']
  created_at = queryResultBase['data']['repository']['createdAt']
  total_releases = queryResultBase['data']['repository']['releases']['totalCount']
  total_closed_issues = queryResultBase['data']['repository']['totalIssuesFechada']['totalCount']

  repo = Repository(owner, name, total_merged_pull_requests,
                    created_at, total_releases, total_closed_issues, [])

  # 2) Buscar as issues do repository (loop)

  endCursor = "null"  # Proxima pagina
  closed_issues = []

  interval = total_closed_issues//50
  print('Iniciando buscas das issues, numero de repeticoes:' + str(interval))
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
    querySize = len(queryResultIssue['data']['repository']['issues']['nodes'])
    # Pega o endCursor aka proxima pagina
    endCursor = '"{}"'.format(
        queryResultIssue['data']['repository']['issues']['pageInfo']['endCursor'])

    # Monta e adiciona o obj de issue em uma lista
    for y in range(querySize):
          number = queryResultIssue['data']['repository']['issues']['nodes'][y]['number']
          title = queryResultIssue['data']['repository']['issues']['nodes'][y]['title']
          created_at = queryResultIssue['data']['repository']['issues']['nodes'][y]['createdAt']
          closed_at = queryResultIssue['data']['repository']['issues']['nodes'][y]['closedAt']

          new_issue_from_query = Issue(number, title, created_at, closed_at)

          # Salva os nodes no array de nodes
          closed_issues.append(new_issue_from_query)

    if x % 10 == 0:
      print('Loop:' + str(x))

  repo.closed_issues = closed_issues
  return repo

# Escreve em um arquivo csv


def writeCsv(repo, name):
  file_infos = "/Users/Rafael/Desktop/benchmark_frameworks/csv_github/repos_graphql_%s.csv" % name
  with open(file_infos, 'w', encoding="utf-8") as new_file_info:

    fnames = [
        'owner',
        'name',
        'created_at',
        'merged_pull_requests',
        'total_releases',
        'total_closed_issues']

    csv_writer = csv.DictWriter(new_file_info, fieldnames=fnames)
    csv_writer.writeheader()
    csv_writer.writerow(
            {
                'owner': repo.owner,
                'name': repo.name,
                'created_at': repo.created_at,
                'merged_pull_requests': repo.merged_pull_requests,
                'total_releases': repo.total_releases,
                'total_closed_issues': repo.total_closed_issues
            })

    print('Arquivo csv infos gerado com sucesso!')

  print('Iniciando geração do csv de issues')
  file_issues = "/Users/Rafael/Desktop/benchmark_frameworks/csv_github/repos_graphql_%s_issues.csv" % name
  with open(file_issues, 'w', encoding="utf-8") as new_file_issues:
        fnames = [
                'number',
                'title',
                'created_at',
                'closed_at']

        csv_writer = csv.DictWriter(new_file_issues, fieldnames=fnames)
        csv_writer.writeheader()

        for issue in repo.closed_issues:
             csv_writer.writerow(
                    {
                        'number': issue.number,
                        'title': issue.title,
                        'created_at': issue.created_at,
                        'closed_at': issue.closed_at,
                    })

        print('Arquivo csv issues gerado com sucesso!')

owners = ['expressjs', 'gin-gonic', 'django', 'rails', 'playframework', 'ktorio', 'dotnet', 'spring-projects', 'vapor', 'laravel']
names = ['express', 'gin', 'django', 'rails', 'playframework', 'ktor', 'core', 'spring-framework', 'vapor', 'laravel']



for x in range(10):
    repo = mine(owners[x], names[x])
    writeCsv(repo, names[x])
