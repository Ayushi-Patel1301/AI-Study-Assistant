from gemini_service import ask_gemini

class PaperGeneratorAgent:

    def generate_paper(self, title, subject, topics, total_marks, difficulty, custom_pattern, instructions, include_answer_key, language="English"):
        pattern = self._pattern(custom_pattern, total_marks) if custom_pattern else f"Auto-distribute {total_marks} marks across MCQ, Short, Medium, and Long Answer sections."
        answer_key = "\nAfter the paper, add a detailed ANSWER KEY section." if include_answer_key else ""
        extra = f"\nAdditional Instructions: {instructions}" if instructions and instructions.strip() else ""

        prompt = f"""Generate a complete, professional exam question paper with these specifications:

Title: {title} | Subject: {subject} | Total Marks: {total_marks} | Difficulty: {difficulty} | Language: {language}
Topics (questions must ONLY come from these): {topics}
Pattern: {pattern}{extra}{answer_key}

IMPORTANT: Generate the entire question paper in {language} language only.

Format requirements:
- Formal header: [Institution], title, subject, total marks, time allowed, date
- General Instructions block (5 points)
- Clearly labelled sections (SECTION A, B, C...)
- Each question numbered with marks in brackets e.g. [2 Marks]
- MCQs must have options (a)(b)(c)(d)
- Section totals must add up to exactly {total_marks} marks
- Difficulty {difficulty}: {'recall/basic' if difficulty=='Easy' else 'application/analysis' if difficulty=='Medium' else 'analysis/evaluation/synthesis'} level questions
- End with: *** END OF QUESTION PAPER ***"""

        return ask_gemini(prompt)

    def _pattern(self, cp, total):
        rows = [f"{cp[c+'_count']}Q × {cp[c+'_marks']}M = {cp[c+'_count']*cp[c+'_marks']}M ({lbl})"
                for c, lbl in [("mcq","MCQ"),("short","Short"),("medium","Medium"),("long","Long")]
                if cp.get(c+"_count") and cp.get(c+"_marks")]
        computed = sum(cp.get(k,0)*cp.get(k.replace("count","marks"),0) for k in [k for k in cp if k.endswith("count")])
        note = f" [Adjust to reach {total}M total]" if computed != total else ""
        return ", ".join(rows) + note