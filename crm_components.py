# CRM-Style UI Components for The Lowdown
# Modern, intuitive interface inspired by CRM best practices

import streamlit as st
import requests
from typing import List, Dict, Any

def render_crm_article_list(articles: List[Dict[str, Any]], api_url: str):
    """
    Render articles in a modern CRM-style list interface with drag-and-drop functionality
    """
    if not articles:
        st.info("📰 No articles found. Import some URLs to get started!")
        return
    
    # Add drag-and-drop CSS and JavaScript
    st.markdown("""
    <style>
    .sortable-list {
        list-style: none;
        padding: 0;
    }
    .sortable-item {
        cursor: move;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    .sortable-item:hover {
        transform: translateY(-2px);
    }
    .sortable-item.dragging {
        opacity: 0.5;
        transform: rotate(2deg);
    }
    .drag-handle {
        cursor: grab;
        user-select: none;
    }
    .drag-handle:active {
        cursor: grabbing;
    }
    </style>
    
    <script>
    function enableDragAndDrop() {
        const sortableList = document.querySelector('.sortable-list');
        if (!sortableList) return;
        
        let draggedElement = null;
        
        // Add drag event listeners to all drag handles
        document.querySelectorAll('.drag-handle').forEach(handle => {
            handle.addEventListener('dragstart', function(e) {
                draggedElement = this.closest('.sortable-item');
                draggedElement.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/html', draggedElement.outerHTML);
            });
            
            handle.addEventListener('dragend', function(e) {
                if (draggedElement) {
                    draggedElement.classList.remove('dragging');
                    draggedElement = null;
                }
            });
        });
        
        // Add drop zone event listeners
        document.querySelectorAll('.sortable-item').forEach(item => {
            item.addEventListener('dragover', function(e) {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
            });
            
            item.addEventListener('drop', function(e) {
                e.preventDefault();
                if (draggedElement && draggedElement !== this) {
                    // Get the positions
                    const draggedId = draggedElement.dataset.itemId;
                    const targetId = this.dataset.itemId;
                    
                    // Call the reorder function
                    reorderItems(draggedId, targetId, 'articles');
                }
            });
        });
    }
    
    function reorderItems(draggedId, targetId, itemType) {
        // Calculate new position based on target position
        const draggedElement = document.querySelector(`[data-item-id="${draggedId}"]`);
        const targetElement = document.querySelector(`[data-item-id="${targetId}"]`);
        
        if (!draggedElement || !targetElement) {
            console.error('Could not find dragged or target elements');
            return;
        }
        
        // Get all items in the list to calculate positions
        const allItems = Array.from(document.querySelectorAll('.sortable-item, .snapshot-sortable-item'));
        const targetIndex = allItems.indexOf(targetElement);
        const newPosition = targetIndex + 1; // 1-based positioning
        
        console.log(`Moving item ${draggedId} to position ${newPosition}`);
        
        // Use the correct API endpoint (no /api prefix)
        const apiUrl = window.location.hostname === 'localhost' ? 
            'http://localhost:8003' : 
            'https://lowdownmvp-production.up.railway.app';
        
        fetch(`${apiUrl}/${itemType}/${draggedId}/position`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                item_id: parseInt(draggedId),
                new_position: newPosition
            })
        })
        .then(response => {
            console.log('API Response:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('API Data:', data);
            if (data.success) {
                // Refresh the page to show new order
                setTimeout(() => window.location.reload(), 500);
            } else {
                console.error('API returned error:', data);
            }
        })
        .catch(error => {
            console.error('Error reordering items:', error);
        });
    }
    
    // Initialize drag and drop when the page loads
    document.addEventListener('DOMContentLoaded', enableDragAndDrop);
    setTimeout(enableDragAndDrop, 1000); // Also try after a delay for dynamic content
    </script>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📰 Article Pipeline")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    pending_count = len([a for a in articles if a.get('status') == 'pending'])
    summarized_count = len([a for a in articles if a.get('status') == 'summarized'])
    accepted_count = len([a for a in articles if a.get('status') == 'accepted'])
    total_count = len(articles)
    
    with col1:
        st.metric("Total Articles", total_count)
    with col2:
        st.metric("Pending", pending_count, delta=f"{pending_count}/{total_count}")
    with col3:
        st.metric("Summarized", summarized_count, delta=f"{summarized_count}/{total_count}")
    with col4:
        st.metric("Accepted", accepted_count, delta=f"{accepted_count}/{total_count}")
    
    st.markdown("---")
    
    # Article list with CRM-style cards (sortable)
    st.markdown('<div class="sortable-list">', unsafe_allow_html=True)
    for i, article in enumerate(articles):
        render_article_card(article, i, api_url)
    st.markdown('</div>', unsafe_allow_html=True)

def render_article_card(article: Dict[str, Any], index: int, api_url: str):
    """
    Render individual article card in CRM style with drag-and-drop functionality
    """
    # Status styling
    status = article.get('status', 'unknown')
    status_colors = {
        'pending': '🟡',
        'summarized': '🔵', 
        'accepted': '🟢',
        'archived': '⚫',
        'scraping_failed': '🔴'
    }
    
    status_emoji = status_colors.get(status, '❓')
    
    # Create expandable card with draggable attributes
    article_id = article.get('id')
    st.markdown(f'<div class="sortable-item" data-item-id="{article_id}" draggable="true">', unsafe_allow_html=True)
    
    with st.container():
        # Header row with key info
        col1, col2, col3, col4, col5 = st.columns([0.5, 3, 1.5, 1, 1])
        
        with col1:
            # Drag handle (now functional)
            st.markdown('<div class="drag-handle" draggable="true">⋮⋮</div>', unsafe_allow_html=True)
        
        with col2:
            # Title and URL preview
            title = article.get('title', 'Untitled')
            url = article.get('url', '')
            url_preview = url.split('/')[-1][:30] + "..." if len(url.split('/')[-1]) > 30 else url.split('/')[-1]
            
            st.markdown(f"**#{article.get('position', index+1)} {title}**")
            st.caption(f"🔗 {url_preview}")
        
        with col3:
            # Status badge
            st.markdown(f"{status_emoji} **{status.upper()}**")
        
        with col4:
            # Source
            source = article.get('source', 'manual_add')
            st.caption(f"📥 {source}")
        
        with col5:
            # Position controls (simplified approach)
            subcol1, subcol2 = st.columns(2)
            with subcol1:
                if st.button("⬆️", key=f"up_{article['id']}", help="Move Up"):
                    # Simple position update via API
                    current_pos = article.get('position', index + 1)
                    if current_pos > 1:
                        try:
                            response = requests.patch(f"{api_url}/articles/{article['id']}/position", 
                                                    json={"item_id": article['id'], "new_position": current_pos - 1})
                            if response.status_code == 200:
                                st.success("Moved up!")
                                st.rerun()
                            else:
                                st.error("Failed to move up")
                        except Exception as e:
                            st.error(f"Error: {e}")
            with subcol2:
                if st.button("⬇️", key=f"down_{article['id']}", help="Move Down"):
                    # Simple position update via API
                    current_pos = article.get('position', index + 1)
                    try:
                        response = requests.patch(f"{api_url}/articles/{article['id']}/position", 
                                                json={"item_id": article['id'], "new_position": current_pos + 1})
                        if response.status_code == 200:
                            st.success("Moved down!")
                            st.rerun()
                        else:
                            st.error("Failed to move down")
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            # Expand details button
            if st.button("⚙️", key=f"expand_{article['id']}", help="Expand details"):
                st.session_state[f"expanded_{article['id']}"] = not st.session_state.get(f"expanded_{article['id']}", False)
        
        # Expanded details
        if st.session_state.get(f"expanded_{article['id']}", False):
            with st.expander("Article Details", expanded=True):
                render_article_details(article, api_url)
        
        st.markdown("---")
    
    # Close the draggable container
    st.markdown('</div>', unsafe_allow_html=True)

def render_article_details(article: Dict[str, Any], api_url: str):
    """
    Render detailed article view with inline editing
    """
    # Summary section
    st.markdown("**📝 Summary**")
    summary = article.get('summary', '')
    if summary:
        # Editable summary
        new_summary = st.text_area(
            "Edit Summary",
            value=summary,
            height=100,
            key=f"summary_edit_{article['id']}"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 Save", key=f"save_summary_{article['id']}"):
                try:
                    response = requests.patch(f"{api_url}/articles/{article['id']}", 
                                            json={"summary": new_summary})
                    if response.status_code == 200:
                        st.success("Summary saved!")
                        st.rerun()
                    else:
                        st.error("Failed to save summary")
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.info("No summary available. Click 'Re-summarize' to generate one.")
    
    # Manual content section (if needed)
    article_status = article.get('status', '')
    if 'failed' in article_status.lower() or 'scraping_failed' in article_status.lower():
        st.markdown("**⚠️ Manual Content Required**")
        article_url = article.get('url', '')
        st.warning("Scraping failed for this article. Click the link below to open it:")
        st.markdown(f"🔗 **[{article_url}]({article_url})**", unsafe_allow_html=True)
        
        manual_content = st.text_area(
            "Paste article content here:",
            value=f"Failed to scrape: {article_url}\n\nPaste the article content here...",
            height=150,
            key=f"manual_content_detail_{article['id']}"
        )
        
        if st.button("🤖 Summarize Manual Content", key=f"manual_sum_detail_{article['id']}"):
            if manual_content.strip() and not manual_content.startswith("Failed to scrape:"):
                try:
                    response = requests.post(f"{api_url}/summarize-manual", json={
                        "article_id": article['id'],
                        "manual_content": manual_content
                    })
                    if response.status_code == 200:
                        st.success("Manual summarization completed!")
                        st.rerun()
                    else:
                        st.error("Failed to summarize manual content")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Action buttons
    st.markdown("**🎯 Actions**")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("🔄 Re-summarize", key=f"resum_detail_{article['id']}"):
            try:
                requests.post(f"{api_url}/summarize", json={"article_id": article['id']})
                st.success("Re-summarization started!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        current_status = article.get('status')
        if current_status != 'accepted':
            if st.button("✅ Accept", key=f"accept_detail_{article['id']}"):
                try:
                    response = requests.patch(f"{api_url}/articles/{article['id']}", 
                                            json={"status": "accepted"})
                    if response.status_code == 200:
                        st.success("Article accepted!")
                        st.rerun()
                    else:
                        st.error("Failed to accept article")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            if st.button("↩️ Un-accept", key=f"unaccept_detail_{article['id']}"):
                try:
                    response = requests.patch(f"{api_url}/articles/{article['id']}", 
                                            json={"status": "summarized"})
                    if response.status_code == 200:
                        st.success("Article un-accepted!")
                        st.rerun()
                    else:
                        st.error("Failed to un-accept article")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col3:
        if st.button("📦 Archive", key=f"archive_detail_{article['id']}"):
            try:
                response = requests.patch(f"{api_url}/articles/{article['id']}", 
                                        json={"status": "archived"})
                if response.status_code == 200:
                    st.success("Article archived!")
                    st.rerun()
                else:
                    st.error("Failed to archive article")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col4:
        if st.button("🗑️ Delete", key=f"delete_detail_{article['id']}"):
            try:
                response = requests.delete(f"{api_url}/articles/{article['id']}")
                if response.status_code == 200:
                    st.success("Article deleted!")
                    st.rerun()
                else:
                    st.error("Failed to delete article")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col5:
        # Position controls
        st.markdown("**Position**")
        subcol1, subcol2 = st.columns(2)
        with subcol1:
            if st.button("⬆️", key=f"up_detail_{article['id']}", help="Move Up"):
                # Move up logic would go here
                pass
        with subcol2:
            if st.button("⬇️", key=f"down_detail_{article['id']}", help="Move Down"):
                # Move down logic would go here
                pass

def render_crm_snapshot_list(snapshots: List[Dict[str, Any]], api_url: str):
    """
    Render snapshots in a modern CRM-style list interface with drag-and-drop functionality
    """
    if not snapshots:
        st.info("📸 No snapshots found. Import some URLs to get started!")
        return
    
    # Add drag-and-drop JavaScript for snapshots (reuse the same script but for snapshots)
    st.markdown("""
    <script>
    function enableSnapshotDragAndDrop() {
        const sortableList = document.querySelector('.snapshot-sortable-list');
        if (!sortableList) return;
        
        let draggedElement = null;
        
        // Add drag event listeners to all snapshot drag handles
        document.querySelectorAll('.snapshot-drag-handle').forEach(handle => {
            handle.addEventListener('dragstart', function(e) {
                draggedElement = this.closest('.snapshot-sortable-item');
                draggedElement.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/html', draggedElement.outerHTML);
            });
            
            handle.addEventListener('dragend', function(e) {
                if (draggedElement) {
                    draggedElement.classList.remove('dragging');
                    draggedElement = null;
                }
            });
        });
        
        // Add drop zone event listeners for snapshots
        document.querySelectorAll('.snapshot-sortable-item').forEach(item => {
            item.addEventListener('dragover', function(e) {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
            });
            
            item.addEventListener('drop', function(e) {
                e.preventDefault();
                if (draggedElement && draggedElement !== this) {
                    // Get the positions
                    const draggedId = draggedElement.dataset.itemId;
                    const targetId = this.dataset.itemId;
                    
                    // Call the reorder function for snapshots
                    reorderItems(draggedId, targetId, 'snapshots');
                }
            });
        });
    }
    
    // Initialize snapshot drag and drop
    document.addEventListener('DOMContentLoaded', enableSnapshotDragAndDrop);
    setTimeout(enableSnapshotDragAndDrop, 1000);
    
    // Also initialize the shared reorderItems function for snapshots
    window.reorderItems = window.reorderItems || reorderItems;
    </script>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📸 Snapshot Pipeline")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    pending_count = len([s for s in snapshots if s.get('status') == 'pending'])
    highlighted_count = len([s for s in snapshots if s.get('status') == 'highlighted'])
    accepted_count = len([s for s in snapshots if s.get('status') == 'accepted'])
    total_count = len(snapshots)
    
    with col1:
        st.metric("Total Snapshots", total_count)
    with col2:
        st.metric("Pending", pending_count, delta=f"{pending_count}/{total_count}")
    with col3:
        st.metric("Highlighted", highlighted_count, delta=f"{highlighted_count}/{total_count}")
    with col4:
        st.metric("Accepted", accepted_count, delta=f"{accepted_count}/{total_count}")
    
    st.markdown("---")
    
    # Snapshot list with CRM-style cards (sortable)
    st.markdown('<div class="snapshot-sortable-list">', unsafe_allow_html=True)
    for i, snapshot in enumerate(snapshots):
        render_snapshot_card(snapshot, i, api_url)
    st.markdown('</div>', unsafe_allow_html=True)

def render_snapshot_card(snapshot: Dict[str, Any], index: int, api_url: str):
    """
    Render individual snapshot card in CRM style with drag-and-drop functionality
    """
    # Status styling
    status = snapshot.get('status', 'unknown')
    status_colors = {
        'pending': '🟡',
        'highlighted': '🔵', 
        'accepted': '🟢',
        'archived': '⚫',
        'scraping_failed': '🔴'
    }
    
    status_emoji = status_colors.get(status, '❓')
    
    # Create expandable card with draggable attributes
    snapshot_id = snapshot.get('id')
    st.markdown(f'<div class="snapshot-sortable-item" data-item-id="{snapshot_id}" draggable="true">', unsafe_allow_html=True)
    
    with st.container():
        # Header row with key info
        col1, col2, col3, col4, col5 = st.columns([0.5, 3, 1.5, 1, 1])
        
        with col1:
            # Drag handle (now functional)
            st.markdown('<div class="snapshot-drag-handle" draggable="true">⋮⋮</div>', unsafe_allow_html=True)
        
        with col2:
            # Title and URL preview
            url = snapshot.get('url', '')
            url_preview = url.split('/')[-1][:30] + "..." if len(url.split('/')[-1]) > 30 else url.split('/')[-1]
            highlight_preview = (snapshot.get('highlight', '')[:50] + "...") if len(snapshot.get('highlight', '')) > 50 else snapshot.get('highlight', 'No highlight yet')
            
            st.markdown(f"**#{snapshot.get('position', index+1)} Snapshot**")
            st.caption(f"🔗 {url_preview}")
            st.caption(f"🚩 {highlight_preview}")
        
        with col3:
            # Status badge
            st.markdown(f"{status_emoji} **{status.upper()}**")
        
        with col4:
            # Source
            source = snapshot.get('source', 'manual_add')
            st.caption(f"📥 {source}")
        
        with col5:
            # Position controls (simplified approach)
            subcol1, subcol2 = st.columns(2)
            with subcol1:
                if st.button("⬆️", key=f"up_snap_{snapshot['id']}", help="Move Up"):
                    # Simple position update via API
                    current_pos = snapshot.get('position', index + 1)
                    if current_pos > 1:
                        try:
                            response = requests.patch(f"{api_url}/snapshots/{snapshot['id']}/position", 
                                                    json={"item_id": snapshot['id'], "new_position": current_pos - 1})
                            if response.status_code == 200:
                                st.success("Moved up!")
                                st.rerun()
                            else:
                                st.error("Failed to move up")
                        except Exception as e:
                            st.error(f"Error: {e}")
            with subcol2:
                if st.button("⬇️", key=f"down_snap_{snapshot['id']}", help="Move Down"):
                    # Simple position update via API
                    current_pos = snapshot.get('position', index + 1)
                    try:
                        response = requests.patch(f"{api_url}/snapshots/{snapshot['id']}/position", 
                                                json={"item_id": snapshot['id'], "new_position": current_pos + 1})
                        if response.status_code == 200:
                            st.success("Moved down!")
                            st.rerun()
                        else:
                            st.error("Failed to move down")
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            # Expand details button
            if st.button("⚙️", key=f"expand_snap_{snapshot['id']}", help="Expand details"):
                st.session_state[f"expanded_snap_{snapshot['id']}"] = not st.session_state.get(f"expanded_snap_{snapshot['id']}", False)
        
        # Expanded details
        if st.session_state.get(f"expanded_snap_{snapshot['id']}", False):
            with st.expander("Snapshot Details", expanded=True):
                render_snapshot_details(snapshot, api_url)
        
        st.markdown("---")
    
    # Close the draggable container
    st.markdown('</div>', unsafe_allow_html=True)

def render_snapshot_details(snapshot: Dict[str, Any], api_url: str):
    """
    Render detailed snapshot view with inline editing
    """
    # Highlight section
    st.markdown("**🚩 Highlight**")
    highlight = snapshot.get('highlight', '')
    if highlight:
        # Editable highlight
        new_highlight = st.text_area(
            "Edit Highlight",
            value=highlight,
            height=100,
            key=f"highlight_edit_{snapshot['id']}"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 Save", key=f"save_highlight_{snapshot['id']}"):
                try:
                    response = requests.patch(f"{api_url}/snapshots/{snapshot['id']}", 
                                            json={"highlight": new_highlight})
                    if response.status_code == 200:
                        st.success("Highlight saved!")
                        st.rerun()
                    else:
                        st.error("Failed to save highlight")
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.info("No highlight available. Use manual content or re-highlight.")
    
    # Manual content section (if needed)
    snapshot_status = snapshot.get('status', '')
    if 'failed' in snapshot_status.lower() or 'scraping_failed' in str(snapshot.get('highlight', '')).lower():
        st.markdown("**⚠️ Manual Content Required**")
        snapshot_url = snapshot.get('url', '')
        st.warning("Scraping failed for this snapshot. Click the link below to open it:")
        st.markdown(f"🔗 **[{snapshot_url}]({snapshot_url})**", unsafe_allow_html=True)
        
        manual_content = st.text_area(
            "Paste article content here:",
            value=f"Failed to scrape: {snapshot_url}\n\nPaste the article content here...",
            height=150,
            key=f"manual_content_snap_detail_{snapshot['id']}"
        )
        
        if st.button("🚩 Generate Highlight from Manual Content", key=f"manual_highlight_detail_{snapshot['id']}"):
            if manual_content.strip() and not manual_content.startswith("Failed to scrape:"):
                try:
                    response = requests.post(f"{api_url}/highlight-manual", json={
                        "snapshot_id": snapshot['id'],
                        "manual_content": manual_content
                    })
                    if response.status_code == 200:
                        st.success("Highlight generated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to generate highlight")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Action buttons (similar to articles)
    st.markdown("**🎯 Actions**")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("🔄 Re-highlight", key=f"rehighlight_detail_{snapshot['id']}"):
            try:
                requests.post(f"{api_url}/highlight", json={"snapshot_id": snapshot['id']})
                st.success("Re-highlighting started!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        current_status = snapshot.get('status')
        if current_status != 'accepted':
            if st.button("✅ Accept", key=f"accept_snap_detail_{snapshot['id']}"):
                try:
                    response = requests.patch(f"{api_url}/snapshots/{snapshot['id']}", 
                                            json={"status": "accepted"})
                    if response.status_code == 200:
                        st.success("Snapshot accepted!")
                        st.rerun()
                    else:
                        st.error("Failed to accept snapshot")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            if st.button("↩️ Un-accept", key=f"unaccept_snap_detail_{snapshot['id']}"):
                try:
                    response = requests.patch(f"{api_url}/snapshots/{snapshot['id']}", 
                                            json={"status": "highlighted"})
                    if response.status_code == 200:
                        st.success("Snapshot un-accepted!")
                        st.rerun()
                    else:
                        st.error("Failed to un-accept snapshot")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col3:
        if st.button("📦 Archive", key=f"archive_snap_detail_{snapshot['id']}"):
            try:
                response = requests.patch(f"{api_url}/snapshots/{snapshot['id']}", 
                                        json={"status": "archived"})
                if response.status_code == 200:
                    st.success("Snapshot archived!")
                    st.rerun()
                else:
                    st.error("Failed to archive snapshot")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col4:
        if st.button("🗑️ Delete", key=f"delete_snap_detail_{snapshot['id']}"):
            try:
                response = requests.delete(f"{api_url}/snapshots/{snapshot['id']}")
                if response.status_code == 200:
                    st.success("Snapshot deleted!")
                    st.rerun()
                else:
                    st.error("Failed to delete snapshot")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col5:
        # Position controls
        st.markdown("**Position**")
        subcol1, subcol2 = st.columns(2)
        with subcol1:
            if st.button("⬆️", key=f"up_snap_detail_{snapshot['id']}", help="Move Up"):
                # Move up logic would go here
                pass
        with subcol2:
            if st.button("⬇️", key=f"down_snap_detail_{snapshot['id']}", help="Move Down"):
                # Move down logic would go here
                pass
