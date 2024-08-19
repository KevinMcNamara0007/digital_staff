from constants import *

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": "bearer token"
}


def get_issue(jira_id):
    url = f"{JIRA_DOMAIN}/rest/api/2/issue/{jira_id}"
    response = requests.request("GET", url, headers=headers)
    return response.json()


def edit_issue(jira_id, jira_payload):
    url = f"{JIRA_DOMAIN}/rest/api/2/issue/{jira_id}"
    try:
        response = requests.request("PUT", url, data=json.dumps(jira_payload), headers=headers)
        return response.status_code
    except Exception as e:
        return e
    

def add_issue_worklog(jira_id, jira_payload):
    url = f"{JIRA_DOMAIN}/rest/api/2/issue/{jira_id}/worklog"
    try:
        response = requests.request("POST", url, data=json.dumps(jira_payload), headers=headers)
        return response.status_code
    except Exception as e:
        return e
    

def get_project(project_id, field=None, year=None, quarter=None, epic=None):
    url = "{JIRA_DOMAIN}/rest/api/2/search"

    jql_query = f'project = {project_id} AND type = Story'

    if year is not None:
        jql_query += f' AND summary ~ \"{year}\"'

    if quarter is not None:
        jql_query += f' AND summary ~ \"{quarter}\"'

    if epic is not None:
        jql_query += f' AND summary ~ \"{epic}\"'

    jql_query += " ORDER by key"

    fields = 'summary, description, customfield_12513, labels, components, created, worklog, status, timetracking'

    if field is not None:
        fields += f', {field}'

    query = {
        'jql': jql_query,
        'maxResults': 1000,
        'fields': fields
    }

    try:
        response = requests.request("GET", url, params=query, headers=headers)
        return response.json()
    
    except Exception as e:
        return e
