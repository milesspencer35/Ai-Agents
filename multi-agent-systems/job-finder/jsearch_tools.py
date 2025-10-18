import requests
import os

JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY")

try:
    from tools import ToolBox
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from tools import ToolBox

def JSearchToolBox():
    def __init__():
        self.toolbox = ToolBox()
        
    def register_tools(self):
        tb = self.toolbox

        @tb.tool
        def job_search(query: str):
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
                    "date_posted": "today",
                    "work_from_home": "false",
                    "employment_types": "FULLTIME",
                    "job_requirements": "no_experience",
                    "radius": "1",
                    "exclude_job_publishers": "BeeBe,Dice",
                    # "fields": "employer_name,job_publisher,job_title,job_country"
                }
            )

            res = response.json()

            # ✅ Check response status
            if res.get("status") != "success":
                raise Exception(f"API Error: {res}")

            # 🎯 Extract just the job listings
            jobs = res.get("data", [])

            return jobs
