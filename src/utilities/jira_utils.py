import requests


def get_issue(jira_id):
    url = ""
    headers = {}
    response = requests.request("GET", url, headers=headers)
    return response.json()


def get_project(project_id, field=None, year=None, quarter=None, epic=None, date_lower_bound=None, date_upper_bound=None):
    url = ""
    headers = {}
    jql_query = f'Project = {project_id} and type = Story'
    if year is not None and year != "":
        jql_query = jql_query + f'AND summary ~\"{year}\"'
    if quarter is not None and quarter != "":
        jql_query = jql_query + f'AND summary ~\"{quarter}\"'
    if epic is not None and epic != "":
        jql_query = jql_query + f'AND summary ~\"{epic}\"'
    jql_query = jql_query + " ORDER BY key"

    fields = 'summary, description, labels, components, created, updated, worklog'
    query = {
        'jql':jql_query,
        'maxResults':1000,
        'fields': fields
    }
    try:
        response = requests.request("GET", url, params=query, headers=headers)
        return response.json()
    except Exception as exc:
        return exc