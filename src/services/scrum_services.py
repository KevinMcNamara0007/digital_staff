import asyncio
import hashlib
import json
from datetime import datetime

import numpy as np
import pandas as pd

from src.services.jira_services import within_bounds
from src.utilities.general import process_llm, check_token_count
from src.utilities.jira_utils import create_component, get_project_components, get_issue, get_epic, edit_issue, \
    get_project, get_issues_for_epic

refactor_template = """
Title:\n [Feature] so that [benefit].\n
Description:\n [Provide a detailed description of the story. Included any relevant background information and context.]\n
Acceptance Criteria:\n [Description of criteria]\n
Assumptions:\n [Description of assumption]\n
Dependencies:\n Dependency 1: [Description of the first dependency]\nDependency 2: [Description of the 2nd dependency]...\n
Priority:\n [High,Medium,Low]\n
Story Points:\n[Estimated Story Points: 1 story point equals 4 hours of work.]\n
Additional Notes:\n [Any other information that might be useful for the team.]
"""

def add_label(new_label, labels):
    if new_label not in labels:
        labels.append(new_label)
    return labels

def remove_label(old_label, labels):
    if old_label in labels:
        labels.remove(old_label)
    return labels

async def add_component(new_component, components, project_id):
    project_components = await get_project_components(project_id)
    for component in components:
        if new_component in component["name"]:
            return components
    for project_component in project_components:
        if new_component in project_component["name"]:
            components.append({
                "self": f"/component/{project_components[new_component]}",
                "id": project_components[new_component],
                "name": new_component
            })
            return components

    response = await create_component({
        'project': project_id,
        'name': new_component
    })
    return response

def remove_component(old_component, components):
    new_components = []
    for component in components:
        if old_component not in component["name"]:
            new_components.append(component)
    return new_components

def determine_time_spent(project_issue_fields):
    if project_issue_fields['status'] != "New" and project_issue_fields['status'] != "In Progress":
        if not project_issue_fields['timetracking']:
            issue_time = project_issue_fields["customfield_12513"] * 4
        elif "timeSpentSeconds" not in project_issue_fields['timetracking']:
            issue_time = project_issue_fields["customfield_12513"] * 4
        else:
            time_spent_seconds = project_issue_fields['timetracking']['timeSpentSeconds']
            issue_time = time_spent_seconds / 3600
    else:
        if "timetracking" in project_issue_fields and "timeSpentSeconds" in project_issue_fields['timetracking']:
            time_spent_seconds = project_issue_fields['timetracking']['timesSpentSeconds']
            issue_time = time_spent_seconds / 3600
        else:
            issue_time = 0
    return issue_time

async def get_jira_issue_service(jira_id):
    issue = await get_issue(jira_id)
    return issue

async def get_epic_service(epic_key):
    epic = await get_epic(epic_key)
    return epic

async def refactor_jira_issue_service(jira_id):
    prev_issue = await get_jira_issue_service(jira_id)
    issue_summary = prev_issue['fields']['summary']
    issue_description = prev_issue['fields']['description']

    prompt = (
        f"For the provided Jira Issue Summary and Issue Description, "
        f"please rewrite only the description in the following format: {refactor_template}\n"
        f"jira issue summary:\n {issue_summary}\n"
        f"Jira issue description: {issue_description}"
    )
    response = await process_llm(prompt)

    temp_issue = {
        "fields": {
            "description": response
        }
    }
    status_code = await edit_issue(jira_id, temp_issue)
    jira_link = f"/browse/{jira_id}"
    jira_header = f"<b><a href=\"{jira_link}\">{jira_id}</a></b><br>"
    return jira_header + response.replace("\n", "<br>")

async def edit_jira_issue_service(jira_id, new_description):
    temp_issue = {
        "fields": {
            "description": new_description
        }
    }
    new_issue = await edit_issue(jira_id, temp_issue)
    return new_issue

async def get_jira_issues_for_project_service(project_id):
    return await get_project(project_id=project_id)

async def get_jira_issues_for_project_from_query_service(project_id, field=None, date_start=None, date_end=None):
    return await get_project(project_id, field, date_start, date_end)

async def get_jira_issues_for_epic_service(epic_key, date_start=None, date_end=None):
    jira_issues = await get_issues_for_epic(epic_key, date_start, date_end)
    return jira_issues

