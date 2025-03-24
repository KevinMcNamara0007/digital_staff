import json

import requests


async def get_headers():
    token = "token"
    bear = "Bearer " + token
    headers = {
        "Content-Type": "application/json",
        "Authorization": bear
    }
    return headers


async def get_issue(jira_id):
    url = f"/{jira_id}"
    header = get_headers()
    response = requests.request("GET", url)
    return response.json()

async def get_epic(epic_key):
    url = f"/{epic_key}"
    header = get_headers()
    response = requests.request("GET", url)
    return response.json()

async def create_issue(jira_payload):
    url = f""
    header = get_headers()
    response = requests.request("POST", url, data=jira_payload)
    return response.json()

async def edit_issue(jira_id, jira_payload):
    url = f"/{jira_id}"
    header = get_headers()
    response = requests.request("PUT", url, data=json.dumps(jira_payload))
    return response.json()

async def add_issue_worklog(jira_id, jira_payload):
    url = f"/{jira_id}/worklog"
    header = get_headers()
    response = requests.request("PUT", url, data=json.dumps(jira_payload))
    return response.json()

async def get_project(project_id, field=None, date_start=None, date_end=None):
    url = "/search"

    jql_query = f'project = {project_id} AND type = Story'

    if date_start is not None and date_start != "":
        jql_query = jql_query + f" AND created >= \"{date_start}\""

    if date_end is not None and date_end != "":
        jql_query = jql_query + f" AND created >= \"{date_end}\""

    fields = 'summary, description, customfield, labels, components, created, updated, worklog, status, timetracking, assignee'
    if field is not None:
        fields = fields + f", {field}"

    query = {
        'jql': jql_query,
        'maxResults': 1000,
        'fields': fields
    }

    try:
        response = requests.request("GET", url, params=query)
        project_issues = response.json()['issues']
        total_issues = response.json()['total']
        # REVIEW AND FIX THIS CODE FOR OPTIMIZATION IN FUTURE
        while len(project_issues) < total_issues:
            query['startAt'] = len(project_issues)
            subsequent_response = requests.request("GET", url, params=query)
            for issue in subsequent_response.json()['issues']:
                project_issues.append(issue)
        return project_issues
    except Exception as e:
        return e

async def get_issues_for_epic(epic_key,date_start=None, date_end=None):
    url = f"epic/{epic_key}/issue"

    jql_query = f'type = Story'

    if date_start is not None and date_start != "":
        jql_query = jql_query + f" AND created >= \"{date_start}\""

    if date_end is not None and date_end != "":
        jql_query = jql_query + f" AND created >= \"{date_end}\""

    fields = 'summary, description, customfield, labels, components, created, updated, worklog, status, timetracking, assignee'

    query = {
        'jql': jql_query,
        'maxResults': 1000,
        'fields': fields
    }

    try:
        response = requests.request("GET", url, params=query)
        epic_issues = response.json()['issues']
        total_issues = response.json()['total']
        # REVIEW AND FIX THIS CODE FOR OPTIMIZATION IN FUTURE
        while len(epic_issues) < total_issues:
            query['startAt'] = len(epic_issues)
            subsequent_response = requests.request("GET", url, params=query)
            for issue in subsequent_response.json()['issues']:
                epic_issues.append(issue)
        return epic_issues
    except Exception as e:
        return e


async def get_project_components(project_id):
    url = f"project/{project_id}/components"

    try:
        response = requests.request("GET", url)
        return response.json()
    except Exception as e:
        return e

async def create_component(jira_payload):
    url = f"/component"

    try:
        response = requests.request("POST", url, data=jira_payload)
        return response.json()
    except Exception as e:
        return e