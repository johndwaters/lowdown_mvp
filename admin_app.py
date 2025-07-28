# admin_app.py
import streamlit as st
import requests
from database import db_handler

# --- Page Config ---
st.set_page_config(page_title="The Lowdown Admin", layout="wide")

# --- Config ---
API_URL = "https://lowdownmvp-production.up.railway.app"

# --- Note: Using Railway API, no local DB needed ---

# Function to fetch articles from Railway API
def fetch_articles_from_api():
    """Fetch articles from Railway API instead of local database"""
    try:
        response = requests.get(f"{API_URL}/articles")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch articles from Railway: {e}")
        return []

# --- Styling ---
st.markdown("""<style>
html, body, [class*="st-"], [class*="css-"] { font-family: 'Helvetica', 'Arial', sans-serif; }
.stButton>button { width: 100%; }
</style>""", unsafe_allow_html=True)

# --- Helper Functions ---
def format_summary_for_export(row):
    """Returns the pre-formatted summary from the article row."""
    return (row.get('summary') or '').strip()

def move_article(article_id, direction):
    """Moves an article up or down in the list."""
    articles = fetch_articles_from_api()
    # Create a list of IDs in the current order
    ordered_ids = [a['id'] for a in articles]
    
    # Find the index of the article to move
    try:
        current_index = ordered_ids.index(article_id)
    except ValueError:
        return # Article not in the list

    # Determine the new index
    if direction == 'up' and current_index > 0:
        new_index = current_index - 1
        # Swap with the article above
        ordered_ids[current_index], ordered_ids[new_index] = ordered_ids[new_index], ordered_ids[current_index]
    elif direction == 'down' and current_index < len(ordered_ids) - 1:
        new_index = current_index + 1
        # Swap with the article below
        ordered_ids[current_index], ordered_ids[new_index] = ordered_ids[new_index], ordered_ids[current_index]
    else:
        return # Can't move further

    # Update the position for all articles based on the new order
    for index, an_id in enumerate(ordered_ids):
        db_handler.update_article(an_id, position=index)
    st.rerun()

# --- Main App ---
st.title("The Lowdown - Content Curation")

# --- Session State Initialization ---
if 'threat_of_day_id' not in st.session_state:
    st.session_state.threat_of_day_id = None

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📝 Article Curation", "🔥 Threat of the Day", "🚀 Export"])

with tab1:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📥 Input")
        with st.form("add_articles_form"):
            urls_to_add = st.text_area("Article URLs", height=150, placeholder="Paste one or more URLs, one per line...")
            if st.form_submit_button("Import Articles"):
                urls = [url.strip() for url in urls_to_add.splitlines() if url.strip()]
                if urls:
                    success_count = 0
                    for url in urls:
                        try:
                            # Pass the URL as the default title, as the backend requires it.
                            response = requests.post(f"{API_URL}/articles", json={"url": url, "title": url, "source": "manual_add"})
                            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                            success_count += 1
                        except requests.exceptions.HTTPError as e:
                            if e.response.status_code == 409:
                                st.toast(f"Article already in list: {url.split('/')[-2][:30]}...", icon="⚠️")
                            else:
                                st.error(f"Failed to add {url}: {e}")
                        except requests.exceptions.RequestException as e:
                            st.error(f"Failed to add {url}: {e}")
                    
                    if success_count > 0:
                        st.toast(f"Successfully imported {success_count} article(s).", icon="✅")
                        st.rerun()

                else:
                    st.warning("Please enter at least one URL.")

        st.subheader("🤖 Actions")
        if st.button("Summarize All Pending Articles"):
            pending_articles = [a for a in fetch_articles_from_api() if a['status'] == 'pending']
            if not pending_articles:
                st.toast("No pending articles to summarize.", icon="👍")
            else:
                progress_bar = st.progress(0, text="Summarizing...")
                for i, article in enumerate(pending_articles):
                    try:
                        requests.post(f"{API_URL}/summarize", json={"article_id": article['id']})
                    except Exception as e:
                        db_handler.update_article(article['id'], status='summarization_failed')
                    progress_bar.progress((i + 1) / len(pending_articles), text=f"Summarized {i+1}/{len(pending_articles)}")
                st.success("Summarization complete!")
                st.rerun()

    with col2:
        st.subheader("📄 Articles")
        articles = fetch_articles_from_api()
        if not articles:
            st.info("No articles in the database. Add some using the form on the left.")
        else:
            for i, article in enumerate(articles):
                with st.container(border=True):
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.caption(f"#{article.get('position', i+1)} | Status: {article.get('status', 'N/A')} | Source: {article.get('source', 'N/A')}")

                    with c2:
                        # --- Reordering Buttons ---
                        sub_c1, sub_c2 = st.columns(2)
                        with sub_c1:
                            st.button("⬆️", key=f"up_{article['id']}", on_click=move_article, args=(article['id'], 'up'), help="Move Up")
                        with sub_c2:
                            st.button("⬇️", key=f"down_{article['id']}", on_click=move_article, args=(article['id'], 'down'), help="Move Down")

                    # Display the summary, with a fallback message if it's empty
                    summary_display = (article.get('summary') or '').strip()
                    if summary_display:
                        st.markdown(summary_display)
                    else:
                        st.info("This article has not been summarized yet.")

                    with st.expander("Edit Summary"):
                        summary_text = st.text_area("Summary Editor", value=article.get('summary', ''), height=150, key=f"summary_{article['id']}")
                        if st.button("Save Summary", key=f"save_{article['id']}"):
                            db_handler.update_article(article['id'], summary=summary_text)
                            st.toast("Summary saved!", icon="✅")
                            st.rerun()
                    
                    with st.expander("📝 Manual Content (Bypass Web Scraping)"):
                        st.info("Use this if the website has a paywall or the scraper can't access the content. Paste the article text below and click 'Summarize Manual Content'.")
                        manual_content = st.text_area(
                            "Article Content", 
                            placeholder="Paste the full article content here...", 
                            height=200, 
                            key=f"manual_content_{article['id']}"
                        )
                        if st.button("🤖 Summarize Manual Content", key=f"manual_sum_{article['id']}"):
                            if manual_content.strip():
                                try:
                                    response = requests.post(f"{API_URL}/summarize-manual", json={
                                        "article_id": article['id'],
                                        "manual_content": manual_content
                                    })
                                    response.raise_for_status()
                                    st.toast("Manual summarization completed!", icon="✅")
                                    st.rerun()
                                except requests.exceptions.RequestException as e:
                                    st.error(f"Failed to summarize manual content: {e}")
                            else:
                                st.warning("Please paste some article content first.")

                    # --- Action Buttons ---
                    btn_cols = st.columns(4)
                    if btn_cols[0].button("Re-summarize", key=f"resum_{article['id']}"):
                        requests.post(f"{API_URL}/summarize", json={"article_id": article['id']})
                        st.toast("Re-summarization started.")
                        st.rerun()
                    
                    current_status = article.get('status')
                    if current_status != 'accepted':
                        if btn_cols[1].button("✅ Accept", key=f"accept_{article['id']}"):
                            try:
                                response = requests.patch(f"{API_URL}/articles/{article['id']}", json={"status": "accepted"})
                                response.raise_for_status()
                                st.toast("Article accepted!", icon="✅")
                                st.rerun()
                            except requests.exceptions.RequestException as e:
                                st.error(f"Failed to accept article: {e}")
                    else:
                        if btn_cols[1].button("↩️ Un-accept", key=f"unaccept_{article['id']}"):
                            try:
                                response = requests.patch(f"{API_URL}/articles/{article['id']}", json={"status": "summarized"})
                                response.raise_for_status()
                                st.toast("Article un-accepted!", icon="↩️")
                                st.rerun()
                            except requests.exceptions.RequestException as e:
                                st.error(f"Failed to un-accept article: {e}")

                    if btn_cols[2].button("Archive", key=f"archive_{article['id']}"):
                        try:
                            response = requests.patch(f"{API_URL}/articles/{article['id']}", json={"status": "archived"})
                            response.raise_for_status()
                            st.toast("Article archived!", icon="📦")
                            st.rerun()
                        except requests.exceptions.RequestException as e:
                            st.error(f"Failed to archive article: {e}")
                    
                    if btn_cols[3].button("🗑️ Delete", key=f"delete_{article['id']}"):
                        try:
                            response = requests.delete(f"{API_URL}/articles/{article['id']}")
                            response.raise_for_status() # Raise an exception for bad status codes
                            st.toast(f"Article deleted.", icon="🗑️")
                            st.rerun()
                        except requests.exceptions.RequestException as e:
                            st.error(f"Failed to delete article: {e}")

