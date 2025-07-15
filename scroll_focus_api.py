
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
import sqlite3
import re

# ---------- CONFIG ----------
DB_PATH = "/mnt/data/scroll_focus_content.db"

# ---------- MODELS ----------
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

# ---------- FASTAPI ----------
app = FastAPI(title="Scroll Focus API", version="0.2")

# ---------- USER PROFILE (stub) ----------
def get_user_profile(user_id: int) -> Dict:
    return {
        "interests": {"psychology": 0.9, "tech": 0.7, "news": 0.4},
        "preferred_media_types": {"article": 1.0, "podcast": 0.7, "video": 0.5},
        "depth_preference": "short",
        "engagement_history": {"The Atlantic": 5, "BBC": 3, "YouTube": 1},
    }

# ---------- SCORING ----------
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

# ---------- FETCH CONTENT ----------
def fetch_content(limit: int = 50) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, url, source, media_type, tags, publish_date FROM content LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    contents = []
    for row in rows:
        title, url, source, media_type, tags, publish_date = row
        contents.append({
            "title": title,
            "url": url,
            "source": source,
            "media_type": media_type,
            "tags": tags.split(','),
            "publish_date": publish_date
        })
    return contents

# ---------- ENDPOINTS ----------
@app.get("/feed/{user_id}", response_model=List[ContentItem])
def get_personalized_feed(user_id: int, limit: int = 20):
    user = get_user_profile(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    contents = fetch_content(limit=100)
    ranked = []
    for item in contents:
        item["score"] = score_content(user, item)
        ranked.append(item)
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:limit]

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
