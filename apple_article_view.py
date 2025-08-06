# Apple-Inspired Article Management Interface
# Following Apple Human Interface Guidelines for professional newsletter production

import streamlit as st
import requests
from typing import List, Dict, Any
import json

def render_apple_article_view(articles: List[Dict[str, Any]], api_url: str):
    """
    Apple-inspired article management interface with proper spacing, typography, and UX
    """
    # Clear Streamlit cache to ensure fresh rendering
    st.cache_data.clear()
    
    if not articles:
        st.info("📰 No articles found. Import some URLs to get started!")
        return
    
    # Apple-inspired CSS following HIG principles
    st.markdown("""
    <style>
    /* Apple Human Interface Guidelines - Professional Layout */
    
    /* Main container with proper spacing */
    .apple-container {
        background: #ffffff;
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border: 1px solid #e5e5e7;
    }
    
    /* Filter bar - Apple style */
    .apple-filter-bar {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px 20px;
        background: #f5f5f7;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #d2d2d7;
    }
    
    .apple-filter-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        background: #007aff;
        color: white;
        border-radius: 16px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .apple-filter-chip:hover {
        background: #0056cc;
        transform: translateY(-1px);
    }
    
    .apple-filter-chip .remove {
        margin-left: 4px;
        cursor: pointer;
        font-weight: bold;
    }
    
    /* Table header - Apple outline view style - WIDER LAYOUT */
    .apple-table-header {
        display: grid;
        grid-template-columns: 50px 60px 3fr 3fr 120px 120px;
        gap: 20px;
        padding: 16px 24px;
        background: #f5f5f7;
        border-radius: 8px;
        border: 1px solid #d2d2d7;
        font-weight: 600;
        font-size: 15px;
        color: #1d1d1f;
        margin-bottom: 8px;
    }
    
    .apple-table-header .sortable {
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 4px;
        transition: color 0.2s ease;
    }
    
    .apple-table-header .sortable:hover {
        color: #007aff;
    }
    
    /* Article row - 44pt minimum touch target - WIDER LAYOUT */
    .apple-article-row {
        display: grid;
        grid-template-columns: 50px 60px 3fr 3fr 120px 120px;
        gap: 20px;
        align-items: center;
        padding: 16px 24px;
        min-height: 52px;
        background: white;
        border: 1px solid #e5e5e7;
        border-radius: 8px;
        margin-bottom: 6px;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .apple-article-row:hover {
        background: #f5f5f7;
        border-color: #007aff;
        box-shadow: 0 2px 8px rgba(0,122,255,0.1);
        transform: translateY(-1px);
    }
    
    .apple-article-row.selected {
        background: #e3f2fd;
        border-color: #007aff;
        box-shadow: 0 0 0 2px rgba(0,122,255,0.2);
    }
    
    /* Typography - Apple system fonts - LARGER FOR WIDER LAYOUT */
    .apple-title {
        font-size: 17px;
        font-weight: 600;
        line-height: 1.4;
        color: #1d1d1f;
        margin: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .apple-summary {
        font-size: 15px;
        line-height: 1.4;
        color: #86868b;
        margin: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .apple-position {
        font-size: 16px;
        font-weight: 700;
        color: #007aff;
        text-align: center;
    }
    
    /* Status badges - Apple style */
    .apple-status {
        padding: 6px 12px;
        border-radius: 16px;
        font-size: 12px;
        font-weight: 600;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-pending { 
        background: #ff9f0a; 
        color: white; 
    }
    .status-summarized { 
        background: #007aff; 
        color: white; 
    }
    .status-accepted { 
        background: #34c759; 
        color: white; 
    }
    .status-archived { 
        background: #8e8e93; 
        color: white; 
    }
    .status-scraping_failed { 
        background: #ff3b30; 
        color: white; 
    }
    
    /* Action buttons - Apple style */
    .apple-action-btn {
        padding: 8px 16px;
        background: #007aff;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        min-height: 32px;
    }
    
    .apple-action-btn:hover {
        background: #0056cc;
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,122,255,0.3);
    }
    
    .apple-action-btn.secondary {
        background: #f5f5f7;
        color: #007aff;
        border: 1px solid #d2d2d7;
    }
    
    .apple-action-btn.secondary:hover {
        background: #e5e5e7;
        border-color: #007aff;
    }
    
    /* Bulk actions toolbar */
    .apple-bulk-toolbar {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 20px;
        background: linear-gradient(135deg, #007aff, #0056cc);
        color: white;
        border-radius: 12px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,122,255,0.3);
    }
    
    .apple-bulk-toolbar .count {
        font-weight: 600;
        margin-right: 8px;
    }
    
    /* Search and filter controls */
    .apple-search-bar {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
    }
    
    .apple-search-input {
        flex: 1;
        padding: 12px 16px;
        border: 1px solid #d2d2d7;
        border-radius: 8px;
        font-size: 16px;
        background: white;
        transition: border-color 0.2s ease;
    }
    
    .apple-search-input:focus {
        outline: none;
        border-color: #007aff;
        box-shadow: 0 0 0 3px rgba(0,122,255,0.1);
    }
    
    /* Sidebar layout */
    .apple-sidebar {
        background: #f5f5f7;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #d2d2d7;
    }
    
    .apple-sidebar h3 {
        font-size: 18px;
        font-weight: 600;
        color: #1d1d1f;
        margin: 0 0 16px 0;
    }
    
    .apple-filter-group {
        margin-bottom: 24px;
    }
    
    .apple-filter-group h4 {
        font-size: 14px;
        font-weight: 600;
        color: #1d1d1f;
        margin: 0 0 8px 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .apple-filter-option {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 6px;
        cursor: pointer;
        transition: background-color 0.2s ease;
        font-size: 14px;
        color: #1d1d1f;
    }
    
    .apple-filter-option:hover {
        background: white;
    }
    
    .apple-filter-option.active {
        background: #007aff;
        color: white;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .apple-article-row {
            grid-template-columns: 1fr;
            gap: 8px;
        }
        
        .apple-table-header {
            display: none;
        }
    }
    
    /* Animation for smooth interactions */
    .fade-in {
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state for selections and filters
    if 'selected_articles' not in st.session_state:
        st.session_state.selected_articles = set()
    if 'filter_status' not in st.session_state:
        st.session_state.filter_status = 'All'
    if 'filter_source' not in st.session_state:
        st.session_state.filter_source = 'All'
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ''
    
    # Full width content (sidebar is handled in main app)
    render_apple_main_content(articles, api_url)

# Sidebar function removed - handled by main app

def render_apple_main_content(articles: List[Dict[str, Any]], api_url: str):
    """Render the main content area with articles - SIMPLIFIED"""
    
    # Search bar
    search_query = st.text_input(
        "🔍 Search articles...",
        placeholder="Search by title, summary, or source...",
        key="search_input"
    )
    
    # Apply search filter
    filtered_articles = articles
    if search_query:
        filtered_articles = [
            article for article in articles
            if (search_query.lower() in article.get('title', '').lower() or
                search_query.lower() in article.get('summary', '').lower() or
                search_query.lower() in article.get('source', '').lower())
        ]
    
    # Bulk actions toolbar (if articles are selected)
    if st.session_state.selected_articles:
        render_bulk_actions_toolbar(api_url)
    
    # Articles count removed per user request
    
    # Table header
    render_table_header()
    
    # Article rows
    render_article_rows(filtered_articles, api_url)

# Filter functions removed - not needed for simplified view

def render_bulk_actions_toolbar(api_url: str):
    """Render bulk actions toolbar when articles are selected"""
    selected_count = len(st.session_state.selected_articles)
    
    st.markdown(f'''
    <div class="apple-bulk-toolbar">
        <span class="count">{selected_count} articles selected</span>
    </div>
    ''', unsafe_allow_html=True)
    
    # Bulk action buttons
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("✅ Accept All", key="bulk_accept"):
            bulk_update_status(list(st.session_state.selected_articles), "accepted", api_url)
    
    with col2:
        if st.button("📋 Mark Summarized", key="bulk_summarized"):
            bulk_update_status(list(st.session_state.selected_articles), "summarized", api_url)
    
    with col3:
        if st.button("🗃️ Archive All", key="bulk_archive"):
            bulk_update_status(list(st.session_state.selected_articles), "archived", api_url)
    
    with col4:
        if st.button("🔄 Re-summarize", key="bulk_resummarize"):
            bulk_resummarize(list(st.session_state.selected_articles), api_url)
    
    with col5:
        if st.button("❌ Clear Selection", key="clear_selection"):
            st.session_state.selected_articles = set()
            st.rerun()

def render_table_header():
    """Render the table header with sortable columns"""
    st.markdown('''
    <div class="apple-table-header">
        <div>☑️</div>
        <div class="sortable"># ↕️</div>
        <div class="sortable">Title ↕️</div>
        <div class="sortable">Summary ↕️</div>
        <div class="sortable">Status ↕️</div>
        <div>Actions</div>
    </div>
    ''', unsafe_allow_html=True)

def render_article_rows(articles: List[Dict[str, Any]], api_url: str):
    """Render individual article rows"""
    for i, article in enumerate(articles):
        article_id = article.get('id')
        is_selected = article_id in st.session_state.selected_articles
        
        # Create unique keys for this article
        checkbox_key = f"select_{article_id}_{i}"
        
        # Article row container
        row_class = "apple-article-row selected" if is_selected else "apple-article-row"
        
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([0.5, 0.6, 2, 2, 1.2, 1])
            
            with col1:
                # Selection checkbox
                if st.checkbox("", key=checkbox_key, value=is_selected):
                    st.session_state.selected_articles.add(article_id)
                else:
                    st.session_state.selected_articles.discard(article_id)
            
            with col2:
                # Position number
                st.markdown(f'<div class="apple-position">{article.get("position", i+1)}</div>', 
                           unsafe_allow_html=True)
            
            with col3:
                # Title (clickable for editing)
                title = article.get('title', 'Untitled')
                if len(title) > 50:
                    title = title[:47] + "..."
                st.markdown(f'<div class="apple-title">{title}</div>', unsafe_allow_html=True)
            
            with col4:
                # Summary preview
                summary = article.get('summary', 'No summary available')
                if len(summary) > 60:
                    summary = summary[:57] + "..."
                st.markdown(f'<div class="apple-summary">{summary}</div>', unsafe_allow_html=True)
            
            with col5:
                # Status badge
                status = article.get('status', 'pending')
                status_class = f"apple-status status-{status}"
                st.markdown(f'<div class="{status_class}">{status.title()}</div>', 
                           unsafe_allow_html=True)
            
            with col6:
                # Action button
                if st.button("⚙️ Edit", key=f"edit_{article_id}_{i}", 
                           help="Edit article details"):
                    # Set edit state in session
                    st.session_state[f"editing_{article_id}"] = True
                    st.rerun()
        
        # Show edit modal if this article is being edited
        if st.session_state.get(f"editing_{article_id}", False):
            render_article_edit_modal(article, api_url)

def render_article_edit_modal(article: Dict[str, Any], api_url: str):
    """Render compact, efficient article editing modal"""
    
    # Compact modal with minimal padding
    st.markdown("""
    <div style="
        background: white;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
        border: 1px solid #d2d2d7;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    ">
    """, unsafe_allow_html=True)
    
    # Compact header with close button
    col_header, col_close = st.columns([4, 1])
    with col_header:
        st.markdown(f"**✏️ Edit Article #{article.get('position', 'N/A')}**")
    with col_close:
        if st.button("❌", key=f"close_{article['id']}", help="Close edit modal"):
            # Clear the edit state
            if f"editing_{article['id']}" in st.session_state:
                del st.session_state[f"editing_{article['id']}"]
            st.rerun()
    
    # Compact form layout
    with st.form(f"edit_form_{article['id']}", clear_on_submit=False):
        
        # Title with URL detection for failed scraping
        current_title = article.get('title', '')
        is_url = current_title.startswith(('http://', 'https://'))
        
        if is_url:
            st.markdown("**⚠️ Failed Article (Click to Open):**")
            # Make URL clickable
            st.markdown(f"🔗 [**{current_title}**]({current_title})")
            st.info("📝 **Scraping failed.** Click the link above to open the article, then use 'Manual Content' to paste the text.")
            # Empty title field for user to enter actual title
            new_title = st.text_input(
                "Article Title", 
                placeholder="Enter the actual article title here...",
                label_visibility="collapsed",
                help="Replace with the real article headline"
            )
        else:
            st.markdown("**Title:**")
            new_title = st.text_input(
                "Title", 
                value=current_title,
                label_visibility="collapsed"
            )
        
        # Summary with scraping failure detection
        current_summary = article.get('summary', '')
        is_scraping_error = 'Scraping error' in current_summary or 'Failed to fetch' in current_summary
        
        if is_scraping_error:
            st.markdown("🤖 **AI Summary (Scraping Failed):**")
            st.error("❌ Scraping failed - Use 'Manual Content' button below to paste article text for AI summarization.")
        else:
            st.markdown("🤖 **AI Summary:**")
            
        new_summary = st.text_area(
            "Summary",
            value=current_summary if not is_scraping_error else "",
            label_visibility="collapsed",
            height=120,
            placeholder="AI-generated summary will appear here..." if is_scraping_error else "Edit the AI-generated summary..."
        )
        
        # Intelligent workflow actions based on article state
        current_status = article.get('status', 'pending')
        current_summary = article.get('summary', '').strip()
        
        st.markdown("**Actions:**")
        
        # Action button row - intelligent based on state
        col1, col2, col3, col4 = st.columns(4)
        
        # Initialize action variables
        re_summarize_clicked = False
        manual_content_clicked = False
        accepted_clicked = False
        archived_clicked = False
        
        with col1:
            # Re-summarize: Always available to try AI again
            re_summarize_clicked = st.form_submit_button(
                "🤖 Re-summarize",
                use_container_width=True,
                help="Have AI generate a new summary"
            )
        
        with col2:
            # Manual Content: For failed scraping or manual input
            manual_content_clicked = st.form_submit_button(
                "✍️ Manual Content", 
                use_container_width=True,
                help="Add content manually if scraping failed"
            )
        
        with col3:
            # Accept: Mark as ready for newsletter (only if has summary)
            if current_summary:
                accepted_clicked = st.form_submit_button(
                    "✅ Accept",
                    use_container_width=True,
                    type="primary" if current_status == 'accepted' else "secondary",
                    help="Accept for newsletter export"
                )
            else:
                st.form_submit_button(
                    "✅ Accept",
                    use_container_width=True,
                    disabled=True,
                    help="Need summary before accepting"
                )
        
        with col4:
            # Archive: Remove from workflow
            archived_clicked = st.form_submit_button(
                "🗑️ Archive",
                use_container_width=True,
                type="primary" if current_status == 'archived' else "secondary",
                help="Remove from newsletter workflow"
            )
        
        # Determine new status and actions
        new_status = current_status  # Default to current
        action_taken = None
        
        if re_summarize_clicked:
            action_taken = 'resummarize'
            new_status = 'pending'  # Will become 'summarized' after AI processing
        elif manual_content_clicked:
            action_taken = 'manual_content'
            # Keep current status, just show manual input
        elif accepted_clicked:
            new_status = 'accepted'
        elif archived_clicked:
            new_status = 'archived'
        
        # Save/Cancel buttons - separate from action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            pass  # Empty space
        with col2:
            # Only save if no special action was taken
            save_clicked = st.form_submit_button(
                "💾 Save Changes", 
                use_container_width=True,
                type="primary",
                help="Save title and summary edits"
            )
        with col3:
            cancel_clicked = st.form_submit_button(
                "❌ Cancel", 
                use_container_width=True,
                help="Close without saving"
            )

    
    # Handle form submissions - prioritize action buttons over save/cancel
    if action_taken == 'resummarize':
        # Trigger AI re-summarization
        try:
            response = requests.post(f"{api_url}/articles/{article['id']}/resummarize")
            if response.status_code == 200:
                st.success("🤖 AI is re-summarizing the article...")
                st.info("Refresh the page in a few moments to see the new summary.")
                # Clear edit state and close modal
                if f"editing_{article['id']}" in st.session_state:
                    del st.session_state[f"editing_{article['id']}"]
                st.rerun()
            else:
                st.error("❌ Failed to trigger re-summarization.")
        except Exception as e:
            st.error(f"❌ Re-summarization error: {str(e)}")
            
    elif action_taken == 'manual_content':
        # Show manual content input area
        st.session_state[f"manual_content_{article['id']}"] = True
        st.info("📝 Manual content mode activated. Add your content below.")
        
        # Manual content input
        st.markdown("**✍️ Manual Article Content:**")
        manual_content = st.text_area(
            "Manual Content",
            placeholder="Paste the full article content here for AI to summarize...",
            height=200,
            label_visibility="collapsed",
            help="Paste article content here if scraping failed"
        )
        
        if manual_content.strip():
            if st.button("🤖 Summarize Manual Content", type="primary"):
                try:
                    # Send manual content for summarization
                    response = requests.post(f"{api_url}/articles/{article['id']}/summarize-manual", 
                                           json={"content": manual_content.strip()})
                    if response.status_code == 200:
                        st.success("✅ Manual content submitted for AI summarization!")
                        st.info("Refresh the page to see the AI-generated summary.")
                        # Clear edit state and close modal
                        if f"editing_{article['id']}" in st.session_state:
                            del st.session_state[f"editing_{article['id']}"]
                        st.rerun()
                    else:
                        st.error("❌ Failed to process manual content.")
                except Exception as e:
                    st.error(f"❌ Manual content error: {str(e)}")
                    
    elif save_clicked and not action_taken:
        # Regular save - only if no action button was clicked
        if new_title.strip():  # Validate title is not empty
            # Prepare update data
            update_data = {
                'title': new_title.strip(), 
                'status': new_status
            }
            
            # Include summary if it was provided
            if new_summary.strip():
                update_data['summary'] = new_summary.strip()
            
            success = update_article(article['id'], update_data, api_url)
            if success:
                st.success("✅ Article updated successfully!")
                st.balloons()
                # Clear the edit state
                if f"editing_{article['id']}" in st.session_state:
                    del st.session_state[f"editing_{article['id']}"]
                st.rerun()
            else:
                st.error("❌ Failed to update article. Please try again.")
        else:
            st.error("❌ Title cannot be empty!")
    
    if cancel_clicked:
        # Clear the edit state
        if f"editing_{article['id']}" in st.session_state:
            del st.session_state[f"editing_{article['id']}"]
        st.rerun()
    
    # Close modal container
    st.markdown("</div>", unsafe_allow_html=True)

def bulk_update_status(article_ids: List[int], new_status: str, api_url: str):
    """Update status for multiple articles"""
    try:
        for article_id in article_ids:
            response = requests.patch(f"{api_url}/articles/{article_id}", 
                                    json={"status": new_status})
            if response.status_code != 200:
                st.error(f"Failed to update article {article_id}")
                return
        
        st.success(f"Updated {len(article_ids)} articles to {new_status}")
        st.session_state.selected_articles = set()
        st.rerun()
        
    except Exception as e:
        st.error(f"Error updating articles: {str(e)}")

def bulk_resummarize(article_ids: List[int], api_url: str):
    """Re-summarize multiple articles"""
    try:
        for article_id in article_ids:
            # Trigger re-summarization (implementation depends on your API)
            response = requests.post(f"{api_url}/articles/{article_id}/resummarize")
            if response.status_code != 200:
                st.error(f"Failed to re-summarize article {article_id}")
                return
        
        st.success(f"Re-summarizing {len(article_ids)} articles")
        st.session_state.selected_articles = set()
        st.rerun()
        
    except Exception as e:
        st.error(f"Error re-summarizing articles: {str(e)}")

def update_article(article_id: int, updates: Dict[str, Any], api_url: str):
    """Update a single article"""
    try:
        response = requests.patch(f"{api_url}/articles/{article_id}", json=updates)
        if response.status_code != 200:
            st.error("Failed to update article")
        
    except Exception as e:
        st.error(f"Error updating article: {str(e)}")
