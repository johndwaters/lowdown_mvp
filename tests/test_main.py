# tests/test_main.py

import pytest
import os
from fastapi.testclient import TestClient
import sqlite3
from main import app
from database import db_handler

@pytest.fixture(scope="function")
def client(tmp_path):
    """
    Fixture to create a fresh, temporary database for each test function
    and provide a TestClient instance.
    """
    db_path = tmp_path / "test_lowdown.db"
    
    conn = sqlite3.connect(db_path)
    with open("database/schema.sql") as f:
        conn.executescript(f.read())
    conn.close()

    original_db_path = db_handler.DB_PATH
    # The TestClient will trigger the startup event, which runs init_db.
    db_handler.DB_PATH = str(db_path)

    with TestClient(app) as client:
        yield client

    # Teardown: restore original DB path and clean up test DB
    db_handler.DB_PATH = original_db_path


def test_read_root(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to The Lowdown API"}


def test_get_articles_empty(client):
    """Test the /articles endpoint, which should initially be an empty list."""
    response = client.get("/articles")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 0


def test_create_and_get_article(client):
    """Test creating a new article and then fetching it."""
    article_data = {"url": "http://test-article.com/1", "title": "Test Article 1"}
    response = client.post("/articles", json=article_data)
    assert response.status_code == 201
    created_article = response.json()
    assert created_article["url"] == article_data["url"]
    assert created_article["title"] == article_data["title"]

    response = client.get("/articles")
    assert response.status_code == 200
    articles = response.json()
    assert len(articles) == 1
    assert articles[0]["url"] == article_data["url"]


def test_create_duplicate_article(client):
    """Test that creating an article with a duplicate URL fails."""
    article_data = {"url": "http://duplicate-article.com/1", "title": "Duplicate Test"}
    response = client.post("/articles", json=article_data)
    assert response.status_code == 201

    response = client.post("/articles", json=article_data)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_update_article(client):
    """Test updating an article's title."""
    create_res = client.post("/articles", json={"url": "http://example.com/updatable", "title": "Original Title"})
    assert create_res.status_code == 201
    article_id = create_res.json()["id"]

    update_data = {"title": "Updated Title"}
    update_res = client.patch(f"/articles/{article_id}", json=update_data)
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Title"

    get_res = client.get(f"/articles/{article_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Updated Title"


def test_delete_article(client):
    """Test deleting an article."""
    create_res = client.post("/articles", json={"url": "http://example.com/deletable", "title": "To Be Deleted"})
    assert create_res.status_code == 201
    article_id = create_res.json()["id"]

    delete_res = client.delete(f"/articles/{article_id}")
    assert delete_res.status_code == 204

    get_res = client.get(f"/articles/{article_id}")
    assert get_res.status_code == 404


def test_get_threats_empty(client):
    """Test the /threats endpoint, which should initially be an empty list."""
    response = client.get("/threats")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 0


def test_create_and_get_threat(client):
    """Test creating a new threat and then fetching it."""
    threat_data = {
        "name": "S-400 Triumf",
        "type": "SAM",
        "country_of_origin": "Russia",
        "specifications": {"range": "400 km"},
        "operators": ["Russia", "China"],
    }
    response = client.post("/threats", json=threat_data)
    assert response.status_code == 201
    created_threat = response.json()
    assert created_threat["name"] == threat_data["name"]
    assert created_threat["specifications"]["range"] == "400 km"

    response = client.get("/threats")
    assert response.status_code == 200
    threats = response.json()
    assert len(threats) == 1
    assert threats[0]["name"] == threat_data["name"]


def test_update_threat(client):
    """Test updating a threat's name."""
    threat_data = {"name": "Original Threat Name", "type": "SAM"}
    create_res = client.post("/threats", json=threat_data)
    assert create_res.status_code == 201
    threat_id = create_res.json()["id"]

    update_data = {"name": "Updated Threat Name"}
    update_res = client.patch(f"/threats/{threat_id}", json=update_data)
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated Threat Name"

    get_res = client.get(f"/threats/{threat_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Updated Threat Name"


def test_delete_threat(client):
    """Test deleting a threat."""
    threat_data = {"name": "To Be Deleted", "type": "SAM"}
    create_res = client.post("/threats", json=threat_data)
    assert create_res.status_code == 201
    threat_id = create_res.json()["id"]

    delete_res = client.delete(f"/threats/{threat_id}")
    assert delete_res.status_code == 204

    get_res = client.get(f"/threats/{threat_id}")
    assert get_res.status_code == 404


def test_get_podcast_episodes_empty(client):
    """Test the /podcasts endpoint, which should initially be an empty list."""
    response = client.get("/podcasts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 0


def test_create_and_get_podcast_episode(client):
    """Test creating a new podcast episode and then fetching it."""
    episode_data = {
        "title": "Episode 1: The Future of Air Combat",
        "podcast_url": "http://example.com/podcast/1",
        "description": "A discussion about 6th generation fighters.",
        "published_date": "2025-06-26",
        "image_url": "http://example.com/image.jpg"
    }
    response = client.post("/podcasts", json=episode_data)
    assert response.status_code == 201
    created_episode = response.json()
    assert created_episode["title"] == episode_data["title"]
    assert created_episode["podcast_url"] == episode_data["podcast_url"]

    response = client.get("/podcasts")
    assert response.status_code == 200
    episodes = response.json()
    assert len(episodes) == 1
    assert episodes[0]["title"] == episode_data["title"]


def test_update_podcast_episode(client):
    """Test updating a podcast episode's title."""
    episode_data = {"title": "Original Episode Title", "podcast_url": "http://example.com/podcast/update"}
    create_res = client.post("/podcasts", json=episode_data)
    assert create_res.status_code == 201
    episode_id = create_res.json()["id"]

    update_data = {"title": "Updated Episode Title"}
    update_res = client.patch(f"/podcasts/{episode_id}", json=update_data)
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Episode Title"

    get_res = client.get(f"/podcasts/{episode_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Updated Episode Title"


def test_delete_podcast_episode(client):
    """Test deleting a podcast episode."""
    episode_data = {"title": "To Be Deleted", "podcast_url": "http://example.com/podcast/delete"}
    create_res = client.post("/podcasts", json=episode_data)
    assert create_res.status_code == 201
    episode_id = create_res.json()["id"]

    delete_res = client.delete(f"/podcasts/{episode_id}")
    assert delete_res.status_code == 204

    get_res = client.get(f"/podcasts/{episode_id}")
    assert get_res.status_code == 404


def test_summarize_article(client, mocker):
    """Test the /summarize endpoint, mocking the AI and web scraper services."""
    # 1. Create an article to summarize
    article_data = {"url": "http://example.com/article1", "title": "Test Article for Summarization"}
    response = client.post("/articles", json=article_data)
    assert response.status_code == 201
    created_article = response.json()
    article_id = created_article["id"]

    # 2. Mock the external services
    mock_content = "This is a long article content that needs to be summarized."
    mock_summary = "🎯 Mock Summary: This is a test summary."
    mocker.patch("services.web_scraper.fetch_and_parse_url", return_value=mock_content)
    mocker.patch("services.ai_service.get_ai_summary", return_value=mock_summary)

    # 3. Call the summarize endpoint
    response = client.post("/summarize", json={"article_id": article_id})
    assert response.status_code == 200
    summarized_article = response.json()

    # 4. Verify the result
    assert summarized_article["id"] == article_id
    assert summarized_article["status"] == "summarized"
    assert summarized_article["summary"] == mock_summary
    assert summarized_article["original_content"] == mock_content


# @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
# def test_summarize_article_integration(client):
#     """Integration test for the /summarize endpoint calling the actual OpenAI API."""
    # 1. Create an article with a real, stable URL
    article_data = {
        "url": "https://en.wikipedia.org/wiki/General_Dynamics_F-16_Fighting_Falcon",
        "title": "General Dynamics F-16 Fighting Falcon"
    }
    article_res = client.post("/articles", json=article_data)
    assert article_res.status_code == 201
    article_id = article_res.json()["id"]

    # 2. Call the summarize endpoint (no mocking)
    summarize_res = client.post("/summarize", json={"article_id": article_id})
    assert summarize_res.status_code == 200
    summary_data = summarize_res.json()

    # 3. Verify the result
    assert summary_data["id"] == article_id
    assert summary_data["summary"] is not None
    assert "Error" not in summary_data["summary"]
    assert "🎯" in summary_data["summary"] # Check for expected format
    print(f"Generated Summary: {summary_data['summary']}")


def test_newsletter_workflow(client):
    """
    Tests the full newsletter workflow:
    1. Create associated content (articles, threat, podcast).
    2. Create a newsletter issue.
    3. Link articles to the issue.
    4. Fetch the full issue and verify its contents.
    5. Export the issue as Markdown and verify the format.
    """
    # Step 1: Create prerequisite content
    threat_data = {"name": "T-14 Armata", "description": "Next-gen Russian MBT.", "specifications": {"weight": "55 tons"}, "operators": ["Russia"]}
    threat_res = client.post("/threats", json=threat_data)
    assert threat_res.status_code == 201
    threat_id = threat_res.json()["id"]

    podcast_data = {"title": "Air Power Analysis", "podcast_url": "http://example.com/podcast.mp3", "description": "Discussing F-35 logistics."}
    podcast_res = client.post("/podcasts", json=podcast_data)
    assert podcast_res.status_code == 201
    podcast_id = podcast_res.json()["id"]

    article1_res = client.post("/articles", json={"url": "http://example.com/article-a", "title": "Article A", "summary": "Summary for A."})
    article2_res = client.post("/articles", json={"url": "http://example.com/article-b", "title": "Article B", "summary": "Summary for B."})
    assert article1_res.status_code == 201
    assert article2_res.status_code == 201
    article1_id = article1_res.json()["id"]
    article2_id = article2_res.json()["id"]

    # Step 2: Create a newsletter issue
    issue_data = {
        "title": "Weekly Briefing",
        "intro_text": "Welcome to this week's issue.",
        "outro_text": "See you next week!",
        "featured_threat_id": threat_id,
        "featured_podcast_id": podcast_id
    }
    issue_res = client.post("/newsletters", json=issue_data)
    assert issue_res.status_code == 201
    issue_id = issue_res.json()["id"]

    # Step 3: Link articles to the issue
    link_res = client.post(f"/newsletters/{issue_id}/articles", json={"article_ids": [article1_id, article2_id]})
    assert link_res.status_code == 204

    # Step 4: Fetch the full newsletter issue and verify
    full_issue_res = client.get(f"/newsletters/{issue_id}")
    assert full_issue_res.status_code == 200
    full_issue = full_issue_res.json()
    
    assert full_issue["title"] == "Weekly Briefing"
    assert len(full_issue["articles"]) == 2
    assert full_issue["featured_threat"]["id"] == threat_id
    assert full_issue["featured_podcast"]["id"] == podcast_id

    # Step 5: Export as Markdown and verify
    export_res = client.get(f"/newsletters/{issue_id}/export")
    assert export_res.status_code == 200
    markdown = export_res.text
    
    assert "# Weekly Briefing" in markdown
    assert "Welcome to this week's issue." in markdown
    assert "Summary for A." in markdown
    assert "## Threat of the Day: T-14 Armata" in markdown
    assert "## 🎙️ Podcast Episode: Air Power Analysis" in markdown
    assert "See you next week!" in markdown
