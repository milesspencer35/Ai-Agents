from llm_agent import LlmAgent
from typing import Optional

SYSTEM_PROMPT = """
You are a resume analyzer agent. 
Your goal is to analyze a resume and return the top 3 job titles that the resume is a good fit for. 
Your output will be used to query a job search api so ONLY return the job titles separated by commas. 
"""

class ResumeAnalyzerAgent(LlmAgent):
    def __init__(self, model: Optional[str] = None):
        super().__init__(system_prompt=SYSTEM_PROMPT, model=model)

    async def evaluate(self, resume: str):
        return await self.execute(
            prompt=f"Find potential job titles for this resume: {resume}"
        )


