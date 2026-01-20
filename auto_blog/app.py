import streamlit as st
import pandas as pd
import os
import sys
import random

# Ensure import works
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from auto_blog import trends, content, wordpress, images
from auto_blog.main import HISTORY_FILE

st.set_page_config(page_title="Auto-Blog Pro", page_icon="🚀", layout="wide")

# Session State Initialization
if 'step' not in st.session_state:
    st.session_state.step = 1 # 1=Research, 2=Select Titles, 3=Publish
if 'keywords' not in st.session_state:
    st.session_state.keywords = []
if 'selected_keywords' not in st.session_state:
    st.session_state.selected_keywords = []
if 'generated_titles' not in st.session_state:
    st.session_state.generated_titles = {} # {keyword: [titles]}
if 'final_titles' not in st.session_state:
    st.session_state.final_titles = []
if 'niche' not in st.session_state:
    st.session_state.niche = ""
if 'research_results' not in st.session_state:
    st.session_state.research_results = []
if 'niche_suggestions' not in st.session_state:
    st.session_state.niche_suggestions = []
if 'niche_input' not in st.session_state:
    st.session_state.niche_input = ""
if 'sub_niche' not in st.session_state:
    st.session_state.sub_niche = ""


st.title("🚀 Auto-Blog Ultra")

# --- STEP 1: DEEP RESEARCH ---
if st.session_state.step == 1:
    st.header("Step 1: Advanced Research & Analysis")
    
    # 1. Niche Suggestions
    st.subheader("🔥 Trending Niche Ideas")
    if st.button("✨ Suggest Hot Niches"):
        with st.spinner("Analyzing market trends..."):
            researcher = trends.KeywordResearcher()
            suggestions = researcher.suggest_niches()
            st.session_state.niche_suggestions = suggestions
            
    if 'niche_suggestions' in st.session_state and st.session_state.niche_suggestions:
        cols = st.columns(len(st.session_state.niche_suggestions))
        for i, suggestion in enumerate(st.session_state.niche_suggestions):
            if cols[i].button(suggestion):
                st.session_state.niche_input = suggestion

    # 2. Inputs
    col1, col2 = st.columns(2)
    with col1:
        niche = st.text_input("Primary Niche", value=st.session_state.get('niche_input', ''), placeholder="e.g. AI Tools")
    with col2:
        sub_niche = st.text_input("Sub-Niche (Optional)", value=st.session_state.get('sub_niche', ''), placeholder="e.g. For Productivity")
        
    col3, col4 = st.columns(2)
    with col3:
        region = st.selectbox("Target Market", ["US", "GB", "CA", "AU", "DE", "FR", "IN"])
    with col4:
        time_range = st.selectbox("Time Range", ["today 3-m", "today 12-m", "now 7-d"])

    if st.button("🔍 Start Deep Research"):
        if not niche:
            st.error("Please enter a niche.")
        else:
            st.session_state.niche = niche
            st.session_state.sub_niche = sub_niche
            
            with st.spinner(f"Performing 7-Step Analysis for '{niche}' in {region}..."):
                researcher = trends.KeywordResearcher()
                results = researcher.analyze_niche(niche, sub_niche, region, time_range)
                st.session_state.research_results = results
                
    # 3. Results Table
    if st.session_state.research_results:
        st.write(f"### Found {len(st.session_state.research_results)} High-Potential Keywords")
        
        # Convert to DataFrame for easier display
        df = pd.DataFrame(st.session_state.research_results)
        
        # Display as interactive table
        st.dataframe(
            df,
            column_config={
                "score": st.column_config.ProgressColumn("Priority Score", format="%.1f", min_value=0, max_value=100),
                "trend": st.column_config.LineChartColumn("Trend (90d)"),
                "kd": "KD (Diff)",
                "volume": "Vol (Est)"
            },
            use_container_width=True
        )
        
        # Selection
        keywords_list = [r['keyword'] for r in st.session_state.research_results]
        selected = st.multiselect("Select Keywords to Target:", keywords_list, default=keywords_list[:5])
        
        if st.button("Next: Generate Titles ➡", type="primary"):
            if not selected:
                st.error("Select at least one keyword.")
            else:
                st.session_state.selected_keywords = selected
                st.session_state.step = 2
                st.rerun()

