import sys
import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

def main():
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    if len(sys.argv) != 4:
        print("Usage: python script.py <instructions.txt> <dress-list.xlsx> <player-info.xlsx>")
        sys.exit(1)

    instructions_file = sys.argv[1]
    dress_list_file = sys.argv[2]
    player_info_file = sys.argv[3]

    with open(instructions_file, "r") as f:
        instructions = f.read()

    base_name1 = os.path.splitext(os.path.basename(dress_list_file))[0]
    base_name2 = os.path.splitext(os.path.basename(player_info_file))[0]
    output_file = f"{base_name1}_vs_{base_name2}_comparison.xlsx"

    try:
        # Convert input Excel files to base64 strings
        with open(dress_list_file, "rb") as f:
            dress_b64 = base64.b64encode(f.read()).decode("utf-8")
        with open(player_info_file, "rb") as f:
            player_b64 = base64.b64encode(f.read()).decode("utf-8")

        # Build the prompt including the base64 files
        prompt = f"""
            {instructions}

            The two Excel files are provided as base64 strings:
            dress_list.xlsx (base64):
            {dress_b64}

            player_info.xlsx (base64):
            {player_b64}

            Please return the resulting reordered Excel as a base64 string.
        """

        print("Sending Prompt")

        response = client.responses.create(
            model="gpt-5",
            input=prompt
        )

        print("Response Received")

        output_base64 = response.output_text.strip()

        # Decode and save
        excel_bytes = base64.b64decode(output_base64)
        with open(output_file, "wb") as f:
            f.write(excel_bytes)

        print(f"✅ AI-generated Excel saved to {output_file}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
