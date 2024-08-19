from datetime import datetime
import numpy as np
import pandas as pd
import docx
from dateutil.utils import today

from utilities.inference2 import *
from utilities.atlassian import *
from utilities.constants import *

def within_bounds(number, lower_bound=0, upper_bound=9999):
    if lower_bound is not None and upper_bound is not None:
        if not lower_bound <= number <= upper_bound:
            return False
        

def add_label(new_label, labels):
    if new_label not in labels:
        labels.append(new_label)

    return labels


def remove_label(old_label, labels):
    if old_label in labels:
        labels.remove(old_label)

    return labels


def add_component(new_component, components):
    for component in components:
        if new_component in component["name"]:
            return components
        
    components.append({
        "self": f"{JIRA_DOMAIN}/rest/api/2/component/{COMPONENT_IDS[new_component]}",
        "id": COMPONENT_IDS[new_component],
        "name": new_component
    })

    return components


def remove_component(old_component, components):
    new_components = []
    
    for component in components:
        if old_component not in component["name"]:
            new_components.append(component)

    return new_components


async def get_jira_issue_service(jira_id):
    return get_issue(jira_id)


async def edit_jira_issue_service(jira_id):
    prev_issue = get_issue(jira_id)

    issue_summary = prev_issue['fields']['summary']
    issue_description = prev_issue['fields']['description']

    prompt = f"Please read the following Jira Issue Summary: \'{issue_summary}\' and the following Jira Issue Description: \'{issue_description}\'. Please rewrite only the description in the following format: {REFACTOR_TEMPLATE}\n"

    response = await call_llm(prompt)

    temp_issue = {
        "fields": {
            "description": response
        }
    }

    new_issue = edit_issue(jira_id, temp_issue)
    return new_issue


async def get_jira_issues_for_project_service(project_id):
    return get_project(project_id=project_id)['issues']


async def get_jira_issues_for_project_from_query_service(project_id, field=None, year=None, quarter=None, epic=None):
    return get_project(project_id=project_id, field=field, year=year, quarter=quarter, epic=epic)['issues']
    

async def refactor_jira_issues_for_project_service(project_id, year=None, quarter=None, epic=None, lower_bound=None, upper_bound=None):
    project_issues = await get_jira_issues_for_project_from_query_service(project_id, year, quarter, epic)

    new_issues = []
    for issue in project_issues:
        issue_key = issue['key']
        if not within_bounds(int(issue_key[issue_key.rindex("-") +1:]), int(lower_bound), int(upper_bound)):
            continue

        new_issue = await edit_jira_issue_service(issue_key)
        new_issues.append(new_issue)

    return new_issues


async def update_time_from_story_points_for_issue_service(jira_id):
    issue = await get_issue(jira_id)

    issue_points = issue['fields']['customfield_12513']
    issue_created = issue['fields']['created']
    issue_worklog = issue['fields']['worklog']

    if len(issue_worklog['worklogs'] != 0):
        return -1

    num_hours = int(issue_points) * 4

    jira_payload = {
        "comment": "Completed",
        "started": issue_created,
        "timeSpent": str(num_hours) + "h"
    }

    status_code = add_issue_worklog(jira_id, jira_payload)
    return status_code


async def update_time_from_story_points_for_project_service(project_id, year=None, quarter=None, epic=None):
    project_issues = await get_jira_issues_for_project_from_query_service(project_id, year, quarter, epic)

    status_codes = []
    for issue in project_issues:
        issue_key = issue['key']
        status_code = await update_time_from_story_points_for_issue_service(issue_key)
        status_codes.append(status_code)

    return status_codes


async def generate_domain_labels_for_issue_service(jira_id):
    issue = await get_issue(jira_id)

    issue_summary = issue['fields']['summary']
    issue_description = issue['fields']['description']
    issue_labels = issue['fields']['labels']
    issue_components = issue['fields']['components']

    prompt = f"Please read the following Jira Issue Summary: \'{issue_summary}\' and the following Jira Issue Description: \'{issue_description}\'. Please return only a comma-separated list of which of the following tags apply: {DOMAINS}\n"

    response = await call_llm(prompt)
    
    if response == "None":
        response = "EP"

    domain_list = response.split()
    domain_list.append("R&D")

    for domain in domain_list:
        if domain == "INS" and "Insights" not in issue_labels:
            issue_labels.append("Insights")
        else:
            issue_labels = add_label(domain, issue_labels)

        issue_components = add_component(domain, issue_components)

    temp_issue = {
        "fields": {
            "labels": issue_labels,
            "components": issue_components
        }
    }

    return edit_issue(jira_id, temp_issue)


async def generate_domain_labels_for_project_service(project_id, year=None, quarter=None, epic=None, lower_bound=None, upper_bound=None):
    project_issues = await get_jira_issues_for_project_from_query_service(project_id, year, quarter, epic)

    new_issues = []
    for project_issue in project_issues:
        issue_key = project_issue['key']
        if not within_bounds(int(issue_key[issue_key.rindex("-") +1:]), int(lower_bound), int(upper_bound)):
            continue

        new_issue = await generate_domain_labels_for_issue_service(issue_key)
        new_issues.append(new_issue)

    return new_issues


