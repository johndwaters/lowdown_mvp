# Enhanced Article View - Phase 2A
# Bulk selection, advanced filtering, and inline editing

import streamlit as st
import requests
from typing import List, Dict, Any

def render_enhanced_article_view(articles: List[Dict[str, Any]], api_url: str):
    """
    Phase 2A: Enhanced article view with bulk operations, filtering, and inline editing
    """
    if not articles:
        st.info("📰 No articles found. Import some URLs to get started!")
        return
    
    # Enhanced CSS for Phase 2A features
    st.markdown("""
    <style>
    /* Enhanced CSS for Phase 2A features - ULTRA COMPACT */
    .enhanced-article-row {
        display: flex;
        align-items: center;
        padding: 0.1rem 0.2rem;
        margin: 0.05rem 0;
        border: 1px solid #e0e0e0;
        border-radius: 2px;
        background: white;
        transition: all 0.2s ease;
        min-height: 20px;
        max-height: 20px;
    }
    .enhanced-article-row:hover {
        background: #f8f9fa;
        border-color: #4A5D23;
        box-shadow: 0 2px 4px rgba(74, 93, 35, 0.1);
    }
    .enhanced-article-row.selected {
        background: #e8f5e8;
        border-color: #4A5D23;
    }
    
    /* Compact elements */
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
        padding: 0.02rem 0.1rem;
        border-radius: 4px;
        font-size: 0.4rem;
        font-weight: 500;
        min-width: 40px;
        text-align: center;
        line-height: 0.9;
        height: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .status-pending { background: #FFB84D; color: white; }
    .status-summarized { background: #87CEEB; color: #333; }
    .status-accepted { background: #90EE90; color: #333; }
    .status-archived { background: #ccc; color: #666; }
    
    /* Bulk actions toolbar */
    .bulk-actions-toolbar {
        background: linear-gradient(135deg, #4A5D23, #3A4A1C);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        display: flex;
        align-items: center;
        gap: 1rem;
        font-size: 0.8rem;
    }
    
    /* Filter bar */
    .filter-bar {
        background: #f8f9fa;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        border: 1px solid #e0e0e0;
    }
    
    /* Ultra-compact buttons - FORCE OVERRIDE */
    .stButton > button, button[kind="secondary"], button[kind="primary"] {
        font-size: 0.5rem !important;
        padding: 0.02rem 0.1rem !important;
        height: 18px !important;
        min-height: 18px !important;
        line-height: 0.9 !important;
        border: none !important;
        background: transparent !important;
        color: #333 !important;
        text-align: left !important;
        font-weight: 400 !important;
        max-height: 18px !important;
    }
    .stButton > button:hover, button[kind="secondary"]:hover, button[kind="primary"]:hover {
        background: #f0f0f0 !important;
        color: #4A5D23 !important;
    }
    
    /* Force all text elements to be tiny */
    div[data-testid="column"] button {
        font-size: 0.5rem !important;
        height: 18px !important;
        padding: 0.02rem 0.1rem !important;
    }
    
    /* Compact checkboxes */
    .stCheckbox {
        margin: 0 !important;
        padding: 0 !important;
    }
    .stCheckbox > label {
        font-size: 0.7rem !important;
        margin: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state for bulk selection
    if 'selected_articles' not in st.session_state:
        st.session_state.selected_articles = set()
    if 'filter_status' not in st.session_state:
        st.session_state.filter_status = 'All'
    if 'filter_source' not in st.session_state:
        st.session_state.filter_source = 'All'
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ''
    
    # Sort articles by position
    sorted_articles = sorted(articles, key=lambda x: x.get('position', 999))
    
    # Advanced Filtering Section
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 1, 1, 1])
    
    with filter_col1:
        search_query = st.text_input(
            "🔍 Search articles", 
            value=st.session_state.search_query,
            placeholder="Search titles and summaries...",
            key="search_input"
        )
        st.session_state.search_query = search_query
    
    with filter_col2:
        status_options = ['All', 'pending', 'summarized', 'accepted', 'archived']
        filter_status = st.selectbox(
            "Status Filter",
            status_options,
            index=status_options.index(st.session_state.filter_status),
            key="status_filter"
        )
        st.session_state.filter_status = filter_status
    
    with filter_col3:
        source_options = ['All'] + list(set([a.get('source', 'manual_add') for a in sorted_articles]))
        filter_source = st.selectbox(
            "Source Filter",
            source_options,
            index=source_options.index(st.session_state.filter_source) if st.session_state.filter_source in source_options else 0,
            key="source_filter"
        )
        st.session_state.filter_source = filter_source
    
    with filter_col4:
        if st.button("🔄 Clear Filters", key="clear_filters"):
            st.session_state.filter_status = 'All'
            st.session_state.filter_source = 'All'
            st.session_state.search_query = ''
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters
    filtered_articles = sorted_articles
    
    # Filter by status
    if filter_status != 'All':
        filtered_articles = [a for a in filtered_articles if a.get('status') == filter_status]
    
    # Filter by source
    if filter_source != 'All':
        filtered_articles = [a for a in filtered_articles if a.get('source') == filter_source]
    
    # Filter by search query
    if search_query:
        search_lower = search_query.lower()
        filtered_articles = [
            a for a in filtered_articles 
            if search_lower in a.get('title', '').lower() or 
               search_lower in a.get('summary', '').lower()
        ]
    
    # Bulk Actions Toolbar (only show if articles are selected)
    selected_count = len(st.session_state.selected_articles)
    if selected_count > 0:
        st.markdown(f"""
        <div class="bulk-actions-toolbar">
            <span><strong>{selected_count}</strong> article(s) selected</span>
        </div>
        """, unsafe_allow_html=True)
        
        bulk_col1, bulk_col2, bulk_col3, bulk_col4, bulk_col5 = st.columns(5)
        
        with bulk_col1:
            if st.button("✅ Accept Selected", key="bulk_accept"):
                for article_id in st.session_state.selected_articles:
                    try:
                        requests.patch(f"{api_url}/articles/{article_id}", json={"status": "accepted"})
                    except Exception as e:
                        st.error(f"Failed to accept article {article_id}: {e}")
                st.session_state.selected_articles.clear()
                st.rerun()
        
        with bulk_col2:
            if st.button("📦 Archive Selected", key="bulk_archive"):
                for article_id in st.session_state.selected_articles:
                    try:
                        requests.patch(f"{api_url}/articles/{article_id}", json={"status": "archived"})
                    except Exception as e:
                        st.error(f"Failed to archive article {article_id}: {e}")
                st.session_state.selected_articles.clear()
                st.rerun()
        
        with bulk_col3:
            if st.button("🔄 Re-summarize Selected", key="bulk_summarize"):
                for article_id in st.session_state.selected_articles:
                    try:
                        requests.post(f"{api_url}/summarize", json={"article_id": article_id})
                    except Exception as e:
                        st.error(f"Failed to summarize article {article_id}: {e}")
                st.session_state.selected_articles.clear()
                st.rerun()
        
        with bulk_col4:
            if st.button("📝 Mark as Summarized", key="bulk_summarized"):
                for article_id in st.session_state.selected_articles:
                    try:
                        requests.patch(f"{api_url}/articles/{article_id}", json={"status": "summarized"})
                    except Exception as e:
                        st.error(f"Failed to update article {article_id}: {e}")
                st.session_state.selected_articles.clear()
                st.rerun()
        
        with bulk_col5:
            if st.button("❌ Clear Selection", key="clear_selection"):
                st.session_state.selected_articles.clear()
                st.rerun()
    
    # Header row with select all checkbox
    header_col1, header_col2, header_col3, header_col4, header_col5, header_col6 = st.columns([0.3, 0.3, 2, 3, 1, 1.5])
    
    with header_col1:
        select_all = st.checkbox("", key="select_all", help="Select All")
        if select_all:
            st.session_state.selected_articles = set([a['id'] for a in filtered_articles])
        elif not select_all and len(st.session_state.selected_articles) == len(filtered_articles):
            st.session_state.selected_articles.clear()
    
    # Header labels
    st.markdown(f"""
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
        <div style="min-width: 50px;">Select</div>
        <div style="min-width: 25px;">#</div>
        <div style="flex: 2; margin: 0 0.3rem;">Title</div>
        <div style="flex: 3; margin: 0 0.3rem;">Summary Preview</div>
        <div style="min-width: 65px; text-align: center;">Status</div>
        <div style="min-width: 80px; margin-left: 0.3rem;">Actions</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render filtered articles
    for index, article in enumerate(filtered_articles):
        article_id = article['id']
        position = article.get('position', index + 1)
        title = article.get('title', 'Untitled')
        status = article.get('status', 'pending')
        
        # Get summary preview (first 80 chars)
        summary = article.get('summary', '')
        if summary:
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
        
        # Create the enhanced row
        row_class = "enhanced-article-row selected" if article_id in st.session_state.selected_articles else "enhanced-article-row"
        
        col1, col2, col3, col4, col5, col6 = st.columns([0.3, 0.3, 2, 3, 1, 1.5])
        
        with col1:
            # Selection checkbox
            is_selected = st.checkbox(
                "", 
                value=article_id in st.session_state.selected_articles,
                key=f"select_{article_id}",
                help=f"Select article #{position}"
            )
            if is_selected:
                st.session_state.selected_articles.add(article_id)
            else:
                st.session_state.selected_articles.discard(article_id)
        
        with col2:
            st.markdown(f'<div class="article-position">#{position}</div>', unsafe_allow_html=True)
        
        with col3:
            # Inline editable title
            if st.session_state.get(f"edit_title_{article_id}", False):
                new_title = st.text_input(
                    "Edit title",
                    value=title,
                    key=f"title_input_{article_id}",
                    label_visibility="collapsed"
                )
                save_col, cancel_col = st.columns(2)
                with save_col:
                    if st.button("💾", key=f"save_title_{article_id}", help="Save"):
                        try:
                            response = requests.patch(f"{api_url}/articles/{article_id}", 
                                                    json={"title": new_title})
                            if response.status_code == 200:
                                st.session_state[f"edit_title_{article_id}"] = False
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                with cancel_col:
                    if st.button("❌", key=f"cancel_title_{article_id}", help="Cancel"):
                        st.session_state[f"edit_title_{article_id}"] = False
                        st.rerun()
            else:
                if st.button(f"{title_display}", key=f"title_{article_id}", help=f"Double-click to edit: {title}"):
                    st.session_state[f"edit_title_{article_id}"] = True
                    st.rerun()
        
        with col4:
            st.markdown(f'<div class="article-summary-preview">{summary_preview}</div>', unsafe_allow_html=True)
        
        with col5:
            # Inline status editor
            if st.session_state.get(f"edit_status_{article_id}", False):
                new_status = st.selectbox(
                    "Status",
                    ['pending', 'summarized', 'accepted', 'archived'],
                    index=['pending', 'summarized', 'accepted', 'archived'].index(status),
                    key=f"status_select_{article_id}",
                    label_visibility="collapsed"
                )
                if new_status != status:
                    try:
                        response = requests.patch(f"{api_url}/articles/{article_id}", 
                                                json={"status": new_status})
                        if response.status_code == 200:
                            st.session_state[f"edit_status_{article_id}"] = False
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                if st.button(f"{status_emoji} {status.upper()}", key=f"status_{article_id}", help="Click to edit status"):
                    st.session_state[f"edit_status_{article_id}"] = True
                    st.rerun()
        
        with col6:
            # Compact action buttons
            action_col1, action_col2, action_col3 = st.columns(3)
            
            with action_col1:
                if st.button("↑", key=f"up_enhanced_{article_id}", help="Move Up"):
                    if position > 1:
                        try:
                            response = requests.patch(f"{api_url}/articles/{article_id}/position", 
                                                    json={"item_id": article_id, "new_position": position - 1})
                            if response.status_code == 200:
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            with action_col2:
                if st.button("↓", key=f"down_enhanced_{article_id}", help="Move Down"):
                    try:
                        response = requests.patch(f"{api_url}/articles/{article_id}/position", 
                                                json={"item_id": article_id, "new_position": position + 1})
                        if response.status_code == 200:
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            with action_col3:
                if st.button("📋", key=f"details_enhanced_{article_id}", help="View Details"):
                    st.session_state[f"expand_{article_id}"] = not st.session_state.get(f"expand_{article_id}", False)
        
        # Expandable details section (only if clicked)
        if st.session_state.get(f"expand_{article_id}", False):
            with st.expander("📋 Article Details", expanded=True):
                st.markdown(f"**URL:** {article.get('url', 'N/A')}")
                st.markdown(f"**Source:** {article.get('source', 'manual_add')}")
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
                        key=f"manual_enhanced_{article_id}",
                        help="Paste the article content here"
                    )
                    
                    if st.button("📝 Process Manual Content", key=f"process_manual_enhanced_{article_id}"):
                        if manual_content.strip():
                            try:
                                response = requests.post(f"{api_url}/summarize-manual", 
                                                       json={"content": manual_content.strip()})
                                if response.status_code == 200:
                                    summary_data = response.json()
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
    
    # Show filtered results summary
    if len(filtered_articles) != len(sorted_articles):
        st.markdown(f"""
        <div style="
            padding: 0.5rem;
            background: #e8f4f8;
            border-radius: 4px;
            margin-top: 0.5rem;
            font-size: 0.8rem;
            color: #2c5282;
        ">
            📊 Showing {len(filtered_articles)} of {len(sorted_articles)} articles
        </div>
        """, unsafe_allow_html=True)
