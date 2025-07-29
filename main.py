# main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

from database import db_handler
from services import ai_service, web_scraper, perplexity_service

from contextlib import asynccontextmanager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # on startup
    db_handler.init_db()
    yield
    # on shutdown
    print("Closing DB connection")

app = FastAPI(
    lifespan=lifespan,
    title="The Lowdown API",
    description="API for managing content for The Lowdown, a defense and aviation newsletter.",
    version="1.0.0"
)
print("=== THE LOWDOWN API SERVER STARTING UP ===")

# Health check endpoint for Railway
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "The Lowdown API"}

# --- Pydantic Models ---
class ArticleCreate(BaseModel):
    url: str
    title: Optional[str] = None
    summary: Optional[str] = None
    source: Optional[str] = 'Manual'

class Article(BaseModel):
    id: int
    url: str
    title: Optional[str] = None
    source: Optional[str] = None
    summary: Optional[str] = None
    status: str
    original_content: Optional[str] = None
    created_at: str
    updated_at: str
    model_config = ConfigDict(from_attributes=True)

class ArticleUpdate(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    source: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None

class ThreatCreate(BaseModel):
    name: str
    type: Optional[str] = Field(None, alias='threat_type')
    country_of_origin: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    operators: Optional[List[str]] = None

class Threat(BaseModel):
    id: int
    name: str
    type: Optional[str] = None
    country_of_origin: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    ioc_year: Optional[int] = None
    operators: Optional[List[str]] = None
    image_url: Optional[str] = None
    status: str
    created_at: str
    updated_at: str
    model_config = ConfigDict(from_attributes=True)

class ThreatUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = Field(None, alias='threat_type')
    country_of_origin: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    ioc_year: Optional[int] = None
    operators: Optional[List[str]] = None
    image_url: Optional[str] = None
    status: Optional[str] = None

class PodcastEpisodeCreate(BaseModel):
    title: str
    podcast_url: str
    description: Optional[str] = None
    published_date: Optional[str] = None
    image_url: Optional[str] = None

class PodcastEpisode(BaseModel):
    id: int
    title: str
    podcast_url: Optional[str] = None
    description: Optional[str] = None
    published_date: Optional[str] = None
    image_url: Optional[str] = None
    created_at: str
    updated_at: str
    model_config = ConfigDict(from_attributes=True)

class PodcastEpisodeUpdate(BaseModel):
    title: Optional[str] = None
    podcast_url: Optional[str] = None
    description: Optional[str] = None
    published_date: Optional[str] = None
    image_url: Optional[str] = None

class SummarizeRequest(BaseModel):
    article_id: int

class ManualSummarizeRequest(BaseModel):
    article_id: int
    manual_content: str

class NewsletterIssueCreate(BaseModel):
    title: str
    intro_text: Optional[str] = None
    outro_text: Optional[str] = None
    featured_threat_id: Optional[int] = None
    featured_podcast_id: Optional[int] = None

class NewsletterIssue(NewsletterIssueCreate):
    id: int
    publication_date: str
    created_at: str
    updated_at: str
    model_config = ConfigDict(from_attributes=True)

class NewsletterIssueFull(NewsletterIssue):
    articles: List[Article] = []
    featured_threat: Optional[Threat] = None
    featured_podcast: Optional[PodcastEpisode] = None

class AddArticlesToNewsletterRequest(BaseModel):
    article_ids: List[int]

class ThreatResearchRequest(BaseModel):
    threat_name: str

class ThreatResearchResponse(BaseModel):
    success: bool
    threat_name: str
    threat_type: str
    newsletter_format: Optional[str] = None
    research_format: Optional[str] = None
    research_content: Optional[str] = None
    citations: Optional[List[str]] = None
    error: Optional[str] = None

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to The Lowdown API"}

@app.get("/articles", response_model=List[Article])
def get_articles():
    return db_handler.fetch_all_articles()

@app.get("/articles/{article_id}", response_model=Article)
def get_article(article_id: int):
    article = db_handler.get_article_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found.")
    return article

@app.post("/articles", response_model=Article, status_code=201)
def create_article(article: ArticleCreate):
    print(f"--- Article creation started for URL: {article.url} ---")
    try:
        new_article = db_handler.add_article(
            url=article.url, 
            title=article.title, 
            source=article.source, 
            summary=article.summary
        )
        if not new_article:
            print(f"WARN: Article with URL {article.url} already exists.")
            raise HTTPException(status_code=409, detail=f"Article with URL {article.url} already exists.")
        
        print(f"--- Article created successfully with ID: {new_article['id']} ---")
        return new_article
    except HTTPException as e:
        # Re-raise HTTP exceptions directly to ensure FastAPI handles them correctly
        raise e
    except Exception as e:
        print(f"ERROR: Failed to create article for URL {article.url}. Unhandled exception: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.patch("/articles/{article_id}", response_model=Article)
def update_article(article_id: int, article_update: ArticleUpdate):
    update_data = article_update.model_dump(exclude_unset=True)
    updated_article = db_handler.update_article(article_id, **update_data)
    if not updated_article:
        raise HTTPException(status_code=404, detail="Article not found or update failed.")
    return updated_article

@app.delete("/articles/{article_id}", status_code=204)
def delete_article(article_id: int):
    if not db_handler.delete_article(article_id):
        raise HTTPException(status_code=404, detail="Article not found.")
    return

# --- Threats Endpoints ---
@app.get("/threats", response_model=List[Threat])
def get_threats():
    return db_handler.fetch_all_threats()

@app.get("/threats/{threat_id}", response_model=Threat)
def get_threat(threat_id: int):
    threat = db_handler.get_threat_by_id(threat_id)
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found.")
    return threat

@app.post("/threats", response_model=Threat, status_code=201)
def create_threat(threat: ThreatCreate):
    new_threat = db_handler.add_threat(threat)
    if not new_threat:
        raise HTTPException(status_code=500, detail="Failed to create threat.")
    return new_threat

@app.patch("/threats/{threat_id}", response_model=Threat)
def update_threat(threat_id: int, threat_update: ThreatUpdate):
    update_data = threat_update.model_dump(exclude_unset=True, by_alias=True)
    updated_threat = db_handler.update_threat(threat_id, update_data)
    if not updated_threat:
        raise HTTPException(status_code=404, detail="Threat not found or update failed.")
    return updated_threat

@app.delete("/threats/{threat_id}", status_code=204)
def delete_threat(threat_id: int):
    if not db_handler.delete_threat(threat_id):
        raise HTTPException(status_code=404, detail="Threat not found.")
    return

# --- Podcasts Endpoints ---
@app.get("/podcasts", response_model=List[PodcastEpisode])
def get_podcasts():
    return db_handler.fetch_all_podcast_episodes()

@app.get("/podcasts/{episode_id}", response_model=PodcastEpisode)
def get_podcast_episode(episode_id: int):
    episode = db_handler.get_podcast_episode_by_id(episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Podcast episode not found.")
    return episode

@app.post("/podcasts", response_model=PodcastEpisode, status_code=201)
def create_podcast_episode(episode: PodcastEpisodeCreate):
    new_episode = db_handler.add_podcast_episode(episode)
    if not new_episode:
        raise HTTPException(status_code=500, detail="Failed to create podcast episode.")
    return new_episode

@app.patch("/podcasts/{episode_id}", response_model=PodcastEpisode)
def update_podcast_episode(episode_id: int, episode_update: PodcastEpisodeUpdate):
    update_data = episode_update.model_dump(exclude_unset=True)
    updated_episode = db_handler.update_podcast_episode(episode_id, update_data)
    if not updated_episode:
        raise HTTPException(status_code=404, detail="Podcast episode not found or update failed.")
    return updated_episode

@app.delete("/podcasts/{episode_id}", status_code=204)
def delete_podcast_episode(episode_id: int):
    if not db_handler.delete_podcast_episode(episode_id):
        raise HTTPException(status_code=404, detail="Podcast episode not found.")
    return

@app.post("/summarize", response_model=Article)
def summarize_article(request: SummarizeRequest):
    print(f"--- Summarization started for article_id: {request.article_id} ---")
    article = db_handler.get_article_by_id(request.article_id)
    if not article:
        print(f"ERROR: Article not found for article_id: {request.article_id}")
        raise HTTPException(status_code=404, detail="Article not found.")

    print(f"Step 1: Scraping content from {article['url']}")
    try:
        content = web_scraper.fetch_and_parse_url(article['url'])
        if not content:
            print(f"ERROR: No content found at URL for article_id: {request.article_id}")
            db_handler.update_article(request.article_id, status='scraping_failed', summary='No content found at URL.')
            raise HTTPException(status_code=400, detail="Failed to fetch or parse article content: No content found.")
        print("Step 1: Scraping successful.")
    except Exception as e:
        error_message = f"Scraping error: {str(e)}"
        print(f"ERROR: {error_message} for article_id: {request.article_id}")
        db_handler.update_article(request.article_id, status='scraping_failed', summary=error_message)
        raise HTTPException(status_code=500, detail=error_message)

    print("Step 2: Getting summary from AI service.")
    try:
        ai_data = ai_service.get_ai_summary(title=article.get('title', ''), content=content, url=article['url'])
        print("Step 2: AI summary received.")
    except Exception as e:
        error_message = f"AI service error: {str(e)}"
        print(f"ERROR: {error_message} for article_id: {request.article_id}")
        db_handler.update_article(request.article_id, status='ai_failed', summary=error_message)
        raise HTTPException(status_code=500, detail=error_message)

    print("Step 3: Updating article in database.")
    update_payload = {
        "title": ai_data.get("title"),
        "summary": ai_data.get("summary_body"),
        "original_content": content,
        "status": "summarized"
    }
    
    updated_article = db_handler.update_article(
        article_id=request.article_id,
        **update_payload
    )

    if not updated_article:
        print(f"ERROR: Failed to update article after summarization for article_id: {request.article_id}")
        raise HTTPException(status_code=500, detail="Failed to update article after summarization.")

    print(f"--- Summarization successful for article_id: {request.article_id} ---")
    return updated_article

@app.post("/summarize-manual", response_model=Article)
def summarize_article_manual(request: ManualSummarizeRequest):
    print(f"--- Manual summarization started for article_id: {request.article_id} ---")
    article = db_handler.get_article_by_id(request.article_id)
    if not article:
        print(f"ERROR: Article not found for article_id: {request.article_id}")
        raise HTTPException(status_code=404, detail="Article not found.")

    print("Step 1: Using manually provided content (bypassing web scraping).")
    content = request.manual_content.strip()
    if not content:
        print(f"ERROR: No manual content provided for article_id: {request.article_id}")
        db_handler.update_article(request.article_id, status='content_failed', summary='No manual content provided.')
        raise HTTPException(status_code=400, detail="Manual content cannot be empty.")
    
    print("Step 2: Getting summary from AI service.")
    try:
        ai_data = ai_service.get_ai_summary(title=article.get('title', ''), content=content, url=article['url'])
        print("Step 2: AI summary received.")
    except Exception as e:
        error_message = f"AI service error: {str(e)}"
        print(f"ERROR: {error_message} for article_id: {request.article_id}")
        db_handler.update_article(request.article_id, status='ai_failed', summary=error_message)
        raise HTTPException(status_code=500, detail=error_message)

    print("Step 3: Updating article in database.")
    update_payload = {
        "title": ai_data.get("title"),
        "summary": ai_data.get("summary_body"),
        "original_content": content,
        "status": "summarized"
    }
    
    updated_article = db_handler.update_article(
        article_id=request.article_id,
        **update_payload
    )

    if not updated_article:
        print(f"ERROR: Failed to update article after manual summarization for article_id: {request.article_id}")
        raise HTTPException(status_code=500, detail="Failed to update article after summarization.")

    print(f"--- Manual summarization successful for article_id: {request.article_id} ---")
    return updated_article

@app.post("/newsletters", response_model=NewsletterIssue, status_code=201)
def create_newsletter_issue(issue: NewsletterIssueCreate):
    return db_handler.create_newsletter_issue(issue)

@app.get("/newsletters", response_model=List[NewsletterIssue])
def list_newsletter_issues():
    return db_handler.fetch_all_newsletter_issues()

@app.get("/newsletters/{issue_id}", response_model=NewsletterIssueFull)
def get_newsletter_issue(issue_id: int):
    issue = db_handler.fetch_full_newsletter_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Newsletter issue not found.")
    return issue

@app.post("/newsletters/{issue_id}/archive", status_code=200)
def archive_newsletter_issue(issue_id: int):
    success = db_handler.archive_newsletter_issue(issue_id)
    if not success:
        raise HTTPException(status_code=404, detail="Newsletter issue not found or already archived.")
    return {"message": "Newsletter issue and associated articles have been archived."}

@app.post("/newsletters/{issue_id}/articles", status_code=204)
def add_articles_to_newsletter(issue_id: int, request: AddArticlesToNewsletterRequest):
    db_handler.add_articles_to_newsletter(issue_id, request.article_ids)
    return

@app.get("/newsletters/{issue_id}/export", response_class=PlainTextResponse)
def export_newsletter(issue_id: int):
    issue = db_handler.fetch_full_newsletter_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Newsletter issue not found.")
    markdown = f"# {issue['title']}\n\n"
    if issue.get('intro_text'):
        markdown += f"{issue['intro_text']}\n\n"
    markdown += "## 🎯 Top Stories\n\n"
    for article in issue.get('articles', []):
        markdown += f"{article['summary']}\n\n"
    if issue.get('featured_threat'):
        threat = issue['featured_threat']
        markdown += f"## Threat of the Day: {threat['name']}\n\n{threat.get('description', '')}\n\n"
    if issue.get('featured_podcast'):
        podcast = issue['featured_podcast']
        markdown += f"## 🎙️ Podcast Episode: {podcast['title']}\n\n{podcast.get('description', '')}\n\n"
    if issue.get('outro_text'):
        markdown += f"{issue['outro_text']}\n"
    return PlainTextResponse(content=markdown)

# --- Threat Research Endpoint ---
@app.post("/research-threat", response_model=ThreatResearchResponse)
def research_threat(request: ThreatResearchRequest):
    """
    Research a military threat using Perplexity AI and return formatted profile.
    """
    try:
        # Get Perplexity API key from environment
        perplexity_api_key = os.environ.get("PERPLEXITY_API_KEY")
        if not perplexity_api_key:
            return ThreatResearchResponse(
                success=False,
                threat_name=request.threat_name,
                threat_type="unknown",
                error="Perplexity API key not configured"
            )
        
        # Create Perplexity service and research threat
        perplexity = perplexity_service.create_perplexity_service(perplexity_api_key)
        research_data = perplexity.research_threat(request.threat_name)
        
        if research_data["success"]:
            formatted_profiles = perplexity.format_threat_profile(research_data)
            return ThreatResearchResponse(
                success=True,
                threat_name=research_data["threat_name"],
                threat_type=research_data["threat_type"],
                newsletter_format=formatted_profiles["newsletter_format"],
                research_format=formatted_profiles["research_format"],
                research_content=research_data["research_content"],
                citations=research_data.get("citations", [])
            )
        else:
            return ThreatResearchResponse(
                success=False,
                threat_name=request.threat_name,
                threat_type=research_data.get("threat_type", "unknown"),
                error=research_data.get("error", "Unknown research error")
            )
            
    except Exception as e:
        return ThreatResearchResponse(
            success=False,
            threat_name=request.threat_name,
            threat_type="unknown",
            error=f"Server error: {str(e)}"
        )

# Server startup configuration for Railway deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
