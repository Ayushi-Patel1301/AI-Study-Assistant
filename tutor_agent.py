from gemini_service import ask_gemini


class TutorAgent:
    def __init__(self):
        self.role = "AI Tutor"

    def get_response( self, user_question ):
        prompt = f"""
You are an expert AI tutor for students of all academic levels and subject.
your role is to
Explain the concept in a simple, clear,accurately and in a student-friendly way.

Student Question: {user_question}
"""
        return ask_gemini(prompt)