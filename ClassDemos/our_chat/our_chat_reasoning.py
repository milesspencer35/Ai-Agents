import asyncio
import sys
from pathlib import Path
from openai import AsyncOpenAI


async def main(prompt_file: Path):
	client = AsyncOpenAI()
	prompt = prompt_file.read_text()
	history = [
		{'role': 'system', 'content': prompt}
	]


	while True:
		user_msg = input('User: ')
		history.append({'role': 'user', 'content': user_msg})

		reasoning = await client.responses.create(
			input=[{"role": "developer", "content": "Analyze the following conversation and reason about it. Your reasoning will be used by AI to generate a response to the user: "},] + history,
			model='o3-mini',
		)

		print("*************Reasoning: ********\n", reasoning.output_text, "\n******** Reasoning end********\n")

		response = await client.responses.create(
			input=history + [{"role": "developer", "content": reasoning.output_text + reasoning.output_text}],
			model='gpt-4o-mini',
			# reasoning={
			# 	"effort": "medium",
			# 	"summary": "detailed"
			# }
		)

		# # Assuming your response object is stored in `response`
		# reasoning_item = response.output[0]  # The ResponseReasoningItem
		# if hasattr(reasoning_item, "summary") and reasoning_item.summary:
		# 	summary_text = reasoning_item.summary[0].text
		# 	print("*******Reasoning summary: *********\n")
		# 	print(summary_text)
		# 	print("******* Reasoning summary end********\n")
		# else:
		# 	print("No reasoning summary found.")


		history.append({
			'role': 'assistant', 'content': response.output_text
		})
		print(response.output_text)
		# Keep only the system prompt and the 9 most recent messages
		if len(history) > 10:
			history = [history[0]] + history[-9:]

if __name__ == '__main__':
	asyncio.run(main(Path(sys.argv[1])))