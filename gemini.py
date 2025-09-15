import google.generativeai as genai
from dotenv import load_dotenv
import asyncio
import os

load_dotenv('env/.env')

GEMINI_API_KEY = os.getenv('LLM_API')

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# python forcing me to put it here when i want to keep the methods together >:(
def load_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Warning: {filename} not found!")
        return ""

RULES = load_file("prompts/rules.txt")
KNOWLEDGE_BASE = load_file("prompts/knowledge.txt")
EXTRAS = load_file("prompts/extras.txt")
PROMPT = load_file("prompts/prompt.txt")


def build_prompt(user_input, username, context_type="USER MESSAGE", replied_context=None):
    if not (RULES and PROMPT):
        print("have a rules.txt, and a prompt.txt")
        return None
    
    prompt = f"""
RULES:
{RULES}

{PROMPT}

KNOWLEDGE BASE:
{KNOWLEDGE_BASE if KNOWLEDGE_BASE else ""}

EXTRAS:
{EXTRAS if EXTRAS else ""}

REPLIED TO MESSAGE: {replied_context if replied_context else ""}

{context_type} from {username}: {user_input}

Please provide a helpful response. If the knowledge base is relevant to the question, use it. Otherwise, answer normally. Keep responses concise for Discord (under 2000 characters)."
"""
    
    return prompt

async def get_gemini_response(user_input, username, context_type="USER MESSAGE", replied_context=None):
    try:
        prompt = build_prompt(user_input, username, context_type, replied_context)
        if not prompt:
            return "Check the console for more information"
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(prompt)
        )
        
        return response.text
    
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Sorry, I'm having trouble processing your request right now."
