import sys
import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

def main():
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    if len(sys.argv) < 4:
        print("Usage: python script.py <file1.xlsx> <file2.xlsx> <output.xlsx>")
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]
    output_file = sys.argv[3]

    try:
        df1 = pd.read_excel(file1)
        df2 = pd.read_excel(file2)

        # Convert DataFrames to CSV text
        data1 = df1.to_csv(index=False)
        data2 = df2.to_csv(index=False)

        # Ask ChatGPT to produce CSV output we can re-convert to Excel
        response = client.responses.create(
            model="gpt-4.1",
            input=f"""
            You are given two Excel files. 
            File 1:\n{data1}\n
            File 2:\n{data2}\n

            Please analyze these files and return your answer STRICTLY as a valid CSV table
            (with headers and rows) so it can be saved back into an Excel file.
            """
        )

        csv_text = response.output_text.strip()

        # Convert AI response back into a DataFrame
        from io import StringIO
        df_out = pd.read_csv(StringIO(csv_text))

        # Save as Excel
        df_out.to_excel(output_file, index=False)
        print(f"✅ AI response saved to {output_file}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
