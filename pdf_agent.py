import fitz
from gemini_service import ask_gemini

class PDFAgent:

    def extract_text(self, pdf_file):
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        return "\n".join(page.get_text() for page in doc)

    def generate_quiz(self, pdf_text):
        prompt = f"""You are a quiz generator. Based on the PDF content below, generate exactly 5 multiple choice questions.

Return ONLY a valid JSON array with no extra text, no markdown, no code blocks. Format:
[
  {{
    "question": "Question text here?",
    "options": ["a) Option1", "b) Option2", "c) Option3", "d) Option4"],
    "answer": "a) Option1",
    "explanation": "Brief explanation here."
  }}
]

PDF Content:
{pdf_text[:12000]}"""
        import json
        raw = ask_gemini(prompt)
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(raw)

    def ask_pdf(self, pdf_text, question):
        prompt = f"""You are a helpful study assistant. Answer the student's question using ONLY the content from the PDF below.
If the answer is not found in the PDF, say: "This information is not available in the uploaded PDF."
Give clear, student-friendly explanations.

PDF Content:
{pdf_text[:12000]}

Student's Question: {question}"""
        return ask_gemini(prompt)