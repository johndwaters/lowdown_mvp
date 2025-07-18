# database/db_handler.py
import sqlite3
from pathlib import Path
import json
from typing import Optional, Dict, Any, List

# Define the path to the database file
DB_PATH = Path(__file__).parent / "lowdown.db"

def dict_factory(cursor, row):
    """Convert query results into a dictionary."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    return conn



def init_db():
    """Initializes the database from the schema.sql file."""
    schema_path = Path(__file__).parent / "schema.sql"
    conn = get_db_connection()
    cursor = conn.cursor()
    with open(schema_path, 'r') as f:
        cursor.executescript(f.read())
    conn.commit()
    conn.close()

# --- Article Functions ---
def fetch_all_articles() -> List[Dict[str, Any]]:
    """Fetches all non-archived articles from the database, ordered by position."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Articles WHERE status != 'archived' ORDER BY position ASC")
    articles = cursor.fetchall()
    conn.close()
    return articles

def add_article(url: str, title: str = "", source: str = "", summary: str = "", status: str = "pending", position: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Adds a new article. If an article with the same URL exists and is
    archived, it un-archives it by setting its status to 'pending' and
    moving it to the top of the list. Otherwise, it returns None for conflicts.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if an article with this URL already exists
    cursor.execute("SELECT * FROM Articles WHERE url = ?", (url,))
    existing_article = cursor.fetchone()

    if existing_article:
        # If it exists and is archived, un-archive it.
        if existing_article['status'] == 'archived':
            # Get the highest position to move this article to the top.
            cursor.execute("SELECT MAX(position) as max_pos FROM Articles WHERE status != 'archived'")
            max_pos_row = cursor.fetchone()
            max_pos = max_pos_row['max_pos'] if max_pos_row and max_pos_row['max_pos'] is not None else 0
            new_position = max_pos + 1

            # Update status to 'pending' and set new position
            cursor.execute(
                "UPDATE Articles SET status = 'pending', position = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_position, existing_article['id'])
            )
            conn.commit()
            
            # Return the now-active article
            updated_article = get_article_by_id(existing_article['id'])
            conn.close()
            return updated_article
        else:
            # Article exists and is already active, so it's a conflict.
            conn.close()
            return None
    else:
        # Article doesn't exist, so create it.
        if position is None:
            cursor.execute("SELECT MAX(position) as max_pos FROM Articles")
            max_pos_row = cursor.fetchone()
            max_pos = max_pos_row['max_pos'] if max_pos_row and max_pos_row['max_pos'] is not None else 0
            position = max_pos + 1

        try:
            cursor.execute(
                "INSERT INTO Articles (url, title, source, summary, status, position) VALUES (?, ?, ?, ?, ?, ?)",
                (url, title, source, summary, status, position),
            )
            conn.commit()
            article_id = cursor.lastrowid
            conn.close()
            return get_article_by_id(article_id)
        except sqlite3.IntegrityError:  # Safeguard
            conn.close()
            return None

def get_article_by_id(article_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Articles WHERE id = ?", (article_id,))
    article = cursor.fetchone()
    conn.close()
    return article

def update_article_summary(article_id: int, summary: str, original_content: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE Articles 
               SET summary = ?, original_content = ?, status = 'summarized', updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (summary, original_content, article_id)
        )
        conn.commit()
    except sqlite3.Error:
        conn.close()
        return None

    if cursor.rowcount == 0:
        conn.close()
        return None

    cursor.execute("SELECT * FROM Articles WHERE id = ?", (article_id,))
    updated_article = cursor.fetchone()
    conn.close()
    return updated_article


def update_article(article_id: int, **update_data) -> Optional[Dict[str, Any]]:
    """Updates an article with the given data."""
    if not update_data:
        return get_article_by_id(article_id)

    conn = get_db_connection()
    cursor = conn.cursor()

    fields = []
    values = []
    for key, value in update_data.items():
        if key in ['url', 'title', 'source', 'original_content', 'summary', 'status', 'tags', 'position']:
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        conn.close()
        return get_article_by_id(article_id)

    fields.append("updated_at = CURRENT_TIMESTAMP")
    
    sql = f"UPDATE Articles SET {', '.join(fields)} WHERE id = ?"
    values.append(article_id)

    try:
        cursor.execute(sql, tuple(values))
        conn.commit()
    except sqlite3.Error:
        conn.close()
        return None

    if cursor.rowcount == 0:
        conn.close()
        return None

    cursor.execute("SELECT * FROM Articles WHERE id = ?", (article_id,))
    updated_article = cursor.fetchone()
    conn.close()
    return updated_article


def delete_article(article_id: int) -> bool:
    """Deletes an article by its ID and re-indexes the positions of remaining articles."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Delete the article itself
        cursor.execute("DELETE FROM Articles WHERE id = ?", (article_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return False # Article did not exist

        # Note: NewsletterArticles table doesn't exist in current schema
        # If it's added in the future, uncomment the line below:
        # cursor.execute("DELETE FROM NewsletterArticles WHERE article_id = ?", (article_id,))

        # Re-index the positions of the remaining non-archived articles
        cursor.execute("SELECT id FROM Articles WHERE status != 'archived' ORDER BY position ASC")
        remaining_articles = cursor.fetchall()
        
        for i, article in enumerate(remaining_articles):
            cursor.execute("UPDATE Articles SET position = ? WHERE id = ?", (i + 1, article['id']))
            
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Database error in delete_article: {e}")
        conn.close()
        return False

# --- Threat Functions ---
def _parse_threat_json_fields(threat: Dict[str, Any]) -> Dict[str, Any]:
    if threat:
        for field in ['specifications', 'operators']:
            if threat.get(field) and isinstance(threat[field], str):
                try:
                    threat[field] = json.loads(threat[field])
                except json.JSONDecodeError:
                    threat[field] = None
    return threat

def fetch_all_threats() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Threats ORDER BY created_at DESC")
    threats = cursor.fetchall()
    conn.close()
    return [_parse_threat_json_fields(threat) for threat in threats]

def add_threat(threat_data) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO Threats (name, type, country_of_origin, description, specifications, operators)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                threat_data.name,
                threat_data.type,
                threat_data.country_of_origin,
                threat_data.description,
                json.dumps(threat_data.specifications) if threat_data.specifications else None,
                json.dumps(threat_data.operators) if threat_data.operators else None,
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid
    except sqlite3.Error:
        conn.close()
        return None

    if new_id is None:
        conn.close()
        return None

    cursor.execute("SELECT * FROM Threats WHERE id = ?", (new_id,))
    new_threat = cursor.fetchone()
    conn.close()
    return _parse_threat_json_fields(new_threat)


def get_threat_by_id(threat_id: int) -> Optional[Dict[str, Any]]:
    """Fetches a single threat by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Threats WHERE id = ?", (threat_id,))
    threat = cursor.fetchone()
    conn.close()
    return _parse_threat_json_fields(threat)


def update_threat(threat_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Updates a threat with the given data."""
    if not update_data:
        return get_threat_by_id(threat_id)

    conn = get_db_connection()
    cursor = conn.cursor()

    fields = []
    values = []
    valid_fields = ['name', 'type', 'country_of_origin', 'description', 'specifications', 'operators', 'ioc_year', 'image_url', 'status', 'tod_summary']
    for key, value in update_data.items():
        if key in valid_fields:
            fields.append(f"{key} = ?")
            if key in ['specifications', 'operators']:
                values.append(json.dumps(value) if value is not None else None)
            else:
                values.append(value)

    if not fields:
        conn.close()
        return get_threat_by_id(threat_id)

    fields.append("updated_at = CURRENT_TIMESTAMP")
    sql = f"UPDATE Threats SET {', '.join(fields)} WHERE id = ?"
    values.append(threat_id)

    try:
        cursor.execute(sql, tuple(values))
        conn.commit()
    except sqlite3.Error:
        conn.close()
        return None

    if cursor.rowcount == 0:
        conn.close()
        return None

    return get_threat_by_id(threat_id)


def delete_threat(threat_id: int) -> bool:
    """Deletes a threat by its ID and unlinks it from newsletter issues."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Unlink from any newsletter issues before deleting
        cursor.execute("UPDATE NewsletterIssues SET featured_threat_id = NULL WHERE featured_threat_id = ?", (threat_id,))
        
        cursor.execute("DELETE FROM Threats WHERE id = ?", (threat_id,))
        conn.commit()
    except sqlite3.Error:
        conn.close()
        return False

    deleted_count = cursor.rowcount
    conn.close()
    return deleted_count > 0

# --- Podcast Functions ---
def fetch_all_podcast_episodes() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM PodcastEpisodes ORDER BY created_at DESC")
    episodes = cursor.fetchall()
    conn.close()
    return episodes

def add_podcast_episode(episode_data) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO PodcastEpisodes (title, podcast_url, description, published_date, image_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                episode_data.title,
                episode_data.podcast_url,
                episode_data.description,
                episode_data.published_date,
                episode_data.image_url,
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid
    except sqlite3.Error:
        conn.close()
        return None

    if new_id is None:
        conn.close()
        return None

    cursor.execute("SELECT * FROM PodcastEpisodes WHERE id = ?", (new_id,))
    new_episode = cursor.fetchone()
    conn.close()
    return new_episode


def get_podcast_episode_by_id(episode_id: int) -> Optional[Dict[str, Any]]:
    """Fetches a single podcast episode by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM PodcastEpisodes WHERE id = ?", (episode_id,))
    episode = cursor.fetchone()
    conn.close()
    return episode


def update_podcast_episode(episode_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Updates a podcast episode with the given data."""
    if not update_data:
        return get_podcast_episode_by_id(episode_id)

    conn = get_db_connection()
    cursor = conn.cursor()

    fields = []
    values = []
    valid_fields = ['title', 'podcast_url', 'description', 'published_date', 'image_url']
    for key, value in update_data.items():
        if key in valid_fields:
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        conn.close()
        return get_podcast_episode_by_id(episode_id)

    fields.append("updated_at = CURRENT_TIMESTAMP")
    sql = f"UPDATE PodcastEpisodes SET {', '.join(fields)} WHERE id = ?"
    values.append(episode_id)

    try:
        cursor.execute(sql, tuple(values))
        conn.commit()
    except sqlite3.Error:
        conn.close()
        return None

    if cursor.rowcount == 0:
        conn.close()
        return None

    return get_podcast_episode_by_id(episode_id)


def delete_podcast_episode(episode_id: int) -> bool:
    """Deletes a podcast episode by its ID and unlinks it from newsletter issues."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Unlink from any newsletter issues before deleting
        cursor.execute("UPDATE NewsletterIssues SET featured_podcast_id = NULL WHERE featured_podcast_id = ?", (episode_id,))
        
        cursor.execute("DELETE FROM PodcastEpisodes WHERE id = ?", (episode_id,))
        conn.commit()
    except sqlite3.Error:
        conn.close()
        return False

    deleted_count = cursor.rowcount
    conn.close()
    return deleted_count > 0

# --- Newsletter Functions ---
def create_newsletter_issue(title: str, article_ids: List[int]) -> Optional[Dict[str, Any]]:
    """
    Creates a new newsletter issue and links the provided articles to it.
    This is a single transaction.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Step 1: Create the newsletter issue record
        cursor.execute(
            "INSERT INTO NewsletterIssues (title) VALUES (?)",
            (title,)
        )
        issue_id = cursor.lastrowid
        if not issue_id:
            raise sqlite3.Error("Failed to retrieve last row ID for newsletter issue.")

        # Step 2: Link articles to the new issue
        if article_ids:
            for article_id in article_ids:
                cursor.execute(
                    "INSERT INTO NewsletterArticles (newsletter_id, article_id) VALUES (?, ?)",
                    (issue_id, int(article_id)) # Ensure article_id is int
                )
        
        conn.commit()

    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        # In a real app, you'd log this error.
        print(f"Database error in create_newsletter_issue: {e}")
        return None

    # Fetch the newly created issue to return it
    cursor.execute("SELECT * FROM NewsletterIssues WHERE id = ?", (issue_id,))
    new_issue = cursor.fetchone()
    conn.close()
    return new_issue

def fetch_all_newsletter_issues() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM NewsletterIssues ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows

def archive_newsletter_issue(issue_id: int) -> bool:
    """
    Archives a newsletter issue and all of its associated articles.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get all article IDs associated with the issue
        cursor.execute("SELECT article_id FROM NewsletterArticles WHERE newsletter_id = ?", (issue_id,))
        article_ids_tuples = cursor.fetchall()
        
        article_ids = [item['article_id'] for item in article_ids_tuples]

        # Update the newsletter issue status to 'archived'
        cursor.execute("UPDATE NewsletterIssues SET status = 'archived' WHERE id = ?", (issue_id,))
        
        # Update the status of all associated articles to 'archived'
        if article_ids:
            placeholders = ','.join(['?'] * len(article_ids))
            cursor.execute(f"UPDATE Articles SET status = 'archived' WHERE id IN ({placeholders})", article_ids)
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error during archiving: {e}")
        return False
    finally:
        conn.close()

def fetch_full_newsletter_issue(issue_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the main issue details
    cursor.execute("SELECT * FROM NewsletterIssues WHERE id = ?", (issue_id,))
    issue = cursor.fetchone()
    if not issue:
        conn.close()
        return None

    # Fetch linked articles
    cursor.execute("""
        SELECT a.* FROM Articles a
        JOIN NewsletterArticles na ON a.id = na.article_id
        WHERE na.newsletter_id = ?
    """, (issue_id,))
    issue['articles'] = cursor.fetchall()

    # Fetch featured threat
    if issue.get('featured_threat_id'):
        cursor.execute("SELECT * FROM Threats WHERE id = ?", (issue['featured_threat_id'],))
        issue['featured_threat'] = _parse_threat_json_fields(cursor.fetchone())

    # Fetch featured podcast
    if issue.get('featured_podcast_id'):
        cursor.execute("SELECT * FROM PodcastEpisodes WHERE id = ?", (issue['featured_podcast_id'],))
        issue['featured_podcast'] = cursor.fetchone()

    conn.close()
    return issue