# --- STEP 2: IDEATION ---
elif st.session_state.step == 2:
    st.header("Step 2: Title Selection")
    st.info(f"Generating titles for {len(st.session_state.selected_keywords)} keywords. This might take a moment due to rate limits...")
    
    if not st.session_state.generated_titles:
        import concurrent.futures
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Parallelize title generation
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_kw = {executor.submit(content.generate_titles, kw, count=5): kw for kw in st.session_state.selected_keywords}
            
            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_kw):
                kw = future_to_kw[future]
                try:
                    titles = future.result()
                    if titles:
                        st.session_state.generated_titles[kw] = titles
                except Exception as e:
                    st.error(f"Error generating titles for {kw}: {e}")
                
                completed_count += 1
                progress = completed_count / len(st.session_state.selected_keywords)
                progress_bar.progress(progress)
                status_text.text(f"Generated titles for {completed_count}/{len(st.session_state.selected_keywords)} keywords...")
        
        status_text.empty()
            
    st.write("### Select Best Titles")
    final_selection = []
    
    for kw, titles in st.session_state.generated_titles.items():
        st.subheader(f"📌 {kw}")
        
        # Load More Button
        if st.button(f"🔄 Generate More Titles for '{kw}'", key=f"more_{kw}"):
            with st.spinner(f"Thinking of more titles for {kw}..."):
                new_titles = content.generate_titles(kw, count=5)
                if new_titles:
                    st.session_state.generated_titles[kw].extend(new_titles)
                    st.rerun()

        # checkbox for each title
        for t in titles:
            if st.checkbox(t, key=t):
                final_selection.append(t)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ Back"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("Next: Publish posts ➡", type="primary"):
            if not final_selection:
                st.error("Please select at least one title.")
            else:
                st.session_state.final_titles = final_selection
                st.session_state.step = 3
                st.rerun()

