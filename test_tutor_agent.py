from tutor_agent import TutorAgent

agent = TutorAgent()

question = "What is a PN junction diode?"

response = agent.get_response(question)

print("\n=== TUTOR AGENT RESPONSE ===\n")
print(response)