
from pathlib import Path
from PyPDF2 import PdfReader
import sys
from resume_analyzer_agent import ResumeAnalyzerAgent
from job_search_agent import JobSearchAgent
from scam_agent import ScamAgent
import asyncio
import os
import requests

JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY")


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text content
        
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        Exception: For other PDF processing errors
    """
    pdf_path = Path(pdf_path)
    
    # Check if file exists
    if not pdf_path.exists() or not pdf_path.is_file():
        raise FileNotFoundError(f"The file {pdf_path} does not exist or is not a file.")
    
    # Check file extension
    if pdf_path.suffix.lower() != '.pdf':
        raise ValueError("The file must be a PDF (.pdf) file.")
    
    try:
        # Initialize PDF reader and extract text
        reader = PdfReader(pdf_path)
        text = ""
        
        # Extract text from each page
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        return text.strip()
    except Exception as e:
        raise Exception(f"Error processing PDF file: {str(e)}")

async def job_search(query: str):
    response = requests.get(
        "https://api.openwebninja.com/jsearch/search",
        headers={
            "x-api-key": JSEARCH_API_KEY
        },
        params={
            "query": query,
            "page": "1",
            "num_pages": "1",
            "country": "us",
            "language": "en",
            "date_posted": "month",
            "work_from_home": "false",
            "employment_types": "FULLTIME",
            "job_requirements": "under_3_years_experience",
            "radius": "50",
            "exclude_job_publishers": "BeeBe,Dice,WhatJobs",
            # "fields": "employer_name,job_publisher,job_title,job_country"
        }
    )

    res = response.json()

    # ✅ Check response status
    if res.get("status") != "OK":
        raise Exception(f"API Error: {res}")

    # 🎯 Extract just the job listings
    jobs = res.get("data", [])

    return jobs

async def main(resume_pdf: str):
    
    try:
        # Extract text from the PDF
        resume_text = extract_text_from_pdf(resume_pdf)
        
        # # Print the extracted text
        # print("\n=== EXTRACTED RESUME TEXT ===")
        # print(resume_text)
        # print("\n=== END OF RESUME TEXT ===")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

    resume_agent = ResumeAnalyzerAgent(model="gpt-5-nano")
    job_titles = await resume_agent.evaluate(resume_text)
    print("\n=== JOB TITLES ===")
    print(job_titles)
    print("\n=== END OF JOB TITLES ===")

    job_titles_list = job_titles.split(",")
    for job_title in job_titles_list:
        jobs = await job_search(job_title + " in Orem, Utah")
        print("\n=== JOB POSTINGS ===")
        print(jobs)
        print("\n=== END OF JOB POSTINGS ===")

        scam_agent = ScamAgent(model="gpt-4o-mini")
        filtered_jobs = await scam_agent.evaluate(jobs)
        print("\n=== FILTERED JOB POSTINGS ===")
        print(filtered_jobs)
        print("\n=== END OF FILTERED JOB POSTINGS ===")

        job_search_agent = JobSearchAgent(model="gpt-5-nano")
        output = await job_search_agent.evaluate(filtered_jobs, resume_text)
        print(f"\n=== JOB SEARCH AGENT OUTPUT FOR {job_title} ===")
        print(output)
        print(f"\n=== END OF JOB SEARCH AGENT OUTPUT FOR {job_title} ===")


        with open(f"results/{job_title}.md", "w") as f:
            f.write(output)
        

if __name__ == "__main__":
    resume_pdf = sys.argv[1]
    asyncio.run(main(resume_pdf))
