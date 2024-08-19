from fastapi import FastAPI, Form, APIRouter

from services.jira_llm_service import *

app = APIRouter()

@app.get("/get_jira_issue/{jira_id}")
async def get_jira_issue(jira_id):
    return await get_jira_issue_service(jira_id)


@app.get("/edit_jira_issue/{jira_id}")
async def edit_jira_issue(jira_id):
    return await edit_jira_issue_service(jira_id)


@app.get("/get_jira_issues_for_project/{project_id}")
async def get_jira_issues_for_project(project_id):
    return await get_jira_issues_for_project_service(project_id)


@app.get("/get_jira_issues_for_project_from_query/{project_id}")
async def get_jira_issues_for_project_from_query(project_id, year=None, quarter=None, epic=None):
    return await get_jira_issues_for_project_from_query_service(project_id, year, quarter, epic)


@app.get("/refactor_jira_issues_for_project/{project_id}")
async def refactor_jira_issues_for_project(project_id, year=None, quarter=None, epic=None, lower_bound=None, upper_bound=None):
    return await refactor_jira_issues_for_project_service(project_id, year, quarter, epic, lower_bound, upper_bound)


@app.get("/update_time_from_story_points_for_issue/{jira_id}")
async def update_time_from_story_points_for_issue(jira_id):
    return await update_time_from_story_points_for_issue_service(jira_id)


@app.get("/update_time_from_story_points_for_project/{project_id}")
async def update_time_from_story_points_for_project(project_id, year=None, quarter=None, epic=None):
    return await update_time_from_story_points_for_project_service(project_id, year, quarter, epic)


@app.get("/generate_domain_labels_for_issue/{jira_id}")
async def generate_domain_labels_for_issue(jira_id):
    return await generate_domain_labels_for_issue_service(jira_id)


@app.get("/add_identify_phase_for_project/{project_id}")
async def add_identify_phase_for_project(project_id, year=None, quarter=None, epic=None, lower_bound=None, upper_bound=None):
    return await add_identify_phase_for_project_service(project_id, year, quarter, epic, lower_bound, upper_bound)


@app.get("/generate_domain_labels_for_project/{project_id}")
async def generate_domain_labels_for_project(project_id, year=None, quarter=None, epic=None, lower_bound=None, upper_bound=None):
    return await generate_domain_labels_for_project_service(project_id, year, quarter, epic, lower_bound, upper_bound)


@app.get("/edit_jira_issue_field_for_project/{project_id}")
async def edit_jira_issue_field_for_project(project_id, field, value, year=None, quarter=None, epic=None, lower_bound=None, upper_bound=None):
    return await edit_jira_issue_field_for_project_service(project_id, field, value, year, quarter, epic, lower_bound, upper_bound)


@app.get("/edit_jira_issue_tags_for_project/{project_id}")
async def edit_jira_issue_tags_for_project(project_id, value, year=None, quarter=None, epic=None, lower_bound=None, upper_bound=None):
    return await edit_jira_issue_tags_for_project_service(project_id, value, year, quarter, epic, lower_bound, upper_bound)


@app.get("/remove_jira_issue_tags_for_project/{project_id}")
async def remove_jira_issue_tags_for_project(project_id, value, year=None, quarter=None, epic=None, lower_bound=None, upper_bound=None):
    return await remove_jira_issue_tags_for_project_service(project_id, value, year, quarter, epic, lower_bound, upper_bound)


@app.get("/generate_report_for_project/{project_id}")
async def generate_report_for_project(project_id, year=None, quarter=None, epic=None):
    return await generate_report_for_project_service(project_id, year, quarter, epic)


@app.get("/pipeline/{project_id}")
async def pipeline(project_id, year=None, quarter=None, epic=None, lower_bound=None, upper_bound=None):
    return await pipeline_service(project_id, year, quarter, epic, lower_bound, upper_bound)