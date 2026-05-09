import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def fetch_linkedin_profile(url: str) -> str:
    """
    Fetches LinkedIn profile data via RapidAPI.
    Returns the JSON payload as a string.
    """
    rapidapi_key = os.getenv("RAPIDAPI_KEY")
    if not rapidapi_key:
         raise ValueError("RAPIDAPI_KEY not found in environment. Direct LinkedIn scraping is blocked. Please provide a RapidAPI key in .env or upload the JSON/PDF export.")
         
    # Using 'Fresh LinkedIn Profile Data API' from RapidAPI as a standard example
    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": "fresh-linkedin-profile-data.p.rapidapi.com"
    }
    querystring = {"linkedin_url": url, "include_skills": "true"}
    
    try:
        response = requests.get(
            "https://fresh-linkedin-profile-data.p.rapidapi.com/get-linkedin-profile", 
            headers=headers, 
            params=querystring
        )
        response.raise_for_status()
        data = response.json()
        return json.dumps(data, indent=2)
    except requests.exceptions.HTTPError as e:
        if response.status_code in (401, 403):
            raise ValueError("Invalid or unauthorized RAPIDAPI_KEY.")
        raise ValueError(f"HTTP Error fetching LinkedIn profile: {e}")
    except Exception as e:
        raise ValueError(f"Failed to fetch LinkedIn data for {url}: {str(e)}")