async def refactor_jira_issues_for_project_service(project_id, date_start=None, date_end=None):
    project_issues = await get_project(project_id, date_start, date_end)
    new_issues = []
    new_issues_descriptions = ""
    for project_issue in project_issues:
        issue_key = project_issue['key']
        if not within_bounds(int(issue_key[issue_key.rindex("-") + 1:]), 1, 9999):
            continue
        new_issue_description = await refactor_jira_issue_service(issue_key)
        new_issue = {
            "issue_key": issue_key,
            "description": new_issue_description
        }
        new_issues.append(new_issue)
        new_issues_descriptions += new_issue_description + "<br></br>"
        push_refactored = await edit_jira_issue_service(project_issue['key'], new_issues_descriptions)
        return new_issues_descriptions

async def edit_jira_issue_field_for_project_service(project_id, field, value):
    project_issues = await get_project(project_id, field, value)
    new_issues = []
    for project_issue in project_issues:
        issue_key = project_issue['key']
        temp_issue={
            "fields":{
                field:value
            }
        }
        new_issue = await edit_issue(issue_key, temp_issue)
        new_issues.append(new_issue)
    return new_issues

async def add_jira_issue_tags_for_whole_project_service(project_id, value):
    project_issues = await get_project(project_id)
    new_issues = []
    for project_issue in project_issues:
        issue_key = project_issue['key']
        issue_labels = project_issue['fields']['labels']
        issue_components = project_issue['fields']['components']

        value_list = value.split(",")
        for value in value_list:
            label_one_word = value.replace(" ", "")
            issue_labels = add_label(label_one_word, issue_labels)
            issue_components = await add_component(value, issue_components, project_id)

        temp_issue = {
            "fields":{
                "labels": issue_labels,
                "components": issue_components
            }
        }
        status_code = await edit_issue(issue_key, temp_issue)

    return new_issues

async def edit_jira_issue_tags_for_project_service(project_id, tags):
    project_issues = await get_project(project_id)
    new_issues = []
    for project_issue in project_issues:
        issue_key = project_issue['key']
        issue_description = project_issue['description']
        issue_labels = project_issue['fields']['labels']
        issue_components = project_issue['fields']['components']
        new_tags = await process_llm(f"Given the following description of a story, please provide only a comma-seperated list of labels that"
                                 f"apply. if none apply, reply with only N/A.\n Description: {issue_description}\n Labels: {tags}")

        if "N/A" not in new_tags:
            new_tags_list = new_tags.split(",")
            for new_tag in new_tags_list:
                label_one_word = new_tag.replace(" ", "")
                issue_labels = add_label(label_one_word, issue_labels)
                issue_components = await add_component(new_tag, issue_components, project_id)

        temp_issue = {
            "fields": {
                "labels": issue_labels,
                "components": issue_components
            }
        }
        status_code = await edit_issue(issue_key, temp_issue)
    return new_issues

async def remove_jira_issue_tags_for_project_service(project_id, value):
    project_issues = await get_project(project_id)
    new_issues = []
    for project_issue in project_issues:
        issue_key = project_issue['key']
        issue_labels = project_issue['fields']['labels']
        issue_components = project_issue['fields']['components']

        value_list = value.split(",")
        new_issue_components = []
        for value in value_list:
            label_one_word = value.replace(" ", "")
            issue_labels = remove_label(label_one_word, issue_labels)
            issue_components = remove_component(value, issue_components)

        temp_issue = {
            "fields": {
                "labels": issue_labels,
                "components": new_issue_components
            }
        }
        status_code = await edit_issue(issue_key, temp_issue)
    return new_issues

