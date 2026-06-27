DIAGNOSIS_PROMPT = """
You are a senior Python software engineer.

A user has uploaded a Python repository.

Bug Report:
{bug_report}

Error Log:
{error_log}

These are the most suspicious functions:

{suspects}

Relevant source snippets:
{repository_context}

Analyze the bug and propose a corrected version of the most relevant function
or code block. The corrected code should be directly useful to the developer,
not a vague instruction.

Return ONLY a valid JSON object.

Do NOT wrap the JSON in markdown.

Do NOT use ```json.

Return only the JSON object.

{{
    "root_cause": "...",
    "suggested_fix": "...",
    "target_file": "...",
    "target_function": "...",
    "corrected_code": "...",
    "confidence": "High | Medium | Low"
}}
"""
