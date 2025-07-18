# pages/archive.py
import streamlit as st
import sys
import os

# Add parent directory to path to import db_handler
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import db_handler

st.set_page_config(layout="wide")

st.title("Archived Newsletters")

st.info("This page shows all previously created and archived newsletter issues.")

# This is a placeholder. The actual function to fetch archived issues will be implemented next.
try:
    # We assume a function or a filter will be added to fetch only archived issues
    all_issues = db_handler.fetch_all_newsletter_issues()
    archived_issues = [issue for issue in all_issues if issue.get('status') == 'archived']
except Exception as e:
    st.error(f"Failed to connect to the database or fetch issues: {e}")
    archived_issues = []

if not archived_issues:
    st.warning("No archived newsletters found.")
else:
    st.subheader("Past Issues")
    # Sort issues by creation date, assuming 'created_at' field exists and is newest first
    try:
        sorted_issues = sorted(archived_issues, key=lambda x: x.get('created_at'), reverse=True)
    except:
        sorted_issues = archived_issues # Fallback if sorting fails

    for issue in sorted_issues:
        # Use a more specific title for the expander
        expander_title = f"{issue.get('title', 'Untitled Issue')} (Archived on: {issue.get('created_at', 'N/A').split('T')[0] if issue.get('created_at') else 'N/A' })"
        with st.expander(expander_title):
            st.markdown(f"### {issue.get('title')}")
            
            # Fetch the full content for the issue
            full_issue_details = db_handler.fetch_full_newsletter_issue(issue['id'])
            
            if full_issue_details and full_issue_details.get('articles'):
                # Recreate the markdown content from the articles
                markdown_content = f"# {full_issue_details['title']}\n\n## 🎯 Top Stories\n\n"
                
                sorted_articles = sorted(full_issue_details['articles'], key=lambda x: x.get('display_order', 999))

                for article in sorted_articles:
                    summary = (article.get('summary') or '').strip()
                    title = (article.get('title') or 'No Title').replace('*', '')
                    url = article.get('url') or '#'
                    if summary.endswith('(more)'):
                        summary = summary[:-6].strip()
                    
                    markdown_content += f"🎯 {title}\n\n{summary} ([more]({url}))\n\n---\n\n"

                st.text_area(
                    label="Archived Content",
                    value=markdown_content,
                    height=400,
                    key=f"archive_preview_{issue['id']}",
                    disabled=True
                )
            else:
                st.error("Could not load the content for this issue.")