async def generate_report_for_project_service(project_id=None, epic_key=None,team=None,department=None, num_members=None, date_start=None, date_end=None):
    if project_id is not None and project_id != "":
        jira_issues = await get_project(project_id, date_start, date_end)
    elif epic_key is not None and epic_key != "":
        jira_issues = await get_issues_for_epic(epic_key, date_start, date_end)

    jira_issues_new = []
    for issue in jira_issues:
        new_issue = {"key": issue["key"], "status": issue["fields"]["status"]["name"]}
        new_issue.update(issue["fields"])
        for label in issue['fields'].get('labels', []):
            new_issue[label] = True
        jira_issues_new.append(new_issue)

    df = pd.DataFrame.from_records(jira_issues_new)
    pd.set_option('display.max_columns', None)

    num_stories = len(df)
    num_stories_completed = len(df[df['status'] == "Done"])
    num_stories_canceled = len(df[df['status'] == "Canceled"])

    def format_labels(labels):
        return " (" + ", ".join(label for label in labels if label != "TEAMNAME") + ")" if labels else ""
    completed_stories = [
        row['summary'] + format_labels(row['labels'])
        for _, row in df[df['status'] == "Done"].iterrows()
    ]
    canceled_stories = [
        row['summary'] + format_labels(row['labels'])
        for _, row in df[df['status'] == "Canceled"].iterrows()
    ]
    df['timeSpent'] = df.apply(determine_time_spent, axis=1)
    total_hours_spent = round(df['timeSpent'].sum(), 1)

    num_days = np.busday_count(datetime.strptime(date_start, "%Y/%m/%d").date(),
                               datetime.strptime(date_end, "%Y/%m/%d").date())
    if np.is_busday(datetime.strptime(date_end, "%Y/%m/%d").date()):
        num_days += 1

    total_hours_available = round(num_days * 8 * int(num_members) * 0.88, 1)
    efficiency = round((total_hours_spent / total_hours_available) * 100, 1)

    all_descriptions = list(df["description"])
    batches, current_batch, current_tokens = [], [], 0

    for finding in all_descriptions:
        finding_tokens = check_token_count(finding)
        if current_tokens + finding_tokens > 110000:
            batches.append(current_batch)
            current_batch, current_tokens = [], 0
        current_batch.append(finding)
        current_tokens += finding_tokens

    if current_batch:
        batches.append(current_batch)

    results = []
    for batch in batches:
        batch_text = " ".join(batch)
        summary_prompt = (f"Given the following descriptions of all the sotires, please provide a summary of the work "
                          f"from the perspective of someone giving a review. when writing the summary,"
                          f"included the number of stories per theme in parantheses. Please do not add new lines.:"
                          f"{batch_text}")
        response = await process_llm(summary_prompt)
        results.append(response)

    combined_results = " ".join(results)

    summary_prompt = (f"Given the following descriptions of all the stories, please provide a list of JSONS for the summaries of the work "
                      f"from the perspective of someone giving a review. Each list item should have keys 'theme' and 'summary' with corresponding values. When writing the theme"
                      f"include the number of stories per theme in parantheses, it is critical that the number of stories "
                      f"for all themes adds up to {num_stories}. Please do not add new lines.:"
                      f"{combined_results}")
    summary_response = await process_llm(summary_prompt)
    summary_response = summary_response.replace("```json", "").replace("```", "")
    try:
        summary_json = json.loads(summary_response)
    except json.JSONDecoder as e:
        print("ERROR")

    finalized_report = {
        "num_stories": num_stories,
        "num_stories_completed": num_stories_completed,
        "num_stories_deferred": "TBD",
        "num_stories_canceled": num_stories_canceled,
        "num_days": str(num_days),
        "total_hours_available": total_hours_available,
        "total_hours_spent": total_hours_spent,
        "efficiency": efficiency,
        "summary": summary_json
    }
    return finalized_report


