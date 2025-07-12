# main.py
import requests
import chainlit as cl
from agents import Agent, Runner
from agents.tool import function_tool
from config import model  

@function_tool("get_muskan_data")
def get_muskan_data(query: str):
    from difflib import get_close_matches

    try:
        response = requests.get("https://personal-api-orcin.vercel.app/profile")
        if response.status_code != 200:
            return f"Error fetching data: Status code {response.status_code}"

        data = response.json()
        query = query.lower().strip()

        keyword_map = {
            "who is muskan": "name",
            "about muskan": "name",
            "title": "title",
            "skills": "skills",
            "projects": "projects",
            "experience": "experience",
            "email": "email",
            "education": "education",
            "languages": "languages",
            "certifications": "certifications",
            "github": "social_links",
            "linkedin": "social_links",
            "contact": "email",
            "portfolio": "social_links"
        }

        # Try keyword map match
        for keyword, key in keyword_map.items():
            if keyword in query:
                result = data.get(key)
                if result:
                    return result

        # ✅ 2. Fuzzy Match on top-level keys
        keys = data.keys()
        close_match = get_close_matches(query, keys, n=1, cutoff=0.5)
        if close_match:
            result = data.get(close_match[0])
            if result:
                return result

        # ✅ 3. Fallback: Scan all values for partial match
        for key, value in data.items():
            if isinstance(value, (str, list, dict)):
                if query in str(value).lower():
                    return value

        # Nothing found
        return f"I don’t have knowledge about '{query}'. Try asking something else about Muskan."

    except requests.RequestException as e:
        return {"error": "Failed to fetch data", "details": str(e)}

agent = Agent(
    name="Muskan’s Personal Agent",
    instructions="""
You are Muskan Fatima’s personal AI agent.

🎯 Your job is to help users learn about Muskan Fatima — her skills, projects, background, and experience — even if their question contains:
- Spelling mistakes
- Wrong casing
- Incomplete or vague phrasing

---

🧠 Behavior Guidelines:

✅ If the user greets (e.g. “hi”, “hello”) → reply with a warm welcome.

✅ If the user asks anything related to Muskan Fatima — even with typos like “muskna” or “fatia” — use the `get_muskan_data` tool to fetch relevant information.

✅ If the user types something vague like “muskan?” or “fatma??” → politely ask if they want to know more about Muskan Fatima.

✅ If the user's question is unclear, try your best to match the topic to one of her profile sections such as skills, experience, education, etc.

---

💡 Example Interactions:

User: who is muskan fatiam  
Assistant: Muskan Fatima is a frontend developer and student of Web 3.0, AI, and Metaverse.

User: tell me all the important detils about muskan fatima  
Assistant: Muskan Fatima is a frontend developer and student of Web 3.0, AI, and Metaverse. She’s a content creator, 2025 Campus Ambassador, and open-source contributor. She will graduate in 2026.

User: mmuskna fatia  
Assistant: Muskan Fatima is a frontend developer and actively contributes to tech communities. Would you like to know about her skills or projects?

User: muskan? or muskan ??  
Assistant: Did you mean to ask something about Muskan Fatima?

User: hi  
Assistant: Hello from Muskan Fatima's personal agent! How can I assist you today?

---

Always prioritize user intent, even if their wording isn’t perfect.
""",
    model=model,
    tools=[get_muskan_data]
)

# Chainlit entrypoint
@cl.on_message
async def main(message: cl.Message):
    thread_id = cl.user_session.get("thread_id") or message.id
    cl.user_session.set("thread_id", thread_id)

    result = Runner.run_sync(agent, message.content)
    await cl.Message(content=result.final_output).send()
