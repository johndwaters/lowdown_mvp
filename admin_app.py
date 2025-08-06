# admin_app.py
import streamlit as st
import requests
from database import db_handler
import json
from pathlib import Path
from crm_components import render_crm_article_list, render_crm_snapshot_list
from compact_article_view import render_compact_article_list
from apple_article_view import render_apple_article_view

# --- Page Config ---
st.set_page_config(page_title="The Lowdown Admin", layout="wide")

# --- Load Military Theme CSS ---
def load_css():
    """Load custom military theme CSS"""
    css_file = Path(__file__).parent / "style.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    # Additional inline CSS for Grok-inspired military theme
    st.markdown("""
    <style>
    /* The Lowdown Military Header */
    .main-title {
        background: linear-gradient(90deg, #3A4A1C, #4A5D23, #5A6D33);
        color: #E8E8E8;
        padding: 1.5rem;
        border-radius: 10px;
        border: 3px solid #5A6D33;
        text-align: center;
        font-family: 'Courier New', monospace;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(74, 93, 35, 0.3);
    }
    
    .subtitle {
        color: #B8C5D1;
        font-family: 'Courier New', monospace;
        text-align: center;
        margin-top: -1rem;
        margin-bottom: 2rem;
        font-style: italic;
    }
    
    /* Military Status Badges */
    .status-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 1px;
    }
    
    .badge-accepted { background: #28A745; color: white; }
    .badge-pending { background: #FF6B35; color: white; }
    .badge-archived { background: #6C757D; color: white; }
    </style>
    """, unsafe_allow_html=True)

# Load the military theme
load_css()

# --- Config ---
API_URL = "http://127.0.0.1:8003"

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

# --- Military-Themed Header ---
st.markdown("""
<div class="main-title">
    🎯 THE LOWDOWN ADMIN
</div>
<div class="subtitle">
    [ CLASSIFIED ] Newsletter Content Management System [ CLASSIFIED ]
</div>
""", unsafe_allow_html=True)

# Sidebar removed - Article Order moved to bottom of page

# Compact Import Section - Apple UI Principles (reduced white space)
col_import, col_admin = st.columns([2, 3])  # Horizontal layout to save vertical space

with col_import:
    st.markdown("**📥 Import Articles**")  # Smaller header
    with st.form("add_articles_form"):
        urls_to_add = st.text_area(
            "URLs", 
            height=68,  # Minimum required height
            placeholder="Paste URLs, one per line...",
            label_visibility="collapsed"
        )
        submit_button = st.form_submit_button(
            "🚀 Import", 
            use_container_width=True,
            type="primary"
        )
    
    # Handle form submission
    if submit_button:
        urls = [url.strip() for url in urls_to_add.splitlines() if url.strip()]
        if urls:
            success_count = 0
            with st.spinner(f"Importing {len(urls)} articles..."):
                for url in urls:
                    try:
                        response = requests.post(f"{API_URL}/articles", json={"url": url, "title": url, "source": "manual_add"})
                        response.raise_for_status()
                        success_count += 1
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 409:
                            st.toast(f"Article already exists: {url.split('/')[-1][:30]}...", icon="⚠️")
                        else:
                            st.error(f"Failed to add {url}: {e}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Failed to add {url}: {e}")
            
            if success_count > 0:
                st.toast(f"✅ Successfully imported {success_count} article(s)!", icon="✅")
                st.rerun()
        else:
            st.warning("Please enter at least one URL")

with col_admin:
    st.markdown("**⚙️ Admin Controls**")  # Moved from below
    col_admin1, col_admin2, col_admin3 = st.columns(3)
    
    with col_admin1:
            if st.button("🗃️ Archive", help="Archive all accepted articles", use_container_width=True):
                accepted_articles = [a for a in fetch_articles_from_api() if a.get('status') == 'accepted']
                
                if accepted_articles:
                    success_count = 0
                    for article in accepted_articles:
                        try:
                            response = requests.patch(f"{API_URL}/articles/{article['id']}", 
                                                    json={"status": "archived"})
                            if response.status_code == 200:
                                success_count += 1
                        except Exception as e:
                            st.error(f"Failed to archive article {article['id']}: {e}")
                    
                    if success_count > 0:
                        st.toast(f"✅ Successfully archived {success_count} article(s)!", icon="✅")
                        st.rerun()
                else:
                    st.info("No accepted articles to archive")
    
    with col_admin2:
        if st.button("🔄 Summarize", help="Summarize all pending articles", use_container_width=True):
            try:
                response = requests.post(f"{API_URL}/batch-summarize")
                if response.status_code == 200:
                    st.toast("✅ Batch summarization started!", icon="✅")
                    st.rerun()
                else:
                    st.error("Failed to start batch summarization")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col_admin3:
        if st.button("📊 Refresh", help="Refresh article data", use_container_width=True):
            st.rerun()
    
