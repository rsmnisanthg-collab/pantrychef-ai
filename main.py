import os
import httpx

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


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
# CHECK API KEY
# =========================================================

if api_key:
    print("Groq API key loaded successfully.")
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
# HOME
# =========================================================

@app.get("/api")
async def api_home():

    return {
        "message": "PantryChef AI API is running",
        "model": MODEL,
        "api_key_loaded": bool(api_key)
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
            "error": "GROQ_API_KEY is not configured."
        }


    try:

        print("Testing Groq API connection...")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": "Reply with only the word OK."
                }
            ],
            "temperature": 0,
            "max_tokens": 10
        }

        async with httpx.AsyncClient(
            timeout=60.0
        ) as http:

            response = await http.post(
                GROQ_API_URL,
                headers=headers,
                json=data
            )


        print(
            "Groq HTTP Status:",
            response.status_code
        )


        if response.status_code != 200:

            print(
                "Groq Error Response:",
                response.text
            )

            return {
                "status": "error",
                "groq": "not connected",
                "api_key_loaded": True,
                "model": MODEL,
                "http_status": response.status_code,
                "error": response.text
            }


        result = response.json()

        answer = result["choices"][0]["message"]["content"]


        print("Groq connection successful!")


        return {
            "status": "ok",
            "groq": "connected",
            "api_key_loaded": True,
            "model": MODEL,
            "response": answer
        }


    except Exception as e:

        print(
            "GROQ HEALTH CHECK ERROR:",
            repr(e)
        )

        return {
            "status": "error",
            "groq": "not connected",
            "api_key_loaded": bool(api_key),
            "model": MODEL,
            "error_type": type(e).__name__,
            "error": str(e)
        }


# =========================================================
# GENERATE RECIPE
# =========================================================

@app.post("/api/generate")
async def generate_recipe(
    request: RecipeRequest
):

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

    if not api_key:

        return {
            "success": False,
            "recipe": "Groq API key is not configured on the server."
        }


    # User prompt

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


    # Request headers

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }


    # Request data

    data = {

        "model": MODEL,

        "messages": [

            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },

            {
                "role": "user",
                "content": user_prompt
            }

        ],

        "temperature": 0.7,

        "max_tokens": 1500
    }


    try:

        print("Calling Groq API directly...")
        print("Model:", MODEL)


        async with httpx.AsyncClient(
            timeout=60.0
        ) as http:

            response = await http.post(

                GROQ_API_URL,

                headers=headers,

                json=data
            )


        print(
            "Groq HTTP Status:",
            response.status_code
        )


        # Check API response

        if response.status_code != 200:

            print(
                "GROQ API ERROR:",
                response.text
            )


            return {

                "success": False,

                "recipe": "Unable to generate recipes.",

                "error": response.text,

                "http_status": response.status_code
            }


        # Convert response to JSON

        result = response.json()


        # Get recipe text

        recipe = result["choices"][0]["message"]["content"]


        print(
            "Recipe generated successfully."
        )


        return {

            "success": True,

            "recipe": recipe
        }


    except httpx.TimeoutException as e:

        print(
            "GROQ TIMEOUT ERROR:",
            repr(e)
        )


        return {

            "success": False,

            "recipe": "Groq API request timed out. Please try again.",

            "error_type": "TimeoutException",

            "error": str(e)
        }


    except httpx.RequestError as e:

        print(
            "GROQ CONNECTION ERROR:",
            repr(e)
        )


        return {

            "success": False,

            "recipe": "Could not connect to Groq API.",

            "error_type": "RequestError",

            "error": str(e)
        }


    except Exception as e:

        print(
            "UNEXPECTED ERROR:",
            repr(e)
        )


        return {

            "success": False,

            "recipe": "An unexpected error occurred.",

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