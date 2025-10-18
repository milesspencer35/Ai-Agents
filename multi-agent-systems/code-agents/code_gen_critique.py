# A generator / critic multi-agent pattern. First agent generates a function and
# the second critiques it. This was developed prior to class. Note more detailed
# instructions that tend to catch more nuanced bugs.

import asyncio

from llm_agent import LlmAgent

COMPLETE_PHRASE = "CODE_IS_PERFECT"

async def main():
    coder = LlmAgent("Your task is to create Python function as outlined by the user. You will "
                     "also receive feedback on the function you generate. As you receive that feedback, "
                     "generate a new function that adheres to the given feedback. Do not provide explanations, "
                     "usage or other information. Generate just the function code.")
    critic = LlmAgent("You are a senior software engineer and an expert in Python. "
                      "Your role is to perform a meticulous code review. "
                      "Critically evaluate the provided Python code based on the original task requirements. "
                      "Look for bugs, style issues, missing edge cases, and areas for improvement. "
                      "If the code needs improvement, provide a bulleted list of your critiques. "
                      "Do not provide your own implementation. You will not be given the unit tests for the "
                      "function so assume they fully cover the cases. "
                      "If the code meets all requirements and would not materially benefit from revision, "
                      f"respond with the single phrase '{COMPLETE_PHRASE}'. This phrase is a signal to stop "
                      "producing a new function so do not use that phrase unless the function is completely "
                      "satisfactory.")

    while True:
        func_spec = input("\n******************\nDescribe a function: ")
        if func_spec == 'DONE':
            break
        feedback = ""
        coder.reset_history()
        critic.reset_history()
        while COMPLETE_PHRASE not in feedback:
            print(">> Generating function...")
            func_impl = await coder.execute(func_spec)
            print(f"\n=======================\n{func_impl}")
            print(">> Examining function...")
            feedback = await critic.execute(f"Specification: {func_spec}\nImplementation:\n{func_impl}")
            print(f"\n----------------------\n{feedback}")
            func_spec = feedback


if __name__ == '__main__':
    asyncio.run(main())