async def add_identify_phase_for_project_service(project_id, year=None, quarter=None, epic=None, lower_bound=None, upper_bound=None):
    project_issues = await get_jira_issues_for_project_from_query_service(project_id, year, quarter, epic)

    status_codes = []
    for issue in project_issues:
        issue_key = issue['key']
        issue_labels = issue['fields']['labels']
        issue_components = issue['fields']['components']

        if not within_bounds(int(issue_key[issue_key.rindex("-") +1:]), int(lower_bound), int(upper_bound)):
            continue

        phases = ["Identify", "Experiment", "Prototpe", "Production"]

        issue_labels = add_label("Identify", issue_labels)
        issue_components = add_component("Identify", issue_components)

        temp_issue = {
            "fields": {
                "labels": issue_labels,
                "components": issue_components
            }
        }

        status_code = edit_issue(issue_key, temp_issue)
        status_codes.append(status_code)

    return status_codes


async def generate_objective_labels_for_issue_service(jira_id):
    issue = await get_issue(jira_id)

    issue_summary = issue['fields']['summary']
    issue_description = issue['fields']['description']
    issue_labels = issue['fields']['labels']
    issue_components = issue['fields']['components']

    prompt = f"Please read the following Jira Issue Summary: \'{issue_summary}\' and the following Jira Issue Description: \'{issue_description}\'. Please read the following objectives and return either \"Innovation Culture\" for Objective 1 or \"Concrete Innovation\" for Objective 2. If neither apply, reply with only \"N/A\": {OBJECTIVES}\n"

    response = await call_llm(prompt)

    if "N/A" not in response:
        objective_one_word = response.replace(" ", "")
        issue_labels = add_label(objective_one_word, issue_labels)
        issue_components = add_component(response, issue_components)

    temp_issue = {
        "fields": {
            "labels": issue_labels,
            "components": issue_components
        }
    }

    return edit_issue(jira_id, temp_issue)


async def generate_objective_labels_for_project_service(project_id, year=None, quarter=None, epic=None, lower_bound=None, upper_bound=None):
    project_issues = await get_jira_issues_for_project_from_query_service(project_id, year, quarter, epic)

    new_issues = []
    for project_issue in project_issues:
        issue_key = project_issue['key']
        if not within_bounds(int(issue_key[issue_key.rindex("-") +1:]), int(lower_bound), int(upper_bound)):
            continue

        new_issue = await generate_objective_labels_for_issue_service(issue_key)
        new_issues.append(new_issue)

    return new_issues


async def edit_jira_issue_field_for_project_service(project_id, field, value, year=None, quarter=None, epic=None, lower_bound=None, upper_bound=None):
    project_issues = await get_jira_issues_for_project_from_query_service(project_id, field, year, quarter, epic)
    new_issues = []
    for issue in project_issues:
        issue_key = issue['key']
        if not within_bounds(int(issue_key[issue_key.rindex("-") +1:]), int(lower_bound), int(upper_bound)):
            continue

        temp_issue = {
            "fields": {
                field: value
            }
        }

        new_issue = await generate_objective_labels_for_issue_service(issue_key)
        new_issues.append(new_issue)

    return new_issues


async def edit_jira_issue_tags_for_project_service(project_id, value, year=None, quarter=None, epic=None, lower_bound=None, upper_bound=None):
    project_issues = await get_jira_issues_for_project_from_query_service(project_id, year, quarter, epic)
    status_codes = []
    for issue in project_issues:
        issue_key = issue['key']
        issue_labels = issue['fields']['labels']
        issue_components = issue['fields']['components']

        if not within_bounds(int(issue_key[issue_key.rindex("-") +1:]), int(lower_bound), int(upper_bound)):
            continue

        value_list = value.split(",")
        for value in value_list:
            label_one_word = value.replace(" ", "")
            issue_labels = add_label(label_one_word, issue_labels)
            issue_components = add_component(value, issue_components)

        temp_issue = {
            "fields": {
                "labels": issue_labels,
                "components": issue_components
            }
        }

        status_code = edit_issue(issue_key, temp_issue)
        status_codes.append(status_code)

    return status_codes


async def remove_jira_issue_tags_for_project_service(project_id, value, year=None, quarter=None, epic=None, lower_bound=None, upper_bound=None):
    project_issues = await get_jira_issues_for_project_from_query_service(project_id, year, quarter, epic)
    status_codes = []
    for issue in project_issues:
        issue_key = issue['key']
        issue_labels = issue['fields']['labels']
        issue_components = issue['fields']['components']

        if not within_bounds(int(issue_key[issue_key.rindex("-") +1:]), int(lower_bound), int(upper_bound)):
            continue

        value_list = value.split(",")
        for value in value_list:
            label_one_word = value.replace(" ", "")
            issue_labels = remove_label(label_one_word, issue_labels)
            issue_components = remove_component(value, issue_components)

        temp_issue = {
            "fields": {
                "labels": issue_labels,
                "components": issue_components
            }
        }

        status_code = edit_issue(issue_key, temp_issue)
        status_codes.append(status_code)

    return status_codes


