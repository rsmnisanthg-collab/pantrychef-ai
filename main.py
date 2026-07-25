import os
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from groq import Groq


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(title="PantryChef AI")


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# GROQ CLIENT
# =========================================================

client = None

if api_key:
    print("Groq API key loaded successfully.")

    client = Groq(
        api_key=api_key,
        timeout=60.0,
        max_retries=2
    )

else:
    print("WARNING: GROQ_API_KEY is not set!")


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are PantryChef, a friendly and practical cooking assistant.

Given a list of ingredients someone has available, suggest 2-3
realistic recipes they can make right now.

For each recipe provide:

1. A short recipe title
2. A one-line description
3. Ingredients used
4. Numbered cooking steps
5. Approximate cooking time

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


# =========================================================
# REQUEST MODEL
# =========================================================

class RecipeRequest(BaseModel):
    ingredients: str
    diet: str = "none"
    followup: str = ""
    history: str = ""


# =========================================================
# API HOME
# =========================================================

@app.get("/api")
async def api_home():

    return {
        "message": "PantryChef AI API is running",
        "model": MODEL
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
async def health():

    if not api_key:

        return {
            "status": "error",
            "groq": "not configured",
            "api_key_loaded": False,
            "model": MODEL,
            "message": "GROQ_API_KEY is not configured."
        }


    if client is None:

        return {
            "status": "error",
            "groq": "client not created",
            "api_key_loaded": True,
            "model": MODEL
        }


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
            temperature=0,
            max_tokens=10
        )

        response_text = test.choices[0].message.content

        print("Groq connection successful!")

        return {
            "status": "ok",
            "groq": "connected",
            "api_key_loaded": True,
            "model": MODEL,
            "response": response_text
        }


    except Exception as e:

        print("GROQ HEALTH CHECK ERROR:", repr(e))

        return {
            "status": "error",
            "groq": "not connected",
            "api_key_loaded": True,
            "model": MODEL,
            "error_type": type(e).__name__,
            "error": str(e)
        }


# =========================================================
# GROQ CONNECTION TEST
# =========================================================

@app.get("/test-groq")
async def test_groq():

    try:

        import httpx

        print("Testing connection to Groq API...")

        async with httpx.AsyncClient(timeout=30.0) as http:

            response = await http.get(
                "https://api.groq.com/openai/v1/models"
            )


        print(
            "Groq API HTTP status:",
            response.status_code
        )


        return {
            "status": "success",
            "http_status": response.status_code,
            "message": "Render can reach Groq API"
        }


    except Exception as e:

        print(
            "GROQ NETWORK ERROR:",
            repr(e)
        )


        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error": str(e)
        }


# =========================================================
# GENERATE RECIPE
# =========================================================

@app.post("/api/generate")
async def generate_recipe(request: RecipeRequest):

    print("====================================")
    print("API REQUEST RECEIVED")
    print("Ingredients:", request.ingredients)
    print("Diet:", request.diet)
    print("====================================")


    # Check ingredients

    if not request.ingredients.strip():

        return {
            "success": False,
            "recipe": "Please enter at least one ingredient."
        }


    # Check API key

    if not api_key or client is None:

        return {
            "success": False,
            "recipe": "Groq API key is not configured on the server."
        }


    # Create user prompt

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
        print("Using model:", MODEL)


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

        print("====================================")
        print("GROQ API ERROR")
        print("ERROR TYPE:", type(e).__name__)
        print("ERROR:", repr(e))
        print("====================================")


        return {
            "success": False,
            "recipe": "Unable to connect to Groq AI right now.",
            "error_type": type(e).__name__,
            "error": str(e)
        }


# =========================================================
# SERVE FRONTEND
# =========================================================

app.mount(
    "/",
    StaticFiles(
        directory=".",
        html=True
    ),
    name="static"
)