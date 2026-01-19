import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("Error: Key not found")
    exit()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=api_key)

try:
    response = llm.invoke("Hello!")
    print(f"AI Response: {response.content}")
except Exception as e:
    print(f"Error: {e}")