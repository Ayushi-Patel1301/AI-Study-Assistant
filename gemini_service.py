import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)

# def ask_gemini(prompt):

#     for _ in range(3):
#         try:
#             response = client.models.generate_content(
#                 model="gemini-1.5-flash",
#                 contents=prompt
#             )
#             return response.text

#         except Exception:
#             continue

#     return "⚠️ AI is busy right now. Please try again."


def ask_gemini(prompt):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text

    except Exception as e:
        return f"ERROR DEBUG: {str(e)}"