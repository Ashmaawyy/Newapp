from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
from scholarly import scholarly

app = Flask(__name__)

# MongoDB Setup
client = MongoClient("mongodb://localhost:27017/")
db = client["the-scientefic-collector"]
papers_collection = db["scientefic-collection"]

def fetch_and_store_papers():
    search_query = scholarly.search_pubs("scientific papers")
    for paper in search_query:
        paper_data = scholarly.fill(paper)
        if not papers_collection.find_one({"title": paper_data["bib"]["title"]}):
            papers_collection.insert_one({
                "title": paper_data["bib"]["title"],
                "author": paper_data["bib"].get("author", "N/A"),
                "publishedAt": paper_data["bib"].get("pub_year", datetime.datetime.now().year),
                "url": paper_data.get("eprint_url", ""),
                "abstract": paper_data["bib"].get("abstract", ""),
                "journal": paper_data["bib"].get("journal", "N/A")
            })
    print("Papers Updated!")

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_store_papers, "interval", minutes=60)
scheduler.start()

@app.route('/')
def index():
    page = request.args.get("page", 1, type=int)
    per_page = 5
    total_count = papers_collection.count_documents({})
    total_pages = (total_count + per_page - 1) // per_page
    
    papers = list(papers_collection.find().sort("publishedAt", -1).skip((page - 1) * per_page).limit(per_page))
    
    return render_template("index.html", papers=papers, page=page, total_pages=total_pages)

@app.route('/update_papers', methods=['GET'])
def update_papers():
    fetch_and_store_papers()
    return jsonify({"status": "success", "message": "Papers updated!"})

@app.route('/load_latest_papers')
def load_latest_papers():
    latest_papers = list(papers_collection.find().sort("publishedAt", -1).limit(5))

    papers_data = [
        {
            "title": item["title"],
            "author": item.get("author", "N/A"),
            "publishedAt": item["publishedAt"],
            "url": item["url"],
            "abstract": item.get("abstract", ""),
            "journal": item.get("journal", "N/A")
        } for item in latest_papers
    ]

    return jsonify({"papers": papers_data})

@app.route('/load_more_papers')
def load_more_papers():
    page = request.args.get("page", 1, type=int)
    per_page = 10  # Load more papers per scroll

    papers = list(papers_collection.find().sort("publishedAt", -1).skip((page - 1) * per_page).limit(per_page))

    papers_data = [
        {
            "title": item["title"],
            "author": item.get("author", "N/A"),
            "publishedAt": item["publishedAt"],
            "url": item["url"],
            "abstract": item.get("abstract", ""),
            "journal": item.get("journal", "N/A")
        } for item in papers
    ]

    return jsonify({"papers": papers_data, "page": page})

@app.route('/search_papers')
def search_papers():
    query = request.args.get("q", "").lower()
    papers = list(papers_collection.find({"title": {"$regex": query, "$options": "i"}}).limit(10))

    papers_data = [
        {
            "title": item["title"],
            "author": item.get("author", "N/A"),
            "publishedAt": item.get("publishedAt", ""),
            "url": item["url"],
            "abstract": item.get("abstract", ""),
            "journal": item.get("journal", "N/A")
        } for item in papers
    ]

    return jsonify({"papers": papers_data})

if __name__ == "__main__":
    app.run(debug=True)