# Article Order section moved to bottom of page

# --- Session State Initialization ---
# (Threat research data will be stored in session state as needed)

# --- TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Article Curation", "📸 Snapshot", "🔍 Threat Research", "📝 Transcript", "🚀 Export"])

with tab1:
    # Modern CRM-style Article Curation Interface
    st.markdown("<div class='military-header'>🎯 ARTICLE CURATION COMMAND CENTER</div>", unsafe_allow_html=True)
    
    # Compact Pipeline Metrics Dashboard
    articles = fetch_articles_from_api()
    total_articles = len(articles)
    pending_count = len([a for a in articles if a['status'] == 'pending'])
    summarized_count = len([a for a in articles if a['status'] == 'summarized'])
    accepted_count = len([a for a in articles if a['status'] == 'accepted'])
    
    # Compact horizontal metrics bar
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
    
    # Apple-Inspired Article Management Interface (Full Width)
    articles = fetch_articles_from_api()
    render_apple_article_view(articles, API_URL)
    
    # Article Order Section - At Bottom
    st.markdown("---")
    st.markdown("### 📋 Article Order")
    
    summarized_articles = [a for a in articles if a['status'] in ['summarized', 'accepted']]
    
    if summarized_articles:
        st.markdown(f"**{len(summarized_articles)} articles ready for export**")
        
        # Sort by position for display
        sorted_articles = sorted(summarized_articles, key=lambda x: x.get('position', 999))
        
        # Enhanced article order display with grouped controls (Apple UI principles)
        for i, article in enumerate(sorted_articles[:10]):  # Show top 10
            col_controls, col_content = st.columns([0.8, 9.2])  # Controls grouped on left
            
            with col_controls:
                # Group up/down arrows together as a single control unit
                subcol1, subcol2 = st.columns(2)
                with subcol1:
                    if i > 0 and st.button("↑", key=f"bottom_up_{article['id']}", help="Move Up"):
                        try:
                            current_position = article.get('position', i + 1)
                            new_position = current_position - 1
                            response = requests.patch(f"{API_URL}/articles/{article['id']}/position", 
                                                    json={"item_id": article['id'], "new_position": new_position})
                            if response.status_code == 200:
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                with subcol2:
                    if i < len(sorted_articles) - 1 and st.button("↓", key=f"bottom_down_{article['id']}", help="Move Down"):
                        try:
                            current_position = article.get('position', i + 1)
                            new_position = current_position + 1
                            response = requests.patch(f"{API_URL}/articles/{article['id']}/position", 
                                                    json={"item_id": article['id'], "new_position": new_position})
                            if response.status_code == 200:
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            with col_content:
                # Show much more text for better understanding
                title = article.get('title', 'Untitled')
                summary = article.get('summary', '')
                status_badge = "🟢" if article['status'] == 'accepted' else "🟠"
                
                # Display full title and summary snippet
                if len(title) > 100:
                    display_title = title[:100] + "..."
                else:
                    display_title = title
                
                st.markdown(f"**{i+1}.** {status_badge} **{display_title}**")
                
                # Show summary preview if available
                if summary:
                    summary_preview = summary[:150] + "..." if len(summary) > 150 else summary
                    st.markdown(f"<small style='color: #666; line-height: 1.3;'>{summary_preview}</small>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<small style='color: #999; font-style: italic;'>No summary available</small>", unsafe_allow_html=True)
        
        if len(sorted_articles) > 10:
            st.caption(f"... and {len(sorted_articles) - 10} more articles")
        
        # Export button
        if st.button("🚀 Export Newsletter", key="bottom_export", help="Export in current order", type="primary"):
            # Switch to export tab
            st.session_state.active_tab = "Export"
            st.rerun()
            
    else:
        st.info("📝 Summarized articles will appear here for ordering. Use ↑↓ to reorder, then export.")

