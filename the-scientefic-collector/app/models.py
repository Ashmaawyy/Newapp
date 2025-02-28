from pymongo import MongoClient
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv

# Load environment variables from keys.env
load_dotenv('C:/Users/ALDEYAA/OneDrive - AL DEYAA MEDIA PRODUCTION/Documents/the-collector-series/keys.env')

# Get the API key from the environment variable
SPRINGER_API_KEY = os.getenv('SPRINGER_API_KEY')

# MongoDB Setup
client = MongoClient("mongodb://localhost:27017/")
db = client["the-scientific-collector"]
papers_collection = db["scientific-collection"]

def fetch_papers(days=60, max_results=100):
    """
    Fetches newly published scientific articles from Springer using their API.
    """
    papers = []
    start = 1
    rows = 10  # Number of results per page (adjust as needed)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    while len(papers) < max_results:
        url = f"https://api.springernature.com/openaccess/json?api_key={SPRINGER_API_KEY}&q=onlinedate:{start_date.strftime('%Y-%m-%d')} TO {end_date.strftime('%Y-%m-%d')}&p={start}&s={rows}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if not data['records']:
                break  # No more records to fetch

            for record in data['records']:
                paper = {
                    "title": record.get("title", "No title"),
                    "author": ", ".join([author["creator"] for author in record.get("creators", [])]),
                    "publishedAt": record.get("publicationDate", "No date"),
                    "url": record.get("url", [{"value": "No URL"}])[0]["value"],
                    "abstract": {
                        "h1": "Abstract",
                        "p": record.get("abstract", "No abstract")
                    },
                    "journal": record.get("publicationName", "Springer")
                }
                papers.append(paper)
                if len(papers) >= max_results:
                    break

            start += rows
        else:
            print(f"❌️ Failed to fetch articles from Springer. Status code: {response.status_code}")
            break

    return papers

def store_papers(papers):
    """
    Stores scraped scientific articles in MongoDB with the new data structure.
    """
    formatted_papers = []

    for paper in papers:
        if not papers_collection.find_one({"title": paper["title"]}):
            formatted_papers.append(paper)

    if formatted_papers:
        papers_collection.insert_many(formatted_papers)
        print(f"✅ Successfully inserted {len(formatted_papers)} papers into MongoDB.")
    else:
        print(f"⚠ No valid and unique papers to insert.")