# --- STEP 3: MASS AUTOMATION ---
elif st.session_state.step == 3:
    st.header("Step 3: Mass Automation Mode 🏭")
    st.info("This mode loops indefinitely to publish hundreds of posts for your selected keywords.")
    
    col1, col2 = st.columns(2)
    with col1:
        max_posts = st.number_input("Target Total Posts", min_value=10, max_value=1000, value=100)
    with col2:
        sitemap_url = st.text_input("Sitemap URL (for Pinging)", value=f"{content.SITE_URL}/sitemap.xml")

    # Only show 'final_titles' if they came from Step 2 MANUALLY. 
    # In Mass Mode, we generate them on the fly.
    
    if st.button("🚀 START INFINITE LOOP", type="primary"):
        status_container = st.empty()
        client = wordpress.get_wp_client()
        
        # 0. Load History to avoid duplicates
        posted_titles = set()
        if os.path.exists("posted_titles.txt"):
            with open("posted_titles.txt", "r", encoding="utf-8") as f:
                posted_titles = set([l.strip() for l in f.readlines()])
        
        # 1. Fetch Internal Links Index (Once at start)
        status_container.info("Indexing existing posts for internal linking...")
        all_posts_index = wordpress.get_all_posts(client)
        st.write(f"Indexed {len(all_posts_index)} existing posts for linking.")
        
        progress_bar = st.progress(0)
        posts_published = 0
        
        # Select base keyword(s)
        target_keywords = st.session_state.selected_keywords if st.session_state.selected_keywords else [st.session_state.niche]
        
        while posts_published < max_posts:
            import time
            import requests

            # Pick a keyword cyclically
            current_kw = target_keywords[posts_published % len(target_keywords)]
            
            # A. Generate Batch of Titles (10)
            status_container.info(f"Generating fresh titles for '{current_kw}'...")
            fresh_titles = content.generate_titles(current_kw, count=10)
            
            # Filter duplicates
            unique_titles = [t for t in fresh_titles if t not in posted_titles]
            
            if not unique_titles:
                status_container.warning(f"No new unique titles found for {current_kw}. Skipping...")
                time.sleep(2)
                continue
                
            # B. Publish Batch
            for title in unique_titles:
                if posts_published >= max_posts: break
                
                status_container.info(f"Creating post {posts_published+1}/{max_posts}: {title}")
                
                # Contextual Linking: Find top 5 relevant links from index (Simple match)
                # Naive approach: check if any word in title matches existing post title
                relevant_links = [] 
                # Shuffle index to keep links varied if no good match found
                random.shuffle(all_posts_index)
                relevant_links = all_posts_index[:5]
                
                # Generate
                post_data = content.generate_blog_post(title, st.session_state.niche, internal_links=relevant_links)
                if not post_data: continue
                
                # VALIDATION CHECKS (Visual Feedback)
                checks = content.validate_post_structure(post_data)
                all_passed = True
                with st.expander(f"✅ Validation Checks for: {title}", expanded=False): # Collapsed to save space in mass mode
                    for name, passed, details in checks:
                        if passed:
                            st.write(f"✅ **{name}**: {details}")
                        else:
                            st.write(f"❌ **{name}**: {details}")
                            all_passed = False
                
                if not all_passed:
                    status_container.warning(f"⚠️ Validation issues for '{title}', but publishing...")
                
                # SEO Meta Data
                custom_fields = []
                if post_data.get('meta_title'):
                    custom_fields.append({'key': '_yoast_wpseo_title', 'value': post_data['meta_title']})
                    custom_fields.append({'key': 'rank_math_title', 'value': post_data['meta_title']})
                if post_data.get('meta_desc'):
                    custom_fields.append({'key': '_yoast_wpseo_metadesc', 'value': post_data['meta_desc']})
                    custom_fields.append({'key': 'rank_math_description', 'value': post_data['meta_desc']})
                
                # Images
                img_urls = images.get_images(title, count=3)
                uploaded_imgs = []
                for url in img_urls:
                    local_path = images.download_image(url)
                    if local_path:
                        try:
                            resp = wordpress.upload_image_to_wp(client, local_path, title)
                            uploaded_imgs.append(resp)
                        except: pass
                        if os.path.exists(local_path): os.remove(local_path)
                
                featured_id = uploaded_imgs[0]['id'] if uploaded_imgs else None
                
                # Inject Images
                final_content = post_data['content']
                if len(uploaded_imgs) > 1:
                    parts = final_content.split('</h2>')
                    new_c = ""
                    e_idx = 1
                    for i, part in enumerate(parts):
                        new_c += part
                        if i < len(parts) - 1: new_c += "</h2>"
                        if (i == 0 or i == 2) and e_idx < len(uploaded_imgs):
                            u = uploaded_imgs[e_idx]['url']
                            new_c += f'<figure><img src="{u}" alt="{title}" style="width:100%; border-radius:10px; margin:20px 0;" /><figcaption>{title}</figcaption></figure>'
                            e_idx += 1
                    final_content = new_c

                # Publish
                try:
                    wordpress.create_wp_post(client, post_data['title'], final_content, post_data['tags'], featured_id, [st.session_state.niche], custom_fields=custom_fields)
                    
                    # Update History
                    with open("posted_titles.txt", "a", encoding="utf-8") as f:
                        f.write(title + "\n")
                    posted_titles.add(title)
                    
                    # Update Link Index
                    all_posts_index.append({'title': title, 'link': '#'}) # URL Unknown until fetch, placeholder
                    
                    posts_published += 1
                    
                except Exception as e:
                    st.error(f"Error publishing: {e}")
                
                progress_bar.progress(posts_published / max_posts)
            
            # C. Ping Google (After batch of 10 or less)
            try:
                requests.get(f"http://www.google.com/ping?sitemap={sitemap_url}")
                st.toast("✅ Sitemap Pinged to Google!")
            except:
                pass
                
        st.balloons()
        st.success("Mass Generation Complete!")

st.sidebar.markdown("---")
if st.sidebar.button("Reset App"):
    st.session_state.clear()
    st.rerun()
