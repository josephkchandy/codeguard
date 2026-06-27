
import json

from langchain_groq import ChatGroq

from app.config import settings


llm = ChatGroq(
    groq_api_key=settings.GROQ_API_KEY,
    model=settings.MODEL_NAME,
    temperature=0
)


def ask_groq(prompt, fallback=None):

    response = llm.invoke(prompt)

    content = response.content.strip()

    # Remove markdown code fences if present
    if content.startswith("```json"):
        content = content.replace("```json", "", 1)

    if content.startswith("```"):
        content = content.replace("```", "", 1)

    if content.endswith("```"):
        content = content[:-3]

    content = content.strip()

    try:
        return json.loads(content)

    except Exception:
        if fallback is not None:
            return fallback

        return {
            "root_cause": content,
            "suggested_fix": "",
            "target_file": "",
            "target_function": "",
            "corrected_code": "",
            "confidence": "Unknown"
        }
