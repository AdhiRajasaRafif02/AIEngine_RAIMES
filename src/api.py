from google import genai
from dotenv import getenv, load_dotenv

client = genai.Client(api_key=getenv("API_GEMINI"))

response = client.models.generate_content(
    model="gemini-2.5-flash", contents="Explain how AI works in a few words"
)
print(response.text)