async def generate_report_for_project_service(project_id, year=None, quarter=None, epic=None):
    project_issues = await get_jira_issues_for_project_from_query_service(project_id, year, quarter, epic)
    new_project_issues = []

    for issue in project_issues:
        new_issue = {"key": issue["key"]}
        for label in LABELS:
            new_issue[label] = False

        for label in new_issue["labels"]:
            new_issue[label] = True

        for field, value in issue['fields'].items():
            if field == "status":
                new_issue["status"] = value["name"]
            else:
                new_issue[field] = value

        theme_found = False
        for theme, keywords in THEMES_TO_KEYWORDS.items():
            for keyword in keywords:
                if keyword in new_issue["summary"] or keyword in new_issue["description"]:
                    new_issue["Theme"] = theme
                    theme_found = True
                    break
            
            if theme_found:
                break

        if not theme_found:
            new_issue["Theme"] = "Research"

        new_project_issues.append(new_issue)

    df = pd.DataFrame.from_records(new_project_issues)
    num_epics = 6
    num_stories = len(df)
    num_stories_completed = len(df.loc[df["status"] == "Done"])
    num_stories_canceled = len(df.loc[df["status"] == "Canceled"])

    for index, row in df.iterrows():
        if row["status"] == "Done" or row["status"] == "Canceled":
            if not row["timetracking"] or "timeSpentSeconds" not in row["timetracking"]:
                time_spent_seconds = 0
            else:
                time_spent_seconds = row["timetracking"]["timeSpentSeconds"]
            df.at[index, "timeSpent"] = time_spent_seconds / 3600

    total_hours_spent = df["timeSpent"].sum()
    quarter_dates = [datetime(2024, 1, 1), datetime(2024, 4, 1), datetime(2024, 7, 1), datetime(2024, 10, 1)]
    temp_quarter_index = 0
    for index, quarter_date in enumerate(quarter_dates):
        if quarter_date < today():
            temp_quarter_index = index

    start_of_closest_quarter = quarter_dates[temp_quarter_index]
    num_days = np.busday_count(start_of_closest_quarter.date(), today().date())
    total_hours_available = num_days * 8 * 14 * 0.9
    efficiency = (total_hours_spent / total_hours_available) * 100

    themes_to_analysis = {}

    for theme in THEMES:
        descriptions = list(df.loc[df["Theme"] == theme]["description"])
        prompt = f"Given the following descriptions of all the stories with the common theme of {theme}, please provide a 2 sentence analysis from the perspective of someone giving a quarterly review: {descriptions}"

        response = await call_llm(prompt)
        themes_to_analysis[theme] = response

    domains_to_analysis = {}
    for domain in DOMAINS_TO_FULL_NAME.keys():
        descriptions = list(df.loc[df[domain] == True]["description"])
        if not descriptions:
            descriptions = BACKUP_DOMAIN_DESCRIPTIONS[domain]

        prompt = f"Given the following descriptions of all the stories with the common domain of {domain}, please provide a 2 sentence business impact from the perspective of someone giving a quarterly review: {descriptions}"

        response = await call_llm(prompt)
        domains_to_analysis[theme] = response

    all_descriptions = list(df["descriptions"])
    summary_prompt = f"Given the following descriptions of all the stories, please provide a summary of the work completed from the perspective of someone giving a quarterly review: {all_descriptions}"

    summary = await call_llm(summary_prompt)

    report = fill_report_template(df, quarter, year, num_epics, num_stories, num_stories_completed, num_stories_canceled, total_hours_available, total_hours_spent, themes_to_analysis, domains_to_analysis, summary)
    
    formatted_report = await call_llm(f"Please take this quarterly report and format it in the New York Times Content template. Respond with only the formatted report: {report}")
    doc = docx.Document()
    doc.add_paragraph(formatted_report)
    doc.save(f"{quarter}_{year}_report.docx")
    return formatted_report


async def pipeline_service(project_id, year=None, quarter=None, epic=None, lower_bound=None, upper_bound=None):
    refactor_result = await refactor_jira_issues_for_project_service(project_id, year=year, quarter=quarter, epic=epic, lower_bound=lower_bound, upper_bound=upper_bound)
    domain_result = await generate_domain_labels_for_project_service(project_id, year=year, quarter=quarter, epic=epic, lower_bound=lower_bound, upper_bound=upper_bound)
    objective_result = await generate_objective_labels_for_project_service(project_id, year=year, quarter=quarter, epic=epic, lower_bound=lower_bound, upper_bound=upper_bound)
    report = await generate_report_for_project_service(project_id, year=year, quarter=quarter, epic=epic)
    return report