with tab2:
    # Modern CRM-style Snapshot Interface
    st.markdown("<div class='military-header'>📸 SNAPSHOT COMMAND CENTER</div>", unsafe_allow_html=True)
    st.markdown("Create concise 1-sentence highlights for quick scanning. Perfect for rapid news consumption.")
    
    def fetch_snapshots_from_api():
        """Fetch snapshots from the backend API"""
        try:
            response = requests.get(f"{API_URL}/snapshots")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch snapshots: {e}")
            return []
    
    # Input section in sidebar-style layout
    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown("### 📥 Import Control")
        with st.form("add_snapshots_form"):
            urls_to_add = st.text_area(
                "Snapshot URLs", 
                height=150, 
                placeholder="Paste one or more URLs, one per line...",
                help="Import multiple snapshots by pasting URLs, one per line"
            )
            if st.form_submit_button("🚀 Import Snapshots", use_container_width=True):
                urls = [url.strip() for url in urls_to_add.splitlines() if url.strip()]
                if urls:
                    success_count = 0
                    with st.spinner(f"Importing {len(urls)} snapshots..."):
                        for url in urls:
                            try:
                                response = requests.post(f"{API_URL}/snapshots", json={"url": url, "source": "manual_add"})
                                response.raise_for_status()
                                success_count += 1
                            except requests.exceptions.HTTPError as e:
                                if e.response.status_code == 409:
                                    st.toast(f"Snapshot already exists: {url.split('/')[-1][:30]}...", icon="⚠️")
                                else:
                                    st.error(f"Failed to add {url}: {e}")
                            except requests.exceptions.RequestException as e:
                                st.error(f"Failed to add {url}: {e}")
                    
                    if success_count > 0:
                        st.toast(f"✅ Successfully imported {success_count} snapshot(s)!", icon="✅")
                        st.rerun()
                else:
                    st.warning("Please enter at least one URL.")
        
        st.markdown("### 🤖 Batch Operations")
        if st.button("🚀 Highlight All Pending", use_container_width=True):
            pending_snapshots = [s for s in fetch_snapshots_from_api() if s['status'] == 'pending']
            if not pending_snapshots:
                st.toast("No pending snapshots to highlight.", icon="👍")
            else:
                progress_bar = st.progress(0, text="Processing snapshots...")
                for i, snapshot in enumerate(pending_snapshots):
                    try:
                        requests.post(f"{API_URL}/highlight", json={"snapshot_id": snapshot['id']})
                    except Exception as e:
                        # Update status to failed if highlighting fails
                        pass
                    progress_bar.progress((i + 1) / len(pending_snapshots), text=f"Processed {i+1}/{len(pending_snapshots)}")
                st.success("✅ Batch highlighting complete!")
                st.rerun()

    with col2:
        # CRM-style snapshot list
        snapshots = fetch_snapshots_from_api()
        render_crm_snapshot_list(snapshots, API_URL)
        
        # --- Snapshot Export Section ---
        st.markdown("---")
        st.subheader("📋 Snapshot Export")
        
        # Get accepted snapshots for export
        accepted_snapshots = [s for s in snapshots if s['status'] == 'accepted']
        
        if not accepted_snapshots:
            st.info("No accepted snapshots to export. Accept some snapshots above to include them in your newsletter.")
        else:
            st.markdown(f"**{len(accepted_snapshots)} accepted snapshot(s) ready for export:**")
            
            # Build the snapshot content for export
            snapshot_content = ""
            for snapshot in accepted_snapshots:
                if snapshot.get('highlight'):
                    snapshot_content += snapshot['highlight'] + "\n\n"
            
            if snapshot_content.strip():
                st.text_area(
                    "Copy to Newsletter", 
                    value=snapshot_content.strip(), 
                    height=200,
                    help="Click in the box and press Cmd+A then Cmd+C to copy all accepted snapshot highlights."
                )
                st.caption("📋 Click in the box and press Cmd+A then Cmd+C to copy.")
                
                # Archive button for accepted snapshots
                if st.button("📦 Archive All Accepted Snapshots", type="secondary", key="snapshot_archive_btn"):
                    for snapshot in accepted_snapshots:
                        try:
                            response = requests.patch(f"{API_URL}/snapshots/{snapshot['id']}", json={"status": "archived"})
                            if response.status_code == 200:
                                st.success(f"📦 Archived snapshot #{snapshot['id']}")
                        except requests.exceptions.RequestException as e:
                            st.error(f"❌ Error archiving snapshot #{snapshot['id']}: {e}")
                    st.toast("Snapshots archived!", icon="📦")
                    st.rerun()
            else:
                st.warning("Accepted snapshots don't have highlights yet. Try re-highlighting them.")

