from llm_agent import LlmAgent
from typing import Optional

SYSTEM_PROMPT = """
You are a professional job search agent. 
Your goal is to take a resume and job posting then provide a summary of the job posting and a 1-10
rating of how well the job posting matches the resume. Make sure to include the link to the job posting. 
If the resume ranking is 5/10 or less don't output it, and don't mention that you did any filtering.
Don't provide any follow up at the end. 
Your output should be in markdown format. 
"""

class JobSearchAgent(LlmAgent):
    def __init__(self, model: Optional[str] = None):
        super().__init__(system_prompt=SYSTEM_PROMPT, model=model)

    async def evaluate(self, jobs: list, resume: str):
        return await self.execute(
            prompt=f"Given this resume: {resume}, provide a summary and 1-10 rating of these job postings: {jobs}"
        )