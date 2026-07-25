import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from groq import Groq

load_dotenv()

app = FastAPI(title="PantryChef AI")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groq API Key
api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    print("WARNING: GROQ_API_KEY is not set!")
else:
    print("Groq API key loaded successfully.")

# Groq Client
client = Groq(api_key=api_key)

# Groq Model
MODEL = os.environ.get(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)


SYSTEM_PROMPT = """
You are PantryChef, a friendly and practical cooking assistant.

Given a list of ingredients someone has available, suggest 2-3
realistic recipes they can make right now.

For each recipe provide:

1. A short recipe title
2. A one-line description
3. Ingredients used
4. Numbered cooking steps

Use the ingredients provided by the user.

You may use common kitchen staples such as:
- Salt
- Pepper
- Oil
- Water

Do not suggest unusual ingredients that the user did not provide.

Keep recipes simple, realistic, and easy to follow.

If the user has a dietary preference, make sure the recipes follow it.

Format the response in clean Markdown.
"""


class RecipeRequest(BaseModel):
    ingredients: str
    diet: str = "none"
    followup: str = ""
    history: str = ""


# TEMPORARY GROQ CONNECTION TEST
@app.get("/health")
async def health():
    try:
        print("Testing Groq API connection...")

        test = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": "Reply with only the word OK."
                }
            ],
            max_tokens=10
        )

        print("Groq connection successful!")

        return {
            "status": "ok",
            "groq": "connected",
            "api_key_loaded": bool(api_key),
            "model": MODEL,
            "response": test.choices[0].message.content
        }

    except Exception as e:
        print("GROQ HEALTH CHECK ERROR:", repr(e))

        return {
            "status": "error",
            "groq": "not connected",
            "api_key_loaded": bool(api_key),
            "model": MODEL,
            "error": repr(e)
        }


@app.post("/api/generate")
async def generate_recipe(request: RecipeRequest):

    print("API REQUEST RECEIVED")
    print("Ingredients:", request.ingredients)
    print("Diet:", request.diet)

    if not request.ingredients.strip():
        return {
            "success": False,
            "recipe": "Please enter at least one ingredient."
        }

    user_prompt = f"""
Ingredients available:
{request.ingredients}

Dietary preference:
{request.diet}

Previous conversation:
{request.history}

Follow-up request:
{request.followup}

Create 2-3 realistic recipes using the available ingredients.
"""

    try:

        print("Calling GroqCloud API...")

        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0.7,
            max_tokens=1500
        )

        recipe = completion.choices[0].message.content

        print("Recipe generated successfully.")

        return {
            "success": True,
            "recipe": recipe
        }

    except Exception as e:

        print("GROQ API ERROR:", repr(e))

        return {
            "success": False,
            "recipe": f"Error generating recipe: {str(e)}"
        }


# Serve frontend
app.mount(
    "/",
    StaticFiles(directory=".", html=True),
    name="static"
)