with tab3:
    st.markdown("#### 🔍 Threat Research")
    st.markdown("Research military threats using Perplexity AI and generate formatted threat profiles.")
    
    # --- Comprehensive Threat Lists (from Excel data) ---
    threat_database = {
        "Fighter Aircraft": [
            "F-35 Lightning II", "F-22 Raptor", "F-16 Fighting Falcon", "F-15C Eagle", "F-15E Strike Eagle",
            "F/A-18C/D Hornet", "F/A-18E/F Super Hornet", "F-14 Tomcat", "Eurofighter Typhoon",
            "Dassault Rafale", "Saab JAS 39 Gripen", "MiG-21 Fishbed", "MiG-23/MF Flogger",
            "MiG-29/MiC Fulcrum", "MiG-31 Foxhound", "Su-27 Flanker", "Su-30 Flanker-C",
            "Su-33 Flanker-D", "Su-35 Flanker-E", "Su-57 Felon", "Chengdu J-7 F-7",
            "Chengdu J-10 Firebird", "Shenyang J-8 Finback", "Shenyang J-11 Flanker",
            "Shenyang J-15 Flanker", "Shenyang J-16 Flanker", "Chengdu J-20 Mighty Dragon",
            "HAL Tejas LCA", "CAC/PAC JF-17 Thunder"
        ],
        "Bomber/Attack Aircraft": [
            "B-52 Stratofortress", "B-2 Spirit", "B-1B Lancer", "Northrop Grumman B-2 Spirit",
            "Tupolev Tu-95 Bear", "Tupolev Tu-160 Blackjack", "Tupolev Tu-22M Backfire",
            "Xian H-6 Hong-6 Badger", "Sukhoi Su-24 Fencer", "Sukhoi Su-34 Fullback",
            "Panavia Tornado IDS/ECR", "SEPECAT Jaguar", "Xian JH-7 Flying Leopard",
            "Fairchild Republic A-10 Thunderbolt II Warthog", "Sukhoi Su-25 CAS/attack Frogfoot"
        ],
        "Transport Aircraft": [
            "Lockheed C-130 Hercules", "Lockheed C-17 Globemaster III", "Lockheed C-5 Galaxy",
            "Airbus A400M Atlas", "Ilyushin Il-76 Candid", "Antonov An-124 Ruslan Condor",
            "Antonov An-12 Cub", "Antonov An-26 Curl", "Embraer C-390 Millennium"
        ],
        "C2/AWACS Aircraft": [
            "Boeing E-3 Sentry AWACS", "Northrop Grumman E-2 Hawkeye", "Boeing E-7 Wedgetail AEW&C",
            "Beriev A-50 AEW&C Mainstay", "Shaanxi KJ-2000 AEW&C Mainring", "Shaanxi KJ-500 AEW&C",
            "Northrop Grumman E-8 Joint STARS", "Gulfstream E-11A Battlefield Airborne Comm. Node"
        ],
        "Air-to-Air Missiles": [
            "AIM-9 Sidewinder", "AIM-7 Sparrow", "AIM-120 AMRAAM", "AIM-54 Phoenix",
            "IRIS-T Infrared Imaging System Tail", "AIM-132 ASRAAM", "MBDA Meteor",
            "MBDA MICA IR/RF", "Vympel R-73 AA-11 Archer", "Vympel R-77 AA-12 Adder",
            "Vympel R-27 AA-10 Alamo", "Vympel R-37 AA-13 Axehead", "Vympel R-33 AA-9 Amos",
            "PL-10 PLA", "PL-12 SD-10", "PL-15"
        ],
        "Air Defense Systems": [
            "MIM-104 Patriot", "MIM-23 Stinger MANPADS", "MIM-23 HAWK", "NASAMS NASAMS II",
            "Aster 30 SAMP/T system", "S-300 SA-10", "S-400 Triumf SA-21 Growler",
            "S-500 Prometheus", "9K22 Tunguska SA-19 Grison", "9K37 Buk SA-11 Gadfly SA-17",
            "9K330 Tor SA-15 Gauntlet", "9K33 Osa SA-8 Gecko", "9K35 Strela-10 SA-13 Gopher",
            "9K32 Strela-2 SA-7 Grail", "HQ-9", "HQ-16", "HQ-7", "HQ-22"
        ],
        "Guided Bombs": [
            "GBU-10 Paveway II 2000 lb", "GBU-12 Paveway II 500 lb", "GBU-24 Paveway III 2000 lb",
            "GBU-31 JDAM 2000 lb", "GBU-32 JDAM 1000 lb", "GBU-38 JDAM 500 lb",
            "GBU-39 Small Diameter Bomb I 250 lb", "GBU-53/B SDB II StormBreaker",
            "AGM-154 JSOW glide bomb", "KAB-500L 500 kg", "KAB-1500L 1500 kg",
            "LS-6 500 kg", "FT PGM Fei Teng series"
        ],
        "Defensive Systems": [
            "THAAD Terminal High Altitude Area Defense", "Iron Dome", "Arrow 3",
            "S-500 Prometheus", "Phalanx CIWS Mk 15", "Kashtan-M", "AN/ALQ-256 DIRCM",
            "Arena APS", "ALQ-213", "ALR 69"
        ],
        "UAV/Drones": [
            "MQ-9 Reaper Predator B", "MQ-1 Predator", "MQ-1C Gray Eagle", "RQ-4 Global Hawk",
            "Baykar Bayraktar TB2", "Baykar Akinci", "IAI Heron TP Eitan", "IAI Harop",
            "Shahed-136 Geran-2", "CASC Wing Loong II", "CASIC CH-4 Cal Heng-4",
            "NORINCO Sky Hawk GV-SH", "Kronstadt Orion Inokhodets-RU", "Orlan-10", "Lancet-3"
        ]
    }
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🎯 Select Threat")
        
        # Threat category selection
        threat_category = st.selectbox(
            "Category (Optional)",
            options=["All Categories"] + list(threat_database.keys()),
            help="Filter threats by category"
        )
        
        # Build threat options based on category
        if threat_category == "All Categories":
            all_threats = []
            for category_threats in threat_database.values():
                all_threats.extend(category_threats)
            threat_options = sorted(all_threats)
        else:
            threat_options = threat_database[threat_category]
        
        # Dropdown selection
        selected_threat = st.selectbox(
            "Select from list",
            options=[""] + threat_options,
            help="Choose a threat from the curated list"
        )
        
        st.markdown("**OR**")
        
        # Manual input
        manual_threat = st.text_input(
            "Enter custom threat",
            placeholder="e.g., F-35, S-400, HIMARS",
            help="Type any military threat name"
        )
        
        # Determine which threat to research
        threat_to_research = manual_threat.strip() if manual_threat.strip() else selected_threat
        
        # Research button
        if st.button("🔍 Research Threat", type="primary", disabled=not threat_to_research):
            if threat_to_research:
                with st.spinner(f"Researching {threat_to_research}..."):
                    try:
                        # Call the threat research endpoint
                        response = requests.post(
                            f"{API_URL}/research-threat",
                            json={"threat_name": threat_to_research},
                            timeout=60
                        )
                        response.raise_for_status()
                        research_data = response.json()
                        
                        # Store results in session state
                        st.session_state.threat_research_data = research_data
                        st.session_state.researched_threat = threat_to_research
                        
                        if research_data["success"]:
                            st.success(f"✅ Research completed for {threat_to_research}!")
                        else:
                            st.error(f"❌ Research failed: {research_data.get('error', 'Unknown error')}")
                            
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Failed to research threat: {e}")
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {e}")
    
    with col2:
        st.subheader("📋 Research Results")
        
        # Display research results if available
        if hasattr(st.session_state, 'threat_research_data') and st.session_state.threat_research_data:
            research_data = st.session_state.threat_research_data
            threat_name = st.session_state.get('researched_threat', 'Unknown')
            
            if research_data["success"]:
                st.markdown(f"**Threat:** {threat_name}")
                st.markdown(f"**Type:** {research_data['threat_type'].replace('_', ' ').title()}")
                
                # Display both formats with tabs
                if research_data.get("newsletter_format") or research_data.get("research_format"):
                    format_tab1, format_tab2 = st.tabs(["📰 Newsletter Format", "🎙️ Research Format"])
                    
                    with format_tab1:
                        if research_data.get("newsletter_format"):
                            st.markdown("**Newsletter Format (Compact & Scannable):**")
                            st.markdown(research_data["newsletter_format"])
                        else:
                            st.info("Newsletter format not available")
                    
                    with format_tab2:
                        if research_data.get("research_format"):
                            st.markdown("**Research Format (Full Context):**")
                            st.markdown(research_data["research_format"])
                        else:
                            st.info("Research format not available")
                
                # Display citations
                if research_data.get("citations"):
                    st.markdown("**Sources:**")
                    for i, citation in enumerate(research_data["citations"][:5], 1):
                        st.markdown(f"{i}. {citation}")
                
                # Copy to clipboard area
                st.markdown("**Copy for Newsletter:**")
                copy_content = research_data.get("research_content", "")
                st.text_area(
                    "Research Content",
                    value=copy_content,
                    height=300,
                    help="Copy this content for your newsletter"
                )
                
                # Action buttons
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("📋 Copy to Clipboard", help="Copy research content"):
                        st.toast("Content copied! (Use Cmd+A, Cmd+C in the text area)", icon="📋")
                
                with col_btn2:
                    if st.button("🔄 Clear Results"):
                        if hasattr(st.session_state, 'threat_research_data'):
                            del st.session_state.threat_research_data
                        if hasattr(st.session_state, 'researched_threat'):
                            del st.session_state.researched_threat
                        st.rerun()
            else:
                st.error(f"Research failed for {threat_name}: {research_data.get('error', 'Unknown error')}")
        else:
            st.info("👈 Select a threat and click 'Research Threat' to get started.")
            st.markdown("""
            **How it works:**
            1. **Select** a threat from the dropdown OR type a custom threat name
            2. **Click** "Research Threat" to start Perplexity AI research
            3. **Review** the generated threat profile with current information
            4. **Copy** the content for your newsletter
            
            **Features:**
            - 🎯 **Smart categorization** (Aircraft, SAM, Munitions, Naval)
            - 🔍 **Real-time research** using Perplexity AI
            - 📚 **Reliable sources** from defense publications
            - 📋 **Formatted output** ready for newsletter use
            """)

