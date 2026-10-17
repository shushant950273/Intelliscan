import os
import sys
from dotenv import load_dotenv
from google import genai

def main() -> None:
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL")

    if not api_key or api_key.strip() == "your_key_here":
        print("Error: GEMINI_API_KEY is missing or contains placeholder. Please set a valid key in .env", file=sys.stderr)
        sys.exit(1)

    if not model_name or model_name.strip() == "your_model_name_here":
        print("Error: GEMINI_MODEL is missing or contains placeholder. Please set a valid model name in .env", file=sys.stderr)
        sys.exit(1)

    try:
        client = genai.Client(api_key=api_key)
        # Unsupported parameters (temperature, top_p, top_k, candidate_count) and experimental thinking configs are omitted.
        response = client.models.generate_content(
            model=model_name,
            contents="Reply with exactly: IntelliScan LLM OK",
        )
        print("LLM Output:")
        print(response.text)
    except Exception as e:
        print(f"Error calling Gemini API: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
