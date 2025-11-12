import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Gemini client with API key
api_key = os.getenv('API_GEMINI')
if not api_key or api_key == 'your_api_key_here':
    raise ValueError('API_GEMINI not configured. Get key from: https://makersuite.google.com/app/apikey')

# Configure the library with the API key
genai.configure(api_key=api_key)


def ask(prompt: str, model_name: str = "gemini-2.5-flash") -> str:
    """Send a prompt to the Gemini model and return the text response.

    Uses the GenerativeModel helper from google.generativeai.
    """
    model = genai.GenerativeModel(model_name=model_name)
    response = model.generate_content(prompt)
    return getattr(response, "text", repr(response))


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Gemini CLI — ask the model a question")
    parser.add_argument("-p", "--prompt", help="One-shot prompt to send and exit")
    parser.add_argument("-m", "--model", default="gemini-2.5-flash", help="Model name to use")
    args = parser.parse_args()

    if args.prompt:
        try:
            print(ask(args.prompt, args.model))
        except Exception as e:
            print("Error calling Gemini:", e)
        return

    # Interactive REPL
    print("Gemini CLI — interactive mode. Type 'exit' or 'quit' to leave.")
    try:
        while True:
            try:
                prompt = input("> ")
            except EOFError:
                print()
                break
            if prompt is None:
                break
            prompt = prompt.strip()
            if not prompt:
                continue
            if prompt.lower() in ("exit", "quit"):
                break
            try:
                answer = ask(prompt, args.model)
                print("\n", answer, "\n")
            except Exception as e:
                print("Error calling Gemini:", e)
    except KeyboardInterrupt:
        print("\nExiting.")


if __name__ == "__main__":
    main()

