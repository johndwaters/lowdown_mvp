# Compact Article View Component for The Lowdown
# High-density, information-rich article display

import streamlit as st
import requests
from typing import List, Dict, Any

def render_compact_article_list(articles: List[Dict[str, Any]], api_url: str):
    """
    Render articles in a compact, table-like view with maximum information density
    """
    if not articles:
        st.info("📰 No articles found. Import some URLs to get started!")
        return
    
    # Sort articles by position
    sorted_articles = sorted(articles, key=lambda x: x.get('position', 999))
    
    # Compact CSS for dense layout
    st.markdown("""
    <style>
    .compact-article-row {
        display: flex;
        align-items: center;
        padding: 0.2rem 0.4rem;
        margin: 0.1rem 0;
        border: 1px solid #e0e0e0;
        border-radius: 3px;
        background: white;
        transition: all 0.2s ease;
        min-height: 35px;
    }
    .compact-article-row:hover {
        background: #f8f9fa;
        border-color: #4A5D23;
        box-shadow: 0 2px 4px rgba(74, 93, 35, 0.1);
    }
    .article-position {
        font-weight: bold;
        color: #4A5D23;
        min-width: 25px;
        font-size: 0.75rem;
    }
    .article-title {
        flex: 1;
        font-weight: 500;
        font-size: 0.7rem;
        line-height: 1.1;
        margin: 0 0.3rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .article-summary-preview {
        flex: 1.5;
        font-size: 0.7rem;
        color: #666;
        line-height: 1.1;
        margin: 0 0.3rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .status-badge {
        padding: 0.1rem 0.3rem;
        border-radius: 8px;
        font-size: 0.65rem;
        font-weight: 500;
        min-width: 65px;
        text-align: center;
    }
    .status-pending { background: #FFB84D; color: white; }
    .status-summarized { background: #87CEEB; color: #333; }
    .status-accepted { background: #90EE90; color: #333; }
    .status-archived { background: #ccc; color: #666; }
    .compact-actions {
        display: flex;
        gap: 0.2rem;
        margin-left: 0.5rem;
    }
    .compact-btn {
        padding: 0.2rem 0.4rem;
        font-size: 0.7rem;
        border: none;
        border-radius: 3px;
        cursor: pointer;
        background: #4A5D23;
        color: white;
        transition: all 0.2s ease;
    }
    .compact-btn:hover {
        background: #3A4A1C;
        transform: translateY(-1px);
    }
    .source-tag {
        font-size: 0.7rem;
        color: #888;
        margin-left: 0.5rem;
        min-width: 60px;
    }
    /* Ultra-compact title buttons */
    .stButton > button {
        font-size: 0.7rem !important;
        padding: 0.1rem 0.3rem !important;
        height: 25px !important;
        min-height: 25px !important;
        line-height: 1.1 !important;
        border: none !important;
        background: transparent !important;
        color: #333 !important;
        text-align: left !important;
        font-weight: 400 !important;
    }
    .stButton > button:hover {
        background: #f0f0f0 !important;
        color: #4A5D23 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header row - ultra-compact
    st.markdown("""
    <div style="
        display: flex;
        align-items: center;
        padding: 0.3rem 0.4rem;
        background: linear-gradient(135deg, #4A5D23, #3A4A1C);
        color: white;
        border-radius: 3px;
        margin-bottom: 0.3rem;
        font-weight: 500;
        font-size: 0.7rem;
    ">
        <div style="min-width: 25px;">#</div>
        <div style="flex: 1; margin: 0 0.3rem;">Title</div>
        <div style="flex: 1.5; margin: 0 0.3rem;">Summary Preview</div>
        <div style="min-width: 65px; text-align: center;">Status</div>
        <div style="min-width: 50px; margin-left: 0.3rem;">Source</div>
        <div style="min-width: 80px; margin-left: 0.3rem;">Actions</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render each article in compact format
    for index, article in enumerate(sorted_articles):
        article_id = article['id']
        position = article.get('position', index + 1)
        title = article.get('title', 'Untitled')
        status = article.get('status', 'pending')
        source = article.get('source', 'manual')
        
        # Get summary preview (first 80 chars)
        summary = article.get('summary', '')
        if summary:
            # Clean up summary for preview
            summary_clean = summary.replace('🎯', '').replace('**', '').strip()
            summary_preview = summary_clean[:80] + "..." if len(summary_clean) > 80 else summary_clean
        else:
            summary_preview = "No summary available"
        
        # Truncate title if too long
        title_display = title[:50] + "..." if len(title) > 50 else title
        
        # Status styling
        status_class = f"status-{status}"
        status_emoji = {
            'pending': '⏳',
            'summarized': '📝',
            'accepted': '✅',
            'archived': '📦'
        }.get(status, '❓')
        
        # Create the compact row
        col1, col2, col3, col4, col5 = st.columns([0.3, 2, 3, 1, 1.5])
        
        with col1:
            st.markdown(f'<div class="article-position">#{position}</div>', unsafe_allow_html=True)
        
        with col2:
            # Title as compact clickable text
            if st.button(f"{title_display}", key=f"title_{article_id}", help=f"Full title: {title}"):
                st.session_state[f"expand_{article_id}"] = not st.session_state.get(f"expand_{article_id}", False)
        
        with col3:
            st.markdown(f'<div class="article-summary-preview">{summary_preview}</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown(f'<div class="status-badge {status_class}">{status_emoji} {status.upper()}</div>', unsafe_allow_html=True)
        
        with col5:
            # Compact action buttons
            action_col1, action_col2, action_col3, action_col4 = st.columns(4)
            
            with action_col1:
                if st.button("↑", key=f"up_compact_{article_id}", help="Move Up"):
                    if position > 1:
                        try:
                            response = requests.patch(f"{api_url}/articles/{article_id}/position", 
                                                    json={"item_id": article_id, "new_position": position - 1})
                            if response.status_code == 200:
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            with action_col2:
                if st.button("↓", key=f"down_compact_{article_id}", help="Move Down"):
                    try:
                        response = requests.patch(f"{api_url}/articles/{article_id}/position", 
                                                json={"item_id": article_id, "new_position": position + 1})
                        if response.status_code == 200:
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            with action_col3:
                if status == 'summarized':
                    if st.button("✅", key=f"accept_compact_{article_id}", help="Accept"):
                        try:
                            response = requests.patch(f"{api_url}/articles/{article_id}", 
                                                    json={"status": "accepted"})
                            if response.status_code == 200:
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                elif status == 'accepted':
                    if st.button("📝", key=f"unaccept_compact_{article_id}", help="Un-accept"):
                        try:
                            response = requests.patch(f"{api_url}/articles/{article_id}", 
                                                    json={"status": "summarized"})
                            if response.status_code == 200:
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            with action_col4:
                if st.button("🗑️", key=f"archive_compact_{article_id}", help="Archive"):
                    try:
                        response = requests.patch(f"{api_url}/articles/{article_id}", 
                                                json={"status": "archived"})
                        if response.status_code == 200:
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        # Expandable details section (only if clicked)
        if st.session_state.get(f"expand_{article_id}", False):
            with st.expander("📋 Article Details", expanded=True):
                st.markdown(f"**URL:** {article.get('url', 'N/A')}")
                st.markdown(f"**Source:** {source}")
                st.markdown(f"**Status:** {status}")
                
                if summary:
                    st.markdown("**Full Summary:**")
                    st.markdown(summary)
                
                # Manual content editing for failed scraping
                if status == 'scraping_failed':
                    st.warning("⚠️ Scraping failed for this article.")
                    failed_url = article.get('url', '')
                    if failed_url:
                        st.markdown(f"🔗 [Open failed article: {failed_url}]({failed_url})")
                    
                    manual_content = st.text_area(
                        "Manual Content",
                        value=failed_url,
                        height=100,
                        key=f"manual_{article_id}",
                        help="Paste the article content here"
                    )
                    
                    if st.button("📝 Process Manual Content", key=f"process_manual_{article_id}"):
                        if manual_content.strip():
                            try:
                                response = requests.post(f"{api_url}/summarize-manual", 
                                                       json={"content": manual_content.strip()})
                                if response.status_code == 200:
                                    summary_data = response.json()
                                    # Update article with new summary
                                    update_response = requests.patch(f"{api_url}/articles/{article_id}", 
                                                                   json={
                                                                       "summary": summary_data["summary"],
                                                                       "status": "summarized"
                                                                   })
                                    if update_response.status_code == 200:
                                        st.success("✅ Article summarized successfully!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to update article")
                                else:
                                    st.error("Failed to summarize content")
                            except Exception as e:
                                st.error(f"Error: {e}")
                        else:
                            st.warning("Please enter some content to summarize")

def render_compact_metrics_bar(articles: List[Dict[str, Any]]):
    """Render a compact horizontal metrics bar"""
    total_articles = len(articles)
    pending_count = len([a for a in articles if a['status'] == 'pending'])
    summarized_count = len([a for a in articles if a['status'] == 'summarized'])
    accepted_count = len([a for a in articles if a['status'] == 'accepted'])
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #4A5D23, #3A4A1C);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: 500;
    ">
        <span>📊 <strong>Pipeline:</strong></span>
        <span>{total_articles} Total</span>
        <span style="color: #FFB84D;">{pending_count} Pending</span>
        <span style="color: #87CEEB;">{summarized_count} Summarized</span>
        <span style="color: #90EE90;">{accepted_count} Accepted</span>
    </div>
    """, unsafe_allow_html=True)
