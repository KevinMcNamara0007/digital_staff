from datetime import datetime
import numpy as np
import pandas as pd
from dateutil.utils import today

from src.utilities.jira_utils import get_issue

refactor_template = """
Title: \n I want [feature\ so that [benefit].
Description: Provide a detailed description of the story. Include any relevant background information and context.
Acceptance Criteria: \n Description of criteria
Assumptions: description of assumption\n
Dependencies: Dependancy 1: Description of first dependency.
Priority: High/Medium/Low
Story points: estimated story points: 1 story point equals 4 hours of work.
Additional Notes: Other information."""

def within_bounds(number, lower_bound=0, upper_bound=999):
    return lower_bound <= number <= upper_bound

def add_label(new_label, labels):
    if new_label not in labels:
        labels.append(new_label)
    return labels

async def get_jira_issue_service(jira_id):
    issue = get_issue(jira_id)
    return issue

async def refactor_jira_issue_service(jira_id):
    prev_issue = await get_jira_issue_service(jira_id)

    issue_summary = prev_issue['fields']['summary']
    issue_description = prev_issue['fields']['description']

    prompt = (
        f"Please read the following Jira Issue Summary: \'{issue_summary}\'. Please rewrite only the description in the"
        f" following format: {refactor_template}\n"
    )