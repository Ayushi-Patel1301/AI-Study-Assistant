from gemini_service import ask_gemini
import json


def generate_quiz(topic, num_questions, difficulty, language="English"):

    prompt = f"""
Generate {num_questions} multiple choice questions on the topic:

{topic}

Difficulty: {difficulty}
Language: {language}

IMPORTANT: Write the entire quiz — questions, options, and answers — in {language}.

Return ONLY valid JSON in this format:

[
  {{
    "question": "Question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Option A"
  }}
]

Do not add markdown.
Do not add explanations.
Return JSON only.
"""

    response = ask_gemini(prompt)

    try:
        return json.loads(response)
    except:
        return []