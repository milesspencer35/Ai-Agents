import sys
import os
from openai import OpenAI
from dotenv import load_dotenv

def main():
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    if len(sys.argv) < 2:
        print("Usage: python script.py <instructions_file.md>")
        sys.exit(1)

    instructions_file = sys.argv[1]
    name1 = input("Enter the first player's name: ")
    name2 = input("Enter the second player's name: ")

    try:
        with open(instructions_file, "r", encoding="utf-8") as f:
            instructions = f.read()
    except FileNotFoundError:
        print(f"Error: File '{instructions_file}' not found.")
        sys.exit(1)

    prompt = (
        f"{instructions}" + 
        f"The two players are: {name1} and {name2}."
    )

    response = client.responses.create(
        model="gpt-5",  # supported tool-enabled model
        tools=[{"type": "web_search"}],
        input=prompt,
    )

    # --- Output to file logic ---
    output_file = "response.md"
    with open(output_file, "w", encoding="utf-8") as f:
        if hasattr(response, "output_text") and response.output_text:
            f.write(response.output_text)
        elif hasattr(response, "output"):
            for item in response.output:
                if item.type == "message" and item.role == "assistant":
                    for content in item.content:
                        if content.type == "output_text":
                            f.write(content.text)
        else:
            f.write("DEBUG: Raw response object ->\n")
            f.write(str(response))
    print(f"Response has been saved to {output_file}")

if __name__ == "__main__":
    main()