with tab4:
    st.markdown("#### 🎤 Teleprompter Script Generator")
    st.markdown("Generate professional news-style teleprompter scripts from your accepted articles and snapshots.")
    
    # Get accepted content counts
    try:
        articles_response = requests.get(f"{API_URL}/articles")
        snapshots_response = requests.get(f"{API_URL}/snapshots")
        
        if articles_response.status_code == 200 and snapshots_response.status_code == 200:
            all_articles = articles_response.json()
            all_snapshots = snapshots_response.json()
            
            accepted_articles = [a for a in all_articles if a['status'] == 'accepted']
            accepted_snapshots = [s for s in all_snapshots if s['status'] == 'accepted']
        else:
            accepted_articles = []
            accepted_snapshots = []
    except requests.exceptions.RequestException:
        accepted_articles = []
        accepted_snapshots = []
    
    # Content overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📰 Articles", len(accepted_articles))
    with col2:
        st.metric("📸 Snapshots", len(accepted_snapshots))
    with col3:
        total_content = len(accepted_articles) + len(accepted_snapshots)
        st.metric("📈 Total Content", total_content)
    
    if total_content == 0:
        st.warning("⚠️ No accepted content found. Please accept some articles or snapshots first.")
        st.info("""
        **💡 How it works:**
        1. Accept articles in the 'Article Curation' tab
        2. Accept snapshots in the 'Snapshot' tab  
        3. Come back here to generate a teleprompter script
        4. AI will create a professional news-style script ready for recording
        """)
    else:
        st.success(f"✅ Ready to generate script from {total_content} pieces of content")
        
        # Script configuration
        st.subheader("⚙️ Script Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            include_intro = st.checkbox("🎤 Include Intro", value=True)
            include_outro = st.checkbox("🎆 Include Outro", value=True)
            
        with col2:
            host_name = st.text_input("🎤 Host Name", value="[HOST NAME]")
            show_name = st.text_input("📺 Show Name", value="The Lowdown")
        
        style = st.selectbox(
            "🎨 Script Style",
            ["news", "conversational", "formal"],
            index=0,
            help="Choose the tone and style for your teleprompter script"
        )
        
        # Generate script button
        if st.button("🎤 Generate Teleprompter Script", type="primary"):
            with st.spinner("🤖 AI is generating your teleprompter script..."):
                try:
                    # Call the Fork API
                    response = requests.post(
                        f"{API_URL}/generate-teleprompter",
                        json={
                            "include_intro": include_intro,
                            "include_outro": include_outro,
                            "host_name": host_name,
                            "show_name": show_name,
                            "style": style
                        },
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        script_data = response.json()
                        
                        if script_data["success"]:
                            # Display script metrics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("🔢 Word Count", script_data["word_count"])
                            with col2:
                                st.metric("⏱️ Est. Duration", script_data["estimated_duration"])
                            with col3:
                                st.metric("🎨 Style", style.title())
                            
                            # Display the generated script
                            st.subheader("📜 Generated Teleprompter Script")
                            st.text_area(
                                "Copy to Teleprompter",
                                value=script_data["script"],
                                height=600,
                                help="Click in the box and press Cmd+A then Cmd+C to copy the entire script"
                            )
                            st.caption("📋 Click in the box and press Cmd+A then Cmd+C to copy.")
                            
                            # Action buttons
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("📋 Copy Script"):
                                    st.toast("Script ready to copy! (Use Cmd+A, Cmd+C in the text area)", icon="📋")
                            
                            with col2:
                                if st.button("💾 Download Script"):
                                    st.toast("Download feature coming soon!", icon="💾")
                            
                            with col3:
                                if st.button("🔄 Generate New"):
                                    st.rerun()
                            
                            # Script tips
                            st.info("""
                            **🎤 Teleprompter Tips:**
                            - **[PAUSE]** markers indicate natural breathing points
                            - **Bold text** indicates emphasis for key points
                            - Read at ~155 words per minute for natural delivery
                            - Practice the script before recording for best results
                            """)
                            
                        else:
                            st.error(f"❌ Script generation failed: {script_data.get('error', 'Unknown error')}")
                    else:
                        st.error(f"❌ API request failed with status {response.status_code}")
                        
                except Exception as e:
                    st.error(f"❌ Failed to generate script: {e}")
        
        # Content preview
        if st.expander("🔍 Preview Content to be Scripted", expanded=False):
            if accepted_articles:
                st.markdown("**📰 Articles:**")
                for i, article in enumerate(accepted_articles, 1):
                    st.markdown(f"{i}. **{article['title']}** ({article['source']})")
            
            if accepted_snapshots:
                st.markdown("**📸 Snapshots:**")
                for i, snapshot in enumerate(accepted_snapshots, 1):
                    if snapshot.get('highlight'):
                        st.markdown(f"{i}. {snapshot['highlight'][:100]}...")

with tab5:
    st.markdown("#### 🚀 Export Newsletter")

    # 1. Get Accepted Articles
    accepted_articles = [a for a in fetch_articles_from_api() if a['status'] == 'accepted']
    
    if not accepted_articles:
        st.warning("No 'accepted' articles to export. Please accept some articles in the 'Article Curation' tab.")
    else:
        st.subheader("Final Preview")
        
        # Build the newsletter content
        final_content = ""
        for article in accepted_articles:
            final_content += format_summary_for_export(article) + "\n\n---\n\n"
        
        # Add threat research if available in session state
        if hasattr(st.session_state, 'threat_research_data') and st.session_state.threat_research_data:
            research_data = st.session_state.threat_research_data
            threat_name = st.session_state.get('researched_threat', 'Unknown Threat')
            
            if research_data.get("success") and research_data.get("newsletter_format"):
                final_content += "## Threat Analysis\n\n"
                final_content += research_data['newsletter_format']

        st.text_area("Copy to Beehiiv", value=final_content, height=400)
        st.caption("Click in the box and press Cmd+A then Cmd+C to copy.")

        if st.button("Archive Articles & Clear", type="primary"):
            for article in accepted_articles:
                db_handler.update_article(article['id'], status='archived')
            # Clear threat research data if present
            if hasattr(st.session_state, 'threat_research_data'):
                del st.session_state.threat_research_data
            if hasattr(st.session_state, 'researched_threat'):
                del st.session_state.researched_threat
            st.toast("Newsletter content archived!", icon="📦")
            st.rerun()
        
        # --- Snapshot Export Section ---
        st.markdown("---")
        st.subheader("📸 Snapshot Export")
        
        # Get accepted snapshots for export
        try:
            snapshots_response = requests.get(f"{API_URL}/snapshots")
            if snapshots_response.status_code == 200:
                all_snapshots = snapshots_response.json()
                accepted_snapshots = [s for s in all_snapshots if s['status'] == 'accepted']
            else:
                accepted_snapshots = []
        except requests.exceptions.RequestException:
            accepted_snapshots = []
        
        if not accepted_snapshots:
            st.info("No accepted snapshots to export. Accept some snapshots in the 'Snapshot' tab to include them in your newsletter.")
        else:
            st.markdown(f"**{len(accepted_snapshots)} accepted snapshot(s) ready for export:**")
            
            # Build the snapshot content for export
            snapshot_content = ""
            for snapshot in accepted_snapshots:
                if snapshot.get('highlight'):
                    snapshot_content += snapshot['highlight'] + "\n\n"
            
            if snapshot_content.strip():
                st.text_area(
                    "Copy Snapshots to Newsletter", 
                    value=snapshot_content.strip(), 
                    height=200,
                    help="Click in the box and press Cmd+A then Cmd+C to copy all accepted snapshot highlights."
                )
                st.caption("📋 Click in the box and press Cmd+A then Cmd+C to copy.")
                
                # Archive button for accepted snapshots
                if st.button("📦 Archive All Accepted Snapshots", type="secondary", key="export_archive_btn"):
                    for snapshot in accepted_snapshots:
                        try:
                            response = requests.patch(f"{API_URL}/snapshots/{snapshot['id']}", json={"status": "archived"})
                            if response.status_code == 200:
                                st.success(f"📦 Archived snapshot #{snapshot['id']}")
                        except requests.exceptions.RequestException as e:
                            st.error(f"❌ Error archiving snapshot #{snapshot['id']}: {e}")
                    st.toast("Snapshots archived!", icon="📦")
                    st.rerun()
            else:
                st.warning("Accepted snapshots don't have highlights yet. Try re-highlighting them in the Snapshot tab.")
        
        # --- Threat Research Export Section ---
        st.markdown("---")
        st.subheader("🔍 Threat Research Export")
        
        # Check if threat research data is available
        if hasattr(st.session_state, 'threat_research_data') and st.session_state.threat_research_data:
            research_data = st.session_state.threat_research_data
            threat_name = st.session_state.get('researched_threat', 'Unknown Threat')
            
            if research_data.get("success"):
                st.markdown(f"**Current Threat Research:** {threat_name}")
                
                # Research content export (detailed version)
                if research_data.get("research_content"):
                    st.text_area(
                        "Copy Threat Research to Newsletter", 
                        value=research_data['research_content'], 
                        height=300,
                        help="Detailed threat research content with comprehensive analysis."
                    )
                    st.caption("📋 Click in the box and press Cmd+A then Cmd+C to copy.")
                
                # Clear threat research button
                if st.button("🗑️ Clear Threat Research", type="secondary", key="export_clear_threat"):
                    if hasattr(st.session_state, 'threat_research_data'):
                        del st.session_state.threat_research_data
                    if hasattr(st.session_state, 'researched_threat'):
                        del st.session_state.researched_threat
                    st.toast("Threat research cleared!", icon="🗑️")
                    st.rerun()
            else:
                st.warning("Threat research data is available but contains errors. Please re-run the research in the Threat Research tab.")
        else:
            st.info("No threat research data available. Generate threat research in the 'Threat Research' tab to include it in your newsletter.")
