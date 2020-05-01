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

#Minera os repositórios
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
  total_releases =   queryResultBase['data']['repository']['releases']['totalCount']
  total_closed_issues =  queryResultBase['data']['repository']['totalIssuesFechada']['totalCount']

  repo = Repository(owner, name, total_merged_pull_requests, created_at, total_releases, total_closed_issues, [])
 

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
    endCursor = '"{}"'.format(queryResultIssue['data']['repository']['issues']['pageInfo']['endCursor'])

    # Monta e adiciona o obj de issue em uma lista
    for y in range(querySize):
          number = queryResultIssue['data']['repository']['issues']['nodes'][y]['number']
          title = queryResultIssue['data']['repository']['issues']['nodes'][y]['title']
          created_at = queryResultIssue['data']['repository']['issues']['nodes'][y]['createdAt']
          closed_at = queryResultIssue['data']['repository']['issues']['nodes'][y]['closedAt']

          new_issue_from_query = Issue(number, title, created_at, closed_at)

          # Salva os nodes no array de nodes
          closed_issues.append(new_issue_from_query)
    
    if x%10 == 0:
      print('Loop:' + str(x))
  

  repo.closed_issues = closed_issues
  return repo

# Escreve em um arquivo csv
def writeCsv(nodes):
  with open("/Users/Rafael/Desktop/labex/repos.csv", 'w') as new_file:

    fnames = [
        'name_with_owner',
        'url',
        'created_at',
        'updated_at',
        'merged_pull_requests',
        'releases',
        'primary_language',
        'total_issues',
        'total_issues_closed']

    csv_writer = csv.DictWriter(new_file, fieldnames=fnames)
    csv_writer.writeheader()
    for node in nodes:
        csv_writer.writerow(
            {
                'name_with_owner': node['nameWithOwner'],
                'url': node['url'],
                'created_at': node['createdAt'],
                'updated_at': node['updatedAt'],
                'merged_pull_requests': node['pullRequests']['totalCount'],
                'releases': node['releases']['totalCount'],
                'primary_language': node['primaryLanguage']['name'] if node['primaryLanguage']!= None else 'null',
                'total_issues': node['numeroTotalIssues']['totalCount'],
                'total_issues_closed': node['numeroTotalIssuesClosed']['totalCount'],
            })

    print('Arquivo csv gerado com sucesso!')


repo = mine("expressjs", "express")
print(repo.owner)
print(repo.name)
print(repo.merged_pull_requests)
print(repo.created_at)
print(repo.total_releases)
print(repo.total_closed_issues)

print(repo.closed_issues[0].number)
print(repo.closed_issues[0].title)
print(repo.closed_issues[0].created_at)
print(repo.closed_issues[0].closed_at)

# writeCsv(nodes)