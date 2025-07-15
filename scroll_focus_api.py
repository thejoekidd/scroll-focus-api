
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
import re

class ContentItem(BaseModel):
    title: str
    url: str
    source: str
    media_type: str
    tags: List[str]
    publish_date: str
    score: float

class CustomQueryRequest(BaseModel):
    user_id: int
    query: str

class CustomQueryResponse(BaseModel):
    user_id: int
    original_query: str
    topics: List[str]
    intent: str
    media_types: List[str]
    freshness: str

app = FastAPI(title="Scroll Focus API (Stubbed)", version="0.2")

def get_user_profile(user_id: int) -> Dict:
    return {
        "interests": {"psychology": 0.9, "tech": 0.7, "news": 0.4},
        "preferred_media_types": {"article": 1.0, "podcast": 0.7, "video": 0.5},
        "depth_preference": "short",
        "engagement_history": {"The Atlantic": 5, "BBC": 3, "YouTube": 1},
    }

def score_content(user, content):
    score = 0.0
    interest_score = sum([user["interests"].get(tag, 0) for tag in content["tags"]]) / max(len(content["tags"]), 1)
    score += interest_score * 0.4
    media_score = user["preferred_media_types"].get(content["media_type"], 0)
    score += media_score * 0.25
    engagement_boost = user["engagement_history"].get(content["source"], 0) / 5
    score += engagement_boost * 0.2
    try:
        days_old = (datetime.now() - datetime.fromisoformat(content["publish_date"])).days
    except ValueError:
        days_old = 0
    freshness_score = max(0, 1 - days_old / 30)
    score += freshness_score * 0.15
    return round(score, 3)

def fetch_stub_content() -> List[Dict]:
    return [
        {
            "title": "The Psychology of Focus",
            "url": "https://www.theatlantic.com/psychology-focus",
            "source": "The Atlantic",
            "media_type": "article",
            "tags": ["psychology"],
            "publish_date": "2025-07-10"
        },
        {
            "title": "How AI Is Changing the World",
            "url": "https://www.bbc.com/ai-world",
            "source": "BBC",
            "media_type": "video",
            "tags": ["tech", "news"],
            "publish_date": "2025-07-13"
        },
        {
            "title": "Deep Dive: Future of Work",
            "url": "https://podcasts.example.com/future-work",
            "source": "FuturePod",
            "media_type": "podcast",
            "tags": ["tech"],
            "publish_date": "2025-07-11"
        }
    ]

@app.get("/feed/{user_id}", response_model=List[ContentItem])
def get_personalized_feed(user_id: int, limit: int = 20):
    user = get_user_profile(user_id)
    contents = fetch_stub_content()
    for item in contents:
        item["score"] = score_content(user, item)
    contents.sort(key=lambda x: x["score"], reverse=True)
    return contents[:limit]

@app.post("/custom-query", response_model=CustomQueryResponse)
def custom_query(request: CustomQueryRequest):
    players = re.findall(r"(Ohtani|Judge|Trout|Elly De La Cruz|Acuna|Soto|Tatis)", request.query, re.IGNORECASE)
    media_types = []
    if re.search(r"(videos?|watch)", request.query, re.IGNORECASE):
        media_types.append("video")
    if re.search(r"(podcasts?|listen)", request.query, re.IGNORECASE):
        media_types.append("podcast")
    if re.search(r"(articles?|read|essay|deep[- ]?dive)", request.query, re.IGNORECASE):
        media_types.append("article")
    if not media_types:
        media_types = ["article", "podcast"]
    freshness = "high" if re.search(r"(stay updated|latest|daily|news)", request.query, re.IGNORECASE) else "flexible"
    return {
        "user_id": request.user_id,
        "original_query": request.query,
        "topics": ["fantasy baseball"] + players,
        "intent": "stay updated" if freshness == "high" else "general interest",
        "media_types": media_types,
        "freshness": freshness
    }
