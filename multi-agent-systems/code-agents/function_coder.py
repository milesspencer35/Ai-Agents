# A generator / critic multi-agent pattern. First agent generates a function and
# the second critiques it. This was developed in class.

import asyncio

from llm_agent import LlmAgent

CODE_COMPLETE = "CODE_IS_PERFECT"

async def main():
    # a function coder / critic agent pair
    code = LlmAgent("you are a coding agent. You will get a request for a function implementation. You should "
                    "produce a python implementation of the function. Do not provide any explanation or anything "
                    "other than the function itself.", model='gpt-4o-mini')
    critic = LlmAgent("You are an expert code critic. You will be given a function implementation and a specification. "
                      "You should evaluate the function for correctness, simplicity, readability. If you have critiques "
                      "provide a bulleted list of those. If the code is satisfactory responde with the single "
                      f"response {CODE_COMPLETE}")

    while True:
        code.reset_history()
        critic.reset_history()
        func_spec = input(f"\n{'*' * 50}\nFunction specification: ")
        feedback = ""
        while CODE_COMPLETE not in feedback:
            print("Generating function...")
            func_impl = await code.execute(f"Specification: {func_spec} {feedback}")
            print(f"\n{'-' * 50}\n{func_impl}")
            print("Evaluating function...")
            feedback = await critic.execute(f"Function specficiation {func_spec}. Implementation: {func_impl}")
            print(f"\n{'-' * 50}\n{feedback}")


if __name__ == '__main__':
    asyncio.run(main())
