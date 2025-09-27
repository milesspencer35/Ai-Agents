from openai import OpenAI
import json
from tools import ToolKit

client = OpenAI()

# Initialize the toolkit
toolkit = ToolKit()
input_list = []

while True:
    user_input = input("User: ")
    input_list.append({"role": "user", "content": user_input})

    # 2. Prompt the model with tools defined
    response = client.responses.create(
        model="gpt-5-nano",
        tools=ToolKit.tools,  # Use the tools from the ToolKit class
        input=input_list,
    )

    # Save function call outputs for subsequent requests
    input_list += response.output

    for item in response.output:
        if item.type == "function_call":
            if item.name == "get_horoscope":
                # 3. Execute the function logic for get_horoscope
                result = ToolKit.get_horoscope(json.loads(item.arguments)['sign'])
            elif item.name == "get_byu_football_schedule":
                result = ToolKit.get_byu_football_schedule()
            elif item.name == "get_current_date":
                result = ToolKit.get_current_date()
            elif item.name == "create_calendar_event":
                result = ToolKit.create_calendar_event(json.loads(item.arguments)['summary'], json.loads(item.arguments)['start_time'], json.loads(item.arguments)['end_time'], json.loads(item.arguments)['calendar_id'])
            
            # 4. Provide function call results to the model
            if result is not None:  # Only add if result is not None
                input_list.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps({
                        "result": result
                    })
                })

    response = client.responses.create(
        model="gpt-5-nano",
        tools=ToolKit.tools,
        input=input_list,
    )

    print("\nAI: " + response.output_text)