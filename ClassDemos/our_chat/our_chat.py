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
		response = await client.responses.create(
			input=history,
			model='gpt-4o-mini'
		)
		history.append({
			'role': 'assistant', 'content': response.output_text
		})
		print(response.output_text)
		if len(history) > 10:
			break

if __name__ == '__main__':
	asyncio.run(main(Path(sys.argv[1])))