with tab2:
    st.header("🔥 Threat of the Day")
    threats = db_handler.fetch_all_threats()
    threat_options = {t['name']: t['id'] for t in threats}

    selected_threat_name = st.selectbox("Select a Threat", options=threat_options.keys())

    if selected_threat_name:
        threat_id = threat_options[selected_threat_name]
        st.session_state.threat_of_day_id = threat_id
        threat = db_handler.get_threat_by_id(threat_id)
        
        st.subheader(f"Editing: {threat['name']}")
        st.text(f"Type: {threat.get('type', 'N/A')} | Country: {threat.get('country_of_origin', 'N/A')}")

        tod_summary = st.text_area(
            "Threat of the Day Summary", 
            value=threat.get('tod_summary', ''), 
            height=200,
            key=f"tod_summary_{threat_id}"
        )

        if st.button("Save Threat Summary"):
            db_handler.update_threat(threat_id, {'tod_summary': tod_summary})
            st.toast("Threat summary saved!", icon="✅")
            st.rerun()

with tab3:
    st.header("🚀 Export Newsletter")

    # 1. Get Accepted Articles
    accepted_articles = [a for a in fetch_articles_from_api() if a['status'] == 'accepted']
    
    # 2. Get Threat of the Day
    threat_of_day = None
    if st.session_state.threat_of_day_id:
        threat_of_day = db_handler.get_threat_by_id(st.session_state.threat_of_day_id)

    if not accepted_articles:
        st.warning("No 'accepted' articles to export. Please accept some articles in the 'Article Curation' tab.")
    else:
        st.subheader("Final Preview")
        
        # Build the newsletter content
        final_content = ""
        for article in accepted_articles:
            final_content += format_summary_for_export(article) + "\n\n---\n\n"
        
        if threat_of_day and threat_of_day.get('tod_summary'):
            final_content += "## Threat of the Day\n\n"
            final_content += f"**{threat_of_day['name']}**\n\n"
            final_content += threat_of_day['tod_summary']

        st.text_area("Copy to Beehiiv", value=final_content, height=400)
        st.caption("Click in the box and press Cmd+A then Cmd+C to copy.")

        if st.button("Archive Articles & Clear", type="primary"):
            for article in accepted_articles:
                db_handler.update_article(article['id'], status='archived')
            st.session_state.threat_of_day_id = None
            st.toast("Newsletter content archived!", icon="📦")
            st.rerun()
