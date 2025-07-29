# admin_app.py
import streamlit as st
import requests
from database import db_handler

# --- Page Config ---
st.set_page_config(page_title="The Lowdown Admin", layout="wide")

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

# --- Main App ---
st.title("The Lowdown - Content Curation")

# --- Session State Initialization ---
if 'threat_of_day_id' not in st.session_state:
    st.session_state.threat_of_day_id = None

# --- TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Article Curation", "🔥 Threat of the Day", "🔍 Threat Research", "📝 Transcript", "🚀 Export"])

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
        
        # Status display with color coding
        status = threat.get('status', 'draft')
        status_color = {
            'accepted': '🟢',
            'pending': '🟡', 
            'draft': '⚪',
            'archived': '⚫'
        }.get(status, '⚪')
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.text(f"Type: {threat.get('type', 'N/A')} | Country: {threat.get('country_of_origin', 'N/A')}")
        with col2:
            st.markdown(f"**Status:** {status_color} {status.title()}")

        tod_summary = st.text_area(
            "Threat of the Day Summary", 
            value=threat.get('tod_summary', ''), 
            height=200,
            key=f"tod_summary_{threat_id}"
        )

        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 Save Summary", key=f"save_threat_{threat_id}"):
                db_handler.update_threat(threat_id, {'tod_summary': tod_summary})
                st.toast("Threat summary saved!", icon="✅")
                st.rerun()
        
        with col2:
            if status != 'accepted':
                if st.button("✅ Accept", key=f"accept_threat_{threat_id}"):
                    try:
                        # Update threat status to accepted
                        response = requests.patch(f"{API_URL}/threats/{threat_id}", json={"status": "accepted"})
                        response.raise_for_status()
                        st.toast("Threat accepted!", icon="✅")
                        st.rerun()
                    except requests.exceptions.RequestException as e:
                        st.error(f"Failed to accept threat: {e}")
            else:
                if st.button("↩️ Un-accept", key=f"unaccept_threat_{threat_id}"):
                    try:
                        # Update threat status back to draft
                        response = requests.patch(f"{API_URL}/threats/{threat_id}", json={"status": "draft"})
                        response.raise_for_status()
                        st.toast("Threat un-accepted!", icon="↩️")
                        st.rerun()
                    except requests.exceptions.RequestException as e:
                        st.error(f"Failed to un-accept threat: {e}")
        
        with col3:
            if st.button("📦 Archive", key=f"archive_threat_{threat_id}"):
                try:
                    response = requests.patch(f"{API_URL}/threats/{threat_id}", json={"status": "archived"})
                    response.raise_for_status()
                    st.toast("Threat archived!", icon="📦")
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to archive threat: {e}")
        
        with col4:
            if st.button("🗑️ Delete", key=f"delete_threat_{threat_id}"):
                try:
                    response = requests.delete(f"{API_URL}/threats/{threat_id}")
                    response.raise_for_status()
                    st.toast("Threat deleted!", icon="🗑️")
                    # Clear session state if this was the selected threat
                    if st.session_state.threat_of_day_id == threat_id:
                        st.session_state.threat_of_day_id = None
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to delete threat: {e}")

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
    st.markdown("#### 📝 Podcast/YouTube Transcript Builder")
    
    # Get accepted articles for transcript
    accepted_articles = [a for a in fetch_articles_from_api() if a['status'] == 'accepted']
    
    if not accepted_articles:
        st.warning("No 'accepted' articles found. Please accept some articles in the 'Article Curation' tab first.")
        st.info("💡 **How it works:** This page builds podcast/YouTube transcripts by taking your accepted articles and using Perplexity AI to add rich context, background, and expert analysis for each story.")
    else:
        st.success(f"📰 Found {len(accepted_articles)} accepted articles ready for transcript enhancement")
        
        # Article selection for context enhancement
        st.subheader("🔍 Select Articles for Context Enhancement")
        
        # Initialize session state for transcript data
        if 'transcript_data' not in st.session_state:
            st.session_state.transcript_data = {}
        
        # Display articles with enhancement options
        for i, article in enumerate(accepted_articles):
            with st.expander(f"📄 {article['title'][:80]}...", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Source:** {article['source']}")
                    st.markdown(f"**Summary:** {article['summary'][:200]}...")
                    if article.get('url'):
                        st.markdown(f"**URL:** [Link]({article['url']})")
                
                with col2:
                    article_key = f"article_{article['id']}"
                    
                    if st.button(f"🔍 Enhance with Context", key=f"enhance_{article['id']}"):
                        with st.spinner(f"Adding context to: {article['title'][:50]}..."):
                            try:
                                # Create context enhancement prompt
                                context_prompt = f"""
                                Provide detailed background context and analysis for this news story:
                                
                                Title: {article['title']}
                                Summary: {article['summary']}
                                
                                Please provide:
                                1. Historical background and context
                                2. Key stakeholders and implications
                                3. Technical details and expert analysis
                                4. Broader geopolitical significance
                                5. Recent developments and trends
                                
                                Format as a detailed, conversational analysis suitable for podcast narration.
                                """
                                
                                # Call Perplexity for context enhancement
                                response = requests.post(
                                    f"{API_URL}/research-threat",
                                    json={"threat_name": context_prompt},
                                    timeout=60
                                )
                                response.raise_for_status()
                                context_data = response.json()
                                
                                if context_data["success"]:
                                    # Store enhanced context
                                    st.session_state.transcript_data[article_key] = {
                                        'article': article,
                                        'enhanced_context': context_data.get('research_content', ''),
                                        'citations': context_data.get('citations', [])
                                    }
                                    st.success("✅ Context added successfully!")
                                else:
                                    st.error(f"❌ Enhancement failed: {context_data.get('error', 'Unknown error')}")
                                    
                            except Exception as e:
                                st.error(f"❌ Failed to enhance article: {e}")
                    
                    # Show if already enhanced
                    if article_key in st.session_state.transcript_data:
                        st.success("✅ Enhanced")
                        if st.button(f"🗑️ Remove", key=f"remove_{article['id']}"):
                            del st.session_state.transcript_data[article_key]
                            st.rerun()
        
        # Transcript Builder Section
        if st.session_state.transcript_data:
            st.subheader("🎙️ Transcript Builder")
            
            # Transcript structure options
            col1, col2 = st.columns(2)
            with col1:
                include_intro = st.checkbox("Include Intro", value=True)
                include_threat_of_day = st.checkbox("Include Threat of the Day", value=True)
            with col2:
                include_outro = st.checkbox("Include Outro", value=True)
                conversational_tone = st.checkbox("Conversational Tone", value=True)
            
            if st.button("🎬 Generate Full Transcript", type="primary"):
                transcript = ""
                
                # Intro
                if include_intro:
                    transcript += """# The Lowdown Podcast - Episode [NUMBER]

## Introduction

Welcome back to The Lowdown, your essential briefing on the latest developments in defense, security, and military technology. I'm [HOST NAME], and today we're diving deep into some significant stories that are shaping the strategic landscape.

---

"""
                
                # Enhanced Articles
                transcript += "## Today's Stories\n\n"
                
                for i, (article_key, data) in enumerate(st.session_state.transcript_data.items(), 1):
                    article = data['article']
                    context = data['enhanced_context']
                    
                    transcript += f"""### Story {i}: {article['title']}

**Quick Summary:**
{article['summary']}

**Deep Dive Analysis:**
{context}

**Key Takeaways:**
- [Add 2-3 key points for listeners]
- [Highlight implications]
- [Note what to watch for next]

---

"""
                
                # Threat of the Day
                if include_threat_of_day:
                    # Get accepted threats
                    accepted_threats = [t for t in db_handler.fetch_all_threats() if t.get('status') == 'accepted']
                    
                    if accepted_threats:
                        # Use the first accepted threat, or the selected one if it's accepted
                        threat_of_day = None
                        if st.session_state.threat_of_day_id:
                            selected_threat = db_handler.get_threat_by_id(st.session_state.threat_of_day_id)
                            if selected_threat and selected_threat.get('status') == 'accepted':
                                threat_of_day = selected_threat
                        
                        # If no accepted selected threat, use the first accepted one
                        if not threat_of_day:
                            threat_of_day = accepted_threats[0]
                        
                        transcript += f"""## Threat of the Day: {threat_of_day['name']}

{threat_of_day.get('tod_summary', 'No summary available')}

---

"""
                    else:
                        transcript += """## Threat of the Day

*No accepted threats available. Please accept a threat in the 'Threat of the Day' tab.*

---

"""
                
                # Outro
                if include_outro:
                    transcript += """## Closing Thoughts

[Add your analysis and perspective on today's stories]

## Wrap-Up

That's a wrap on today's episode of The Lowdown. If you found this analysis valuable, please subscribe and share with others who need to stay informed on defense and security developments.

For more detailed analysis and the latest updates, check out our newsletter at [WEBSITE]. 

I'm [HOST NAME], thanks for listening, and we'll see you next time on The Lowdown.

---

**Episode Notes:**
- Total Runtime: [TIME]
- Stories Covered: {len(st.session_state.transcript_data)}
- Research Sources: Multiple defense publications and expert analysis
"""
                
                # Display the generated transcript
                st.subheader("📝 Generated Transcript")
                st.text_area(
                    "Full Podcast/YouTube Transcript",
                    value=transcript,
                    height=600,
                    help="Copy this transcript for your podcast/YouTube production"
                )
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📋 Copy Transcript"):
                        st.toast("Transcript ready to copy! (Use Cmd+A, Cmd+C in the text area)", icon="📋")
                
                with col2:
                    if st.button("💾 Save Draft"):
                        # Could implement saving to database later
                        st.toast("Draft saved to session!", icon="💾")
                
                with col3:
                    if st.button("🔄 Clear All"):
                        st.session_state.transcript_data = {}
                        st.rerun()
        
        else:
            st.info("👆 Enhance some articles with context to start building your transcript.")
            st.markdown("""
            **💡 Transcript Builder Features:**
            - 🔍 **Context Enhancement**: Uses Perplexity AI to add background and analysis
            - 🎙️ **Podcast Structure**: Organized intro, stories, threat of the day, outro
            - 📝 **Copy-Ready Format**: Formatted for easy podcast/YouTube production
            - 🎯 **Conversational Tone**: Written for natural narration
            """)

with tab5:
    st.markdown("#### 🚀 Export Newsletter")

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
