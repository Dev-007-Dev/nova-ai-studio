"""NOVA AI STUDIO - Next-Generation AI-Powered Creative Visual Studio.

Frontend & Application Workflow built with Streamlit.
Supports Natural Language Search, AI Vision Captioning, Multi-Version Tracking,
Preset Transforms, and Generative Edits via OpenAI, Gemini, and Local Neural Engine.
"""

import os
from pathlib import Path
from typing import Dict, Any, List
import streamlit as st
from PIL import Image

# Backend imports
from backend.config import (
    BASE_DIR,
    PRESET_EDITS,
    OPENAI_API_KEY as DEFAULT_OPENAI_KEY,
    GEMINI_API_KEY as DEFAULT_GEMINI_KEY,
    OPENAI_API_BASE as DEFAULT_OPENAI_BASE,
    AZURE_OPENAI_MODEL as DEFAULT_AZURE_MODEL
)
from backend.storage import StorageManager
from backend.vision_captioner import analyze_image
from backend.edit_engine import EditEngine, synthesize_prompt_with_llm
from backend.search_engine import SearchEngine
from seed_sample_data import seed_library

# ==============================================================================
# Page Configuration & Styling
# ==============================================================================
st.set_page_config(
    page_title="Nova AI | Creative Studio",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
css_path = BASE_DIR / "assets" / "style.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize Session State
NAV_TABS = [
    "🖼️ Image Library & Search",
    "🎨 Studio & Edit Mode",
    "📜 Version History & Lineage",
    "🧪 Prompt Engineering & Architecture"
]

if "storage" not in st.session_state:
    st.session_state.storage = StorageManager()
if "edit_engine" not in st.session_state:
    st.session_state.edit_engine = EditEngine()
if "search_engine" not in st.session_state:
    st.session_state.search_engine = SearchEngine()
if "selected_image_id" not in st.session_state:
    st.session_state.selected_image_id = None
if "active_tab" not in st.session_state or st.session_state.active_tab not in NAV_TABS:
    st.session_state.active_tab = NAV_TABS[0]
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = DEFAULT_OPENAI_KEY
if "openai_api_base" not in st.session_state:
    st.session_state.openai_api_base = DEFAULT_OPENAI_BASE
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = DEFAULT_GEMINI_KEY
if "engine_mode" not in st.session_state:
    st.session_state.engine_mode = "openai" if DEFAULT_OPENAI_KEY else "local"
if "last_engineered_prompt" not in st.session_state:
    st.session_state.last_engineered_prompt = None

storage: StorageManager = st.session_state.storage
edit_engine: EditEngine = st.session_state.edit_engine
search_engine: SearchEngine = st.session_state.search_engine


# Helper for rendering dominant color swatch dots
def get_color_hex(color_name: str) -> str:
    cn = color_name.lower()
    palette = {
        "orange": "#f97316", "terracotta": "#c2410c", "green": "#22c55e",
        "olive": "#84cc16", "sunlight": "#fde047", "teal": "#14b8a6",
        "turquoise": "#06b6d4", "amber": "#f59e0b", "sand": "#d4b996",
        "azure": "#0284c7", "blue": "#3b82f6", "oak": "#92400e",
        "brown": "#78350f", "cream": "#fef3c7", "latte": "#e2d5c3",
        "sage": "#86efac", "tortoiseshell": "#a16207", "golden": "#eab308",
        "emerald": "#10b981", "sky": "#38bdf8", "beige": "#f5f5dc",
        "black": "#18181b", "white": "#f8fafc", "cyan": "#06b6d4",
        "magenta": "#d946ef", "purple": "#a855f7", "gray": "#94a3b8", "red": "#ef4444"
    }
    for k, v in palette.items():
        if k in cn:
            return v
    return "#818cf8"


# ==============================================================================
# Sidebar: Settings, Model Config & Library Status
# ==============================================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand-card">
      <div style="display:flex; align-items:center; gap:12px;">
        <span style="font-size:1.8rem; filter:drop-shadow(0 0 10px rgba(99,102,241,0.6));">✦</span>
        <div>
          <h2 style="margin:0; font-size:1.35rem; font-weight:800; font-family:'Space Grotesk',sans-serif; letter-spacing:-0.03em; background:linear-gradient(135deg, #ffffff 20%, #818cf8 80%, #38bdf8 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">NOVA AI</h2>
          <span style="font-size:0.72rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.08em; font-weight:600;">Creative Studio v2.0</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("⚙️ AI Engine & Configuration")

    is_azure = bool(st.session_state.openai_api_base and "azure" in st.session_state.openai_api_base.lower())
    key_label = "Azure OpenAI Key" if is_azure else "OpenAI API Key"

    # API Keys Configuration
    user_openai_key = st.text_input(
        key_label,
        value=st.session_state.openai_api_key,
        type="password",
        help="Enables Vision scene understanding & prompt synthesis (GPT-4o / GPT-4.1-mini / DALL-E 3)"
    )
    if user_openai_key != st.session_state.openai_api_key:
        st.session_state.openai_api_key = user_openai_key

    with st.expander("🌐 Custom Endpoint / Azure Foundry URL", expanded=is_azure):
        user_endpoint = st.text_input(
            "API Base URL",
            value=st.session_state.openai_api_base,
            help="Azure AI Foundry endpoint (e.g. .../openai/v1) or custom base URL"
        )
        if user_endpoint != st.session_state.openai_api_base:
            st.session_state.openai_api_base = user_endpoint
            os.environ["OPENAI_API_BASE"] = user_endpoint

    user_gemini_key = st.text_input(
        "Google Gemini API Key",
        value=st.session_state.gemini_api_key,
        type="password",
        help="Enables Gemini 1.5 Flash Vision analysis & Imagen generation"
    )
    if user_gemini_key != st.session_state.gemini_api_key:
        st.session_state.gemini_api_key = user_gemini_key

    # Active Provider Selector
    available_engines = []
    if st.session_state.openai_api_key:
        engine_title = "🤖 Azure OpenAI (GPT-4.1-mini)" if is_azure else "🤖 OpenAI (GPT-4o + DALL-E 3)"
        available_engines.append(engine_title)
    if st.session_state.gemini_api_key:
        available_engines.append("🌟 Google Gemini (Flash Vision)")
    available_engines.append("⚡ Smart Neural Engine (Zero Cost & Fast)")

    default_engine_idx = 0
    if st.session_state.engine_mode == "local" and "⚡ Smart Neural Engine (Zero Cost & Fast)" in available_engines:
        default_engine_idx = available_engines.index("⚡ Smart Neural Engine (Zero Cost & Fast)")
    elif st.session_state.engine_mode == "gemini":
        for idx, eng in enumerate(available_engines):
            if "Gemini" in eng:
                default_engine_idx = idx

    selected_engine_label = st.selectbox(
        "Active Creative Engine",
        options=available_engines,
        index=default_engine_idx
    )
    if "OpenAI" in selected_engine_label or "Azure" in selected_engine_label:
        st.session_state.engine_mode = "openai"
    elif "Gemini" in selected_engine_label:
        st.session_state.engine_mode = "gemini"
    else:
        st.session_state.engine_mode = "local"

    # Status Pill with animated glow
    if st.session_state.engine_mode == "openai":
        status_text = "Azure GPT-4.1-mini Connected" if is_azure else "OpenAI GPT-4o Connected"
        st.markdown(f"""
        <div style="background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.3); border-radius:10px; padding:8px 12px; display:flex; align-items:center; gap:8px; font-size:0.82rem; color:#34d399;">
          <span class="pulse-dot"></span> <strong>{status_text}</strong>
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state.engine_mode == "gemini":
        st.markdown("""
        <div style="background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.3); border-radius:10px; padding:8px 12px; display:flex; align-items:center; gap:8px; font-size:0.82rem; color:#34d399;">
          <span class="pulse-dot"></span> <strong>Google Gemini Connected</strong>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(99,102,241,0.12); border:1px solid rgba(99,102,241,0.3); border-radius:10px; padding:8px 12px; display:flex; align-items:center; gap:8px; font-size:0.82rem; color:#a5b4fc;">
          <span class="pulse-dot" style="background:#818cf8; box-shadow:0 0 8px #818cf8;"></span> <strong>Local Neural Engine Active (Offline)</strong>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    st.subheader("📊 Studio Telemetry")
    all_imgs = storage.get_all_images()
    total_versions = sum(len(img.get("versions", [])) for img in all_imgs)

    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.markdown(f"""
        <div class="stat-pill">
          <span class="label">Library Assets</span>
          <span class="value">{len(all_imgs)}</span>
        </div>
        """, unsafe_allow_html=True)
    with col_stat2:
        st.markdown(f"""
        <div class="stat-pill">
          <span class="label">Total Versions</span>
          <span class="value">{total_versions}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Reseed Sample Portfolio", use_container_width=True):
        seed_library()
        st.success("Sample images and revisions restored!")
        st.rerun()

    st.markdown("""
    <div class="sidebar-footer">
      <strong style="color:#cbd5e1;">✦ Nova AI Studio</strong><br>
      • Natural Language Semantic Search<br>
      • Multi-Modal Scene Auto-Captioning<br>
      • Prompt Synthesis Pipeline<br>
      • Non-Destructive Version Trees<br>
      <div style="margin-top:10px; font-size:0.7rem; color:#64748b;">
        Created with passion by the <strong>Nova AI Team</strong>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# Main Navigation Header & Hero Banner
# ==============================================================================
engine_badge_name = "OpenAI GPT-4o" if st.session_state.engine_mode == "openai" else ("Gemini Flash" if st.session_state.engine_mode == "gemini" else "Local Neural")

st.markdown(f"""
<div class="nova-header">
  <div class="nova-header-inner">
    <div class="nova-title-group">
      <div class="nova-title">
        <span>✦ NOVA AI</span>
        <span class="nova-brand-badge">STUDIO PRO</span>
      </div>
      <div class="nova-subtitle">
        Next-generation visual editing studio powered by multimodal vision and generative intelligence. Search image assets in human language, synthesize creative edits with prompt engineering, and inspect complete non-destructive revision lineage.
      </div>
    </div>
    <div class="nova-header-telemetry">
      <div class="nova-telemetry-chip">
        <span class="pulse-dot"></span>
        <span>Engine: <strong>{engine_badge_name}</strong></span>
      </div>
      <div class="nova-telemetry-chip">
        <span>Assets: <strong>{len(all_imgs)}</strong></span>
      </div>
      <div class="nova-telemetry-chip">
        <span>Revisions: <strong>{total_versions}</strong></span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

selected_tab = st.radio(
    "Navigation",
    options=NAV_TABS,
    index=NAV_TABS.index(st.session_state.active_tab),
    horizontal=True,
    label_visibility="collapsed",
    key="main_navigation_bar"
)
if selected_tab != st.session_state.active_tab:
    st.session_state.active_tab = selected_tab
    st.rerun()


# ==============================================================================
# TAB 1: Image Library & Natural Language Search
# ==============================================================================
if st.session_state.active_tab == NAV_TABS[0]:
    all_images = storage.get_all_images()

    st.markdown("### 🔍 Search Image Assets in Natural Language")
    st.caption("Ask in everyday human phrases — our hybrid semantic search parses visual attributes, objects, and concepts.")

    col_search, col_clear = st.columns([5, 1])
    with col_search:
        search_query = st.text_input(
            "Natural Language Search",
            placeholder="Try: 'alpine mountain reflection', 'cyberpunk city neon', 'fashion portrait', 'dog in meadow', 'creator workspace'...",
            label_visibility="collapsed"
        )
    with col_clear:
        if st.button("Reset Search", use_container_width=True):
            search_query = ""
            st.rerun()

    # Quick Search Exploration Chips
    st.markdown("<span style='font-size:0.76rem; color:#94a3b8; font-weight:600; text-transform:uppercase; letter-spacing:0.06em;'>Quick Concept Filters:</span>", unsafe_allow_html=True)
    chip_cols = st.columns(6)
    with chip_cols[0]:
        if st.button("🏔️ Alpine Lake", key="chip_mountain", use_container_width=True):
            search_query = "mountain lake"
    with chip_cols[1]:
        if st.button("🐕 Pets & Dogs", key="chip_dog", use_container_width=True):
            search_query = "dog"
    with chip_cols[2]:
        if st.button("☕ Workspace", key="chip_coffee", use_container_width=True):
            search_query = "workspace"
    with chip_cols[3]:
        if st.button("👩 Fashion Portrait", key="chip_portrait", use_container_width=True):
            search_query = "fashion portrait"
    with chip_cols[4]:
        if st.button("🌆 Cyberpunk City", key="chip_cyberpunk", use_container_width=True):
            search_query = "cyberpunk neon"
    with chip_cols[5]:
        if st.button("🎨 Edited Only", key="chip_edited", use_container_width=True):
            search_query = "edited"

    # Upload New Image Accordion
    with st.expander("📤 Upload New Image to Library", expanded=(len(all_images) == 0)):
        upload_col1, upload_col2 = st.columns([3, 2])
        with upload_col1:
            uploaded_file = st.file_uploader(
                "Choose an image (PNG, JPG, JPEG, WEBP)",
                type=["png", "jpg", "jpeg", "webp"],
                key="library_uploader"
            )
        with upload_col2:
            custom_title = st.text_input("Custom Title (Optional)", placeholder="e.g. Sunset in Malibu")
            auto_caption = st.checkbox("Auto-analyze image with AI Vision", value=True)

        if uploaded_file is not None:
            if st.button("🚀 Process & Ingest into Library", type="primary", use_container_width=True):
                with st.spinner("Analyzing image composition with Vision AI..."):
                    pil_img = Image.open(uploaded_file)
                    caption_data = {}
                    if auto_caption:
                        caption_data = analyze_image(
                            pil_img,
                            provider=st.session_state.engine_mode,
                            openai_key=st.session_state.openai_api_key,
                            gemini_key=st.session_state.gemini_api_key,
                            filename=uploaded_file.name,
                            base_url=st.session_state.get("openai_api_base")
                        )

                    new_record = storage.add_original_image(
                        pil_image=pil_img,
                        filename=uploaded_file.name,
                        title=custom_title or caption_data.get("title"),
                        caption=caption_data.get("caption"),
                        tags=caption_data.get("tags"),
                        objects=caption_data.get("objects"),
                        dominant_colors=caption_data.get("dominant_colors")
                    )
                    st.success(f"Added '{new_record['title']}' to your library!")
                    st.session_state.selected_image_id = new_record["id"]
                    st.rerun()

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # Perform Search
    if search_query:
        search_results = search_engine.search(
            search_query,
            all_images,
            openai_key=st.session_state.openai_api_key
        )
        st.markdown(f"**Found {len(search_results)} match{'es' if len(search_results) != 1 else ''} for query:** <span class='badge-match'>'{search_query}'</span>", unsafe_allow_html=True)
    else:
        search_results = [(img, 1.0, []) for img in all_images]
        st.markdown(f"**Displaying all {len(all_images)} cataloged assets**")

    # Gallery Grid
    if not search_results:
        st.info("No images matched your query. Try terms like 'beach', 'sunset', 'portrait', or 'dog'.")
    else:
        cols_per_row = 3
        for i in range(0, len(search_results), cols_per_row):
            grid_cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(search_results):
                    img_rec, score, reasons = search_results[i + j]
                    active_ver = storage.get_active_version(img_rec)
                    thumb_path = BASE_DIR / active_ver["thumbnail_path"]

                    with grid_cols[j]:
                        with st.container(border=True):
                            # Thumbnail image with rounded styling
                            if thumb_path.exists():
                                st.image(str(thumb_path), use_container_width=True)
                            else:
                                orig_full = BASE_DIR / active_ver["image_path"]
                                if orig_full.exists():
                                    st.image(str(orig_full), use_container_width=True)

                            # Title & Badges
                            ver_count = len(img_rec.get("versions", []))
                            active_ver_num = active_ver.get("version_number", 0)

                            badge_html = f"<span class='badge-version'>v{active_ver_num} ({ver_count} revs)</span>"
                            if search_query and score > 0.1:
                                badge_html += f" <span class='badge-match'>{int(score*100)}% Match</span>"

                            st.markdown(f"""
                            <div style="margin-top:10px; margin-bottom:8px;">
                              <strong style="font-size:1.08rem; color:#f8fafc; font-family:'Space Grotesk',sans-serif;">{img_rec.get('title', 'Untitled')}</strong><br>
                              <div style="margin-top:4px;">{badge_html}</div>
                            </div>
                            """, unsafe_allow_html=True)

                            # Search match reasons
                            if reasons:
                                reason_tags = " ".join([f"<span class='badge-tag'>{r}</span>" for r in reasons])
                                st.markdown(f"<div style='margin-bottom:6px;'>{reason_tags}</div>", unsafe_allow_html=True)

                            # Caption preview
                            caption_text = img_rec.get("caption", "")
                            if len(caption_text) > 115:
                                caption_text = caption_text[:115] + "..."
                            st.caption(caption_text)

                            # Tags
                            tags_html = " ".join([f"<span class='badge-tag'>#{t}</span>" for t in img_rec.get("tags", [])[:4]])
                            st.markdown(f"<div style='margin-bottom:8px;'>{tags_html}</div>", unsafe_allow_html=True)

                            btn_c1, btn_c2 = st.columns([3, 1])
                            with btn_c1:
                                if st.button("🎨 Open in Studio", key=f"edit_btn_{img_rec['id']}", use_container_width=True):
                                    st.session_state.selected_image_id = img_rec["id"]
                                    st.session_state.active_tab = NAV_TABS[1]
                                    st.rerun()
                            with btn_c2:
                                if st.button("🗑️", key=f"del_btn_{img_rec['id']}", help="Delete asset from library"):
                                    storage.delete_image(img_rec["id"])
                                    if st.session_state.selected_image_id == img_rec["id"]:
                                        st.session_state.selected_image_id = None
                                    st.rerun()


# ==============================================================================
# TAB 2: Studio & Edit Mode
# ==============================================================================
elif st.session_state.active_tab == NAV_TABS[1]:
    all_images = storage.get_all_images()

    if not all_images:
        st.warning("Your image library is empty. Please upload an image or click 'Reseed Sample Portfolio' in the sidebar.")
    else:
        # Image selector dropdown
        img_options = {img["id"]: f"{img['title']} (v{storage.get_active_version(img)['version_number']})" for img in all_images}
        default_index = 0
        if st.session_state.selected_image_id in img_options:
            default_index = list(img_options.keys()).index(st.session_state.selected_image_id)

        col_sel, col_quick_nav = st.columns([4, 2])
        with col_sel:
            selected_id = st.selectbox(
                "Select Asset to Edit",
                options=list(img_options.keys()),
                format_func=lambda x: img_options[x],
                index=default_index,
                label_visibility="collapsed"
            )
            st.session_state.selected_image_id = selected_id
            active_img_record = storage.get_image(selected_id)

        if active_img_record:
            active_version = storage.get_active_version(active_img_record)
            original_version = active_img_record["versions"][0]

            active_img_path = BASE_DIR / active_version["image_path"]
            orig_img_path = BASE_DIR / original_version["image_path"]

            with col_quick_nav:
                st.markdown(f"""
                <div style="display:flex; gap:8px; align-items:center; justify-content:flex-end; padding-top:6px;">
                  <span class="badge-version badge-active">Active: v{active_version['version_number']}</span>
                  <span class="badge-tag">{active_img_record['width']}×{active_img_record['height']}px</span>
                </div>
                """, unsafe_allow_html=True)

            # Two-column layout: Canvas Display (Left) + AI Edit Controls (Right)
            col_canvas, col_controls = st.columns([7, 5])

            with col_canvas:
                canvas_view_mode = st.radio(
                    "Canvas Display Mode",
                    ["✨ Active Version", "⚡ Side-by-Side (Original vs Active)"],
                    horizontal=True,
                    label_visibility="collapsed"
                )

                if canvas_view_mode == "✨ Active Version":
                    if active_img_path.exists():
                        st.image(
                            str(active_img_path),
                            use_container_width=True,
                            caption=f"Version v{active_version['version_number']} — {active_version.get('prompt', '')}"
                        )
                else:
                    col_before, col_after = st.columns(2)
                    with col_before:
                        st.markdown("<div style='text-align:center; font-weight:700; color:#94a3b8; font-size:0.82rem; margin-bottom:4px; letter-spacing:0.05em;'>ORIGINAL (v0)</div>", unsafe_allow_html=True)
                        if orig_img_path.exists():
                            st.image(str(orig_img_path), use_container_width=True)
                    with col_after:
                        st.markdown(f"<div style='text-align:center; font-weight:700; color:#818cf8; font-size:0.82rem; margin-bottom:4px; letter-spacing:0.05em;'>CURRENT (v{active_version['version_number']})</div>", unsafe_allow_html=True)
                        if active_img_path.exists():
                            st.image(str(active_img_path), use_container_width=True)

                # Metadata & AI Understanding Accordion
                with st.expander("👁️ AI Vision Understanding & Scene Inspector", expanded=False):
                    st.markdown(f"**Scene Caption:** {active_img_record.get('caption', 'N/A')}")

                    obj_c, col_c = st.columns(2)
                    with obj_c:
                        st.markdown("**Detected Objects:**")
                        objs = active_img_record.get("objects", [])
                        if objs:
                            st.markdown(" ".join([f"<span class='badge-tag'>{o}</span>" for o in objs]), unsafe_allow_html=True)
                        else:
                            st.caption("None recorded")

                    with col_c:
                        st.markdown("**Dominant Color Palette:**")
                        colors = active_img_record.get("dominant_colors", [])
                        if colors:
                            color_chips = ""
                            for c in colors:
                                dot_hex = get_color_hex(c)
                                color_chips += f"<span class='color-swatch-pill'><span class='color-dot' style='background:{dot_hex};'></span>{c}</span>"
                            st.markdown(f"<div>{color_chips}</div>", unsafe_allow_html=True)
                        else:
                            st.caption("None recorded")

                    if active_img_record.get("tags"):
                        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
                        st.markdown("**Semantic Keywords:**")
                        st.markdown(" ".join([f"<span class='badge-tag'>#{t}</span>" for t in active_img_record["tags"]]), unsafe_allow_html=True)

                # Download active version button
                if active_img_path.exists():
                    with open(active_img_path, "rb") as f_img:
                        st.download_button(
                            label=f"💾 Download Active Image (v{active_version['version_number']})",
                            data=f_img.read(),
                            file_name=f"{active_img_record['id']}_v{active_version['version_number']}.jpg",
                            mime="image/jpeg",
                            use_container_width=True
                        )

            with col_controls:
                st.markdown("### 🎛️ AI Edit Control Center")
                st.markdown(f"""
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; background:rgba(255,255,255,0.03); padding:8px 12px; border-radius:10px; border:1px solid var(--border-subtle);'>
                  <span style='font-size:0.8rem; color:#94a3b8;'>Active Provider:</span>
                  <span style='font-size:0.85rem; font-weight:700; color:#a5b4fc;'>{st.session_state.engine_mode.upper()}</span>
                </div>
                """, unsafe_allow_html=True)

                # SECTION 1: 1-Click Curated Presets
                st.markdown("#### 1. Instant 1-Click Presets")
                preset_keys = list(PRESET_EDITS.keys())

                p_col1, p_col2 = st.columns(2)
                for idx, p_key in enumerate(preset_keys):
                    p_info = PRESET_EDITS[p_key]
                    target_col = p_col1 if idx % 2 == 0 else p_col2
                    with target_col:
                        if st.button(
                            f"{p_info['icon']} {p_info['label']}",
                            key=f"preset_btn_{p_key}",
                            use_container_width=True,
                            help=p_info['description']
                        ):
                            with st.spinner(f"Applying preset '{p_info['label']}'..."):
                                with Image.open(active_img_path) as current_pil:
                                    edited_pil, eng_prompt, model_name = edit_engine.apply_preset(
                                        current_pil,
                                        p_key,
                                        engine_mode=st.session_state.engine_mode,
                                        openai_key=st.session_state.openai_api_key,
                                        gemini_key=st.session_state.gemini_api_key
                                    )
                                    storage.add_version(
                                        image_id=active_img_record["id"],
                                        edited_image=edited_pil,
                                        prompt=p_info["label"],
                                        edit_type="preset",
                                        model_used=model_name,
                                        notes=f"Preset {p_info['label']}: {eng_prompt[:80]}"
                                    )
                                    st.session_state.last_engineered_prompt = eng_prompt
                                    st.success(f"Generated new version with {p_info['label']}!")
                                    st.rerun()

                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                st.markdown("---")

                # SECTION 2: Custom Natural Language Instruction
                st.markdown("#### 2. Custom Natural Language Instruction")
                st.caption("Direct the model in plain conversational English. The prompt synthesizer will translate it into a preservation-aware specification.")

                if st.session_state.engine_mode == "local":
                    st.markdown("""
                    <div style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.25); border-radius:10px; padding:10px 14px; margin-bottom:12px; font-size:0.8rem; color:#cbd5e1; line-height:1.4;">
                      <strong style="color:#a5b4fc;">⚡ Smart Local Engine (Zero Cost Mode)</strong><br>
                      The local engine simulates visual styles, lighting, color grading, and skin/hair portrait retouches directly on your CPU. To <strong>physically inpaint or generate new objects</strong> (like generating trees, removing hair, or altering physical features), connect OpenAI DALL-E 3 or Google Gemini in the sidebar.
                    </div>
                    """, unsafe_allow_html=True)

                # Prompt suggestion chips
                st.markdown("<span style='font-size:0.75rem; color:#94a3b8; font-weight:600;'>INSPIRATION TEMPLATES:</span>", unsafe_allow_html=True)
                sug_c1, sug_c2 = st.columns(2)
                with sug_c1:
                    if st.button("✂️ 'remove background'", use_container_width=True):
                        st.session_state.custom_prompt_input = "remove the background and isolate subject on clean studio backdrop"
                    if st.button("💆 'retouch skin & hair'", use_container_width=True):
                        st.session_state.custom_prompt_input = "apply soft portrait retouching to hair and skin texture"
                with sug_c2:
                    if st.button("🌅 'sunset golden hour'", use_container_width=True):
                        st.session_state.custom_prompt_input = "change colors and lighting to warm cinematic sunset golden hour"
                    if st.button("🕶️ 'cyberpunk neon glow'", use_container_width=True):
                        st.session_state.custom_prompt_input = "apply cyberpunk neon lighting with electric cyan and magenta reflections"

                user_instruction = st.text_area(
                    "Edit Prompt",
                    value=st.session_state.get("custom_prompt_input", ""),
                    placeholder="e.g. 'remove the background', 'add dramatic storm clouds', 'make it look like vintage film'...",
                    height=90,
                    label_visibility="collapsed"
                )

                if st.button("✨ Synthesize & Execute Edit", type="primary", use_container_width=True):
                    if not user_instruction.strip():
                        st.error("Please enter a natural language instruction.")
                    else:
                        with st.spinner("Synthesizing prompt specification and rendering edit..."):
                            with Image.open(active_img_path) as current_pil:
                                edit_result = edit_engine.apply_custom_instruction(
                                    image=current_pil,
                                    instruction=user_instruction,
                                    image_caption=active_img_record.get("caption", ""),
                                    objects_list=active_img_record.get("objects", []),
                                    engine_mode=st.session_state.engine_mode,
                                    openai_key=st.session_state.openai_api_key,
                                    gemini_key=st.session_state.gemini_api_key
                                )

                                storage.add_version(
                                    image_id=active_img_record["id"],
                                    edited_image=edit_result["edited_image"],
                                    prompt=user_instruction,
                                    edit_type="custom_prompt",
                                    model_used=edit_result["model_used"],
                                    notes=f"Category: {edit_result['edit_category']}"
                                )
                                st.session_state.last_engineered_prompt = edit_result["engineered_prompt"]
                                st.success("Edit executed and cataloged as new version!")
                                st.rerun()

                # Prompt Engineering Live Preview Box
                if st.session_state.last_engineered_prompt:
                    with st.expander("⚡ Prompt Engineering Specification Inspector", expanded=True):
                        st.markdown(f"""
                        <div class="prompt-box">
                          <div class="prompt-box-header">
                            <span>Synthesized Output Spec</span>
                            <span style="color:#38bdf8;">Production Grade</span>
                          </div>
                          {st.session_state.last_engineered_prompt}
                        </div>
                        """, unsafe_allow_html=True)


# ==============================================================================
# TAB 3: Version History & Lineage
# ==============================================================================
elif st.session_state.active_tab == NAV_TABS[2]:
    all_images = storage.get_all_images()
    if not all_images:
        st.info("No images in library yet.")
    else:
        img_opts = {img["id"]: img["title"] for img in all_images}
        chosen_id = st.selectbox(
            "Select Image to View Version History",
            options=list(img_opts.keys()),
            format_func=lambda x: img_opts[x],
            index=list(img_opts.keys()).index(st.session_state.selected_image_id) if st.session_state.selected_image_id in img_opts else 0
        )
        img_record = storage.get_image(chosen_id)

        if img_record:
            st.markdown(f"### 📜 Version Lineage: *{img_record['title']}*")
            st.caption(f"Asset ID: `{img_record['id']}` • Total Revisions: **{len(img_record['versions'])}**")

            # Timeline Display
            for ver in reversed(img_record["versions"]):
                ver_id = ver["version_id"]
                is_active = (ver_id == img_record.get("current_version_id"))
                v_num = ver.get("version_number", 0)

                with st.container(border=True):
                    col_thumb, col_meta, col_actions = st.columns([2, 5, 2])

                    with col_thumb:
                        thumb_file = BASE_DIR / ver["thumbnail_path"]
                        if thumb_file.exists():
                            st.image(str(thumb_file), use_container_width=True)
                        else:
                            full_file = BASE_DIR / ver["image_path"]
                            if full_file.exists():
                                st.image(str(full_file), use_container_width=True)

                    with col_meta:
                        badge_status = "<span class='badge-version badge-active'>ACTIVE VERSION</span>" if is_active else "<span class='badge-version'>ARCHIVED REVISION</span>"
                        st.markdown(f"""
                        <div style="display:flex; align-items:center; gap:8px;">
                          <h4 style="margin:0; font-family:'Space Grotesk',sans-serif;">Version {v_num}</h4>
                          {badge_status}
                        </div>
                        <div style="font-size:0.85rem; color:#94a3b8; margin-top:6px; line-height:1.6;">
                          <strong>Timestamp:</strong> {ver.get('timestamp', 'N/A')}<br>
                          <strong>Edit Type:</strong> <span class='badge-tag'>{ver.get('edit_type', 'N/A')}</span><br>
                          <strong>Model / Engine:</strong> <span class='badge-tag'>{ver.get('model_used', 'N/A')}</span><br>
                          <div style="margin-top:4px;">
                            <strong>Instruction:</strong> <em>"{ver.get('prompt', 'N/A')}"</em>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_actions:
                        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
                        if not is_active:
                            if st.button("⏪ Revert to Version", key=f"revert_btn_{ver_id}", use_container_width=True):
                                storage.revert_to_version(img_record["id"], ver_id)
                                st.success(f"Reverted to Version {v_num}!")
                                st.rerun()

                        img_full_path = BASE_DIR / ver["image_path"]
                        if img_full_path.exists():
                            with open(img_full_path, "rb") as f_dl:
                                st.download_button(
                                    label="💾 Download File",
                                    data=f_dl.read(),
                                    file_name=f"{img_record['id']}_v{v_num}.jpg",
                                    mime="image/jpeg",
                                    key=f"dl_ver_{ver_id}",
                                    use_container_width=True
                                )


# ==============================================================================
# TAB 4: Prompt Engineering & API Architecture Documentation
# ==============================================================================
elif st.session_state.active_tab == NAV_TABS[3]:
    st.markdown("### 🧪 Prompt Engineering Architecture & Live Sandbox")

    st.markdown("""
    In generative editing, user prompts like **'remove background'** or **'make it sunset'** are inherently ambiguous.
    Directly dispatching shorthand phrases produces severe identity drift, hallucinations, or broken perspectives.

    Nova AI implements an **Autonomous Two-Stage Vision & Prompt Synthesis Pipeline**:
    """)

    st.markdown("""
    ```mermaid
    flowchart LR
        A[Original Image] --> B[Multimodal Vision: GPT-4o / Gemini]
        B --> C[Structured Scene Metadata: Subject, Pose, Lighting]
        D[User Casual Prompt] --> E[LLM Prompt Synthesizer]
        C --> E
        E --> F[Engineered Generation Specification]
        F --> G[Generative Engine: DALL-E 3 / Imagen / Local Neural]
        G --> H[New Cataloged Version Card]
    ```
    """)

    st.markdown("#### Live Prompt Synthesizer Sandbox")
    st.caption("Observe how raw natural language is synthesized into high-precision production prompts.")

    test_c1, test_c2 = st.columns(2)
    with test_c1:
        test_context = st.text_area(
            "Sample Image Context (Vision Scene Analysis)",
            value="A smiling young woman in an autumn park with soft golden hour backlighting, vibrant leaves, and creamy bokeh.",
            height=105
        )
    with test_c2:
        test_raw_instruction = st.text_input(
            "User Raw Instruction",
            value="add a retro bicycle leaning on a park bench in the background"
        )
        if st.button("⚡ Execute Prompt Synthesis Test", type="primary", use_container_width=True):
            with st.spinner("Synthesizing prompt specification..."):
                synth_result = synthesize_prompt_with_llm(
                    user_instruction=test_raw_instruction,
                    image_caption=test_context,
                    openai_key=st.session_state.openai_api_key,
                    gemini_key=st.session_state.gemini_api_key
                )
                st.session_state.synth_demo = synth_result

    if "synth_demo" in st.session_state:
        res = st.session_state.synth_demo
        st.markdown(f"""
        <div class="glass-card" style="margin-top:16px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <strong style="color:#a5b4fc; font-size:1.1rem; font-family:'Space Grotesk',sans-serif;">Synthesized Result</strong>
            <span class="badge-version">{res.get('edit_category', 'General')}</span>
          </div>
          <div style="font-size:0.86rem; color:#cbd5e1; margin-bottom:12px;">
            <strong>Change Summary:</strong> {res.get('summary_of_changes', 'N/A')}
          </div>
          <div class="prompt-box">
            <div class="prompt-box-header">Engineered Positive Generation Specification</div>
            {res.get('engineered_prompt', 'N/A')}
          </div>
          <div style="font-size:0.82rem; color:#fb7185; margin-top:8px;">
            <strong>Negative Constraints:</strong> {res.get('negative_prompt', 'None')}
          </div>
        </div>
        """, unsafe_allow_html=True)