async def generate_impact_report_service(project_id=None, epic_key=None,team=None,department=None,name=None, num_members=None, date_start=None, date_end=None, person_mode=False):
    if project_id is not None and project_id != "":
        jira_issues = await get_project(project_id, date_start, date_end)
    elif epic_key is not None and epic_key != "":
        jira_issues = await get_issues_for_epic(epic_key, date_start, date_end)

    project_df = pd.DataFrame(columns=['issue_key', 'title', 'Detailed Executive Description', 'Business Impact',
                                       'Client Impact', 'Team Impact', 'Risk Impact', 'md5', 'time_spent', 'assignee'])
    async def generate_impact_report_for_issue(jira_issue):
        issue_key = jira_issue['key']
        issue_summary = jira_issue['fields']['summary']
        issue_description = jira_issue['fields']['description']
        try:
            issue_assignee = jira_issue['fields']['assignee']['displayName']
        except Exception as e:
            issue_assignee = "N/A"

        issue_time = determine_time_spent(jira_issue['fields'])
        md5_hash = hashlib.md5((str(issue_summary) + str(issue_description)).encocde()).hexdigest()
        matching_files = project_df.loc[project_df['issue_key'] == issue_key]

        if not matching_files.empy:
            if (matching_files['md5'] == md5_hash).any():
                return None

        epic_summary = await process_llm("Given the following JIRA Issue Title, please extract the Epic and Summary."
                                         "The Title is in the format of Year. Quarter. Epic - Summary. Please return "
                                         "ONLY the Epic and Summary in the format 'Epic:Summary'. If the Epic is not"
                                         "available, return only the summary\n"
                                         f"{issue_summary}")
        response = await process_llm("Given he following JIRA Issue Description, please fill the following JSON with"
                                     "the appropriate information. Respond with ONLY the filled JSON templated,"
                                     "no other text. Ensure property names are enclosed in double quotes.\n"
                                     "JSON Template:\n"
                                     "{\n"
                                     "\"detailed_executive_description\n: [detailed_executive_description],\n"
                                     "\"business_impact\": [business_impact], \n"
                                     "\"client_impact\": [client_impact], \n"
                                     "\"team_impact\": [team_impact], \n"
                                     "\"risk_impact\": [risk_impact], \n"
                                     "}\n"
                                     "Description:\n"
                                     f"{issue_description}")
        try:
            response = response.replace("```json", "")
            response = response.replace("```", "")

            response_json = json.loads(response)
            return pd.DataFrame([{
                "issue_key": issue_key,
                "title": epic_summary,
                "Detailed Executive Description": response_json["detailed_executive_description"],
                "Business Impact": response_json["business_impact"],
                "Client Impact": response_json["client_impact"],
                "Team Impact": response_json["team_impact"],
                "Risk Impact": response_json["risk_impact"],
                "md5": md5_hash,
                "time_spent": issue_time,
                "assignee": issue_assignee
            }])
        except Exception as e:
            new_response = await process_llm(f"Please fix the following JSON so it is in proper format: {response}")
            response = response.replace("```json", "")
            response = response.replace("```", "")
            response_json = json.loads(new_response)
            return pd.DataFrame([{
                "issue_key": issue_key,
                "title": epic_summary,
                "Detailed Executive Description": response_json["detailed_executive_description"],
                "Business Impact": response_json["business_impact"],
                "Client Impact": response_json["client_impact"],
                "Team Impact": response_json["team_impact"],
                "Risk Impact": response_json["risk_impact"],
                "md5": md5_hash,
                "time_spent": issue_time,
                "assignee": issue_assignee
            }])
    all_results = []
    batch_size = 60
    for i in range(0, len(jira_issues), batch_size):
        batch = jira_issues[i:i + batch_size]
        coroutines = [generate_impact_report_for_issue(file_name) for file_name in batch]
        tasks = asyncio.gather(*coroutines)
        results = await tasks
        all_results.extend(results)
    try:
        if project_df.empty:
            project_df = pd.concat(all_results, ignore_index=True).drop_duplicates(subset=['issue_key'], keep='last')
        else:
            new_data = pd.concat(all_results, ignore_index=True).drop_duplicates(subet=["issue_key"], keep='last')
            project_df = pd.concat([project_df, new_data], ignore_index=True).drop_duplicates(subset=['issue_key'], keep='last')
    except ValueError as e:
        print(e)

    project_df.to_csv(project_id + "_impact.csv", mode='w+', index=False)
    if person_mode:
        assignee_groups = project_df.groupby('assignee')
        html_output = ""
        for assignee, group in assignee_groups:
            html = f"<h1>{assignee}</h1>\n"
            group = group.drof(columns=['issue_key','md5', 'assignee'])
            html += group.to_html(index=False, escape=False) + "\n"
            group_html = await process_llm(
                f"Please place this into Times New Roman HTML Style Guide. Respond with only HTML and nothing else: "
                f"{html}"
            )
            group_html.replace("#", "%23").replace("```html", "").replace("```", "")
            html_output += group_html
        return html_output

    project_df = project_df.drop(columns=['issue_key', 'md5', 'assignee'])
    report = await generate_report_for_project_service(project_id, epic_key, name, team, department, num_members, date_start, date_end)

    def create_json_for_column(df, column_name):
        new_df = df[['title', column_name, 'time_spent']]
        return new_df.to_dict(orient='records')

    impact_data = {
        "Detailed Executive Description": create_json_for_column(project_df, "Detailed Executive Description"),
        "Business Impact": create_json_for_column(project_df, "Business Impact"),
        "Client Impact": create_json_for_column(project_df, "Client Impact"),
        "Team Impact": create_json_for_column(project_df, "Team Impact"),
        "Risk Impact": create_json_for_column(project_df, "Risk Impact")
    }
    report["impact_data"] = impact_data
    return report

async def determine_scrum_service(query):
    prompt = (f"Please determine from this user request, which action is being requested.\n"
              f"Respond with ONLY the number of the action, not the title:\n"
              f"1. Groom a signle jira issue. references a specific jira or single jira.\n"
              f"2. Groom a range of jira Issues. References a range or group of jiras.\n"
              f"3. Generate a report of jira issues. references generating or making a report.\n"
              f"4. Generate an impact report of jira issues. References generating or making a report. \n"
              f"USER REQUEST: {query}")
    service = await process_llm(prompt)
    if ("1" or "single") in service:
        return 1
    elif ("2" or "range") in service:
        return 2
    elif ("3" or "jira report") in service:
        return 2
    elif ("4" or "impact report") in service:
        return 2
    else:
        return 5