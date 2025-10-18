from llm_agent import LlmAgent
from typing import Optional

SYSTEM_PROMPT = """
You are an expert at finding scams and fake job postings.
You will be given a list of job postings in json format.
Your job is to filter out any job postings that are scams or seem fake.
ONLY return the filtered list of job postings. Do not provide any additional text.
"""

class ScamAgent(LlmAgent):
    def __init__(self, model: Optional[str] = None):
        super().__init__(system_prompt=SYSTEM_PROMPT, model=model)

    async def evaluate(self, jobs: list):
        return await self.execute(
            prompt=f"Here is the json of the job postings: {jobs}"
        )


