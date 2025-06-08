# sentinel_ai_app.py
import json  # For save/load state

import streamlit as st

import ai_analyzers as aia  # AI Analyzers
import rule_based_validators as rbv  # Rule Based Validators
# Import from your new modules
from kdp_data import (
    DEFAULT_SESSION_STATE, SUPPORTED_LANGUAGES,
    AI_TEXT_OPTIONS, AI_IMAGE_OPTIONS, AI_TRANSLATION_OPTIONS,
    TRIM_SIZE_OPTIONS_PAPERBACK, TRIM_SIZE_OPTIONS_HARDCOVER,
    INK_PAPER_OPTIONS_PAPERBACK, INK_PAPER_OPTIONS_HARDCOVER,
    BOOK_FORMAT_OPTIONS, YES_NO_OPTIONS, MANUSCRIPT_UPLOAD_FORMAT_OPTIONS,
    KDP_PAGE_COUNT_SPECS_PAPERBACK, KDP_PAGE_COUNT_SPECS_HARDCOVER,
    INK_PAPER_TO_KEY_MAP
)
from text_processing import extract_text_from_file, get_library_warnings

# --- Initialize Bedrock Client ---
# This is called once when the script is first run or rerun after changes.
if 'bedrock_client_initialized' not in st.session_state:
    st.session_state.bedrock_client_initialized, st.session_state.bedrock_client_message = aia.init_bedrock_client()

if not st.session_state.bedrock_client_initialized:
    st.error(st.session_state.bedrock_client_message) # Show prominent error if Bedrock fails

# --- Session State Initialization ---
def initialize_session_state_values():
    """Initializes or resets session state variables to their defaults."""
    for key, default_value in DEFAULT_SESSION_STATE.items():
        if key not in st.session_state: # Only initialize if not already present
            st.session_state[key] = default_value

initialize_session_state_values() # Call it once at the start

# --- UI Layout ---
st.set_page_config(page_title="Sentinel AI - KDP Validation Assistant", layout="wide", initial_sidebar_state="expanded")
st.title("📚 Sentinel AI")
st.caption("Your AI-powered KDP Pre-submission Validation Assistant. Helping you meet KDP guidelines *before* you publish.")

# Display warnings for missing optional libraries (from text_processing.py)
library_warnings = get_library_warnings()
for warning_msg in library_warnings:
    st.sidebar.warning(warning_msg)


# --- Helper function for UI consistency ---
def create_text_input(label, session_state_key, help_text="", max_chars=None, disabled=False, expander=None):
    container = expander if expander else st.sidebar
    st.session_state[session_state_key] = container.text_input(
        label,
        value=st.session_state[session_state_key],
        help=help_text,  # Corrected: st.text_input uses 'help'
        max_chars=max_chars,
        disabled=disabled,
        key=f"widget_{session_state_key}"
    )

def create_text_area(label, session_state_key, help_text="", height=100, disabled=False, expander=None):
    container = expander if expander else st.sidebar
    st.session_state[session_state_key] = container.text_area(
        label,
        value=st.session_state[session_state_key],
        help=help_text,  # Corrected: st.text_area uses 'help'
        height=height,
        disabled=disabled,
        key=f"widget_{session_state_key}"
    )

def create_checkbox(label, session_state_key, help_text="", disabled=False, expander=None):
    container = expander if expander else st.sidebar
    st.session_state[session_state_key] = container.checkbox(
        label,
        value=st.session_state[session_state_key],
        help=help_text,  # Corrected: st.checkbox uses 'help'
        disabled=disabled,
        key=f"widget_{session_state_key}"
    )

def create_selectbox(label, session_state_key, options, help_text="", disabled=False, expander=None):
    container = expander if expander else st.sidebar
    current_value = st.session_state[session_state_key]
    try:
        current_index = options.index(current_value)
    except ValueError:
        current_index = 0
        st.session_state[session_state_key] = options[0]

    st.session_state[session_state_key] = container.selectbox(
        label,
        options=options,
        index=current_index,
        help=help_text,  # Corrected: st.selectbox uses 'help'
        disabled=disabled,
        key=f"widget_{session_state_key}"
    )

def create_radio(label, session_state_key, options, help_text="", disabled=False, expander=None):
    container = expander if expander else st.sidebar
    current_value = st.session_state[session_state_key]
    try:
        current_index = options.index(current_value)
    except ValueError:
        current_index = 0
        st.session_state[session_state_key] = options[0]

    st.session_state[session_state_key] = container.radio(
        label,
        options=options,
        index=current_index,
        help=help_text,  # Corrected: st.radio uses 'help'
        disabled=disabled,
        key=f"widget_{session_state_key}",
        horizontal=True
    )

def create_number_input(label, session_state_key, min_val=0, max_val=100, step=1, help_text="", disabled=False, expander=None):
    container = expander if expander else st.sidebar
    st.session_state[session_state_key] = container.number_input(
        label,
        min_value=min_val,
        max_value=max_val,
        value=st.session_state[session_state_key],
        step=step,
        help=help_text,  # Corrected: st.number_input uses 'help'
        disabled=disabled,
        key=f"widget_{session_state_key}"
    )

# --- Sidebar for Global Actions & Manuscript Upload ---
with st.sidebar:
    st.header("Actions & Manuscript")
    uploaded_manuscript_file = st.file_uploader(
        "Upload Manuscript (Optional, for deeper AI analysis & auto-fill)",
        type=['txt', 'docx', 'pdf', 'epub', 'html', 'htm', 'xhtml'],
        key="widget_manuscript_file_uploader", # Use a distinct key for the widget
        help="Supports .txt, .docx, .pdf, .epub, .html files."
    )

    if uploaded_manuscript_file:
        if st.session_state.get('last_uploaded_filename') != uploaded_manuscript_file.name or \
           not st.session_state.extracted_manuscript_text:
            with st.spinner(f"Extracting text from {uploaded_manuscript_file.name}..."):
                extracted_text, extraction_msg = extract_text_from_file(uploaded_manuscript_file)
                st.session_state.extracted_manuscript_text = extracted_text
                st.session_state.last_uploaded_filename = uploaded_manuscript_file.name
            if extraction_msg:
                if "Error" in extraction_msg: st.error(extraction_msg)
                else: st.warning(extraction_msg)
            elif extracted_text:
                st.success(f"Extracted {len(extracted_text):,} characters.")
            else:
                st.warning("Could not extract text or file was empty.")
    elif st.session_state.last_uploaded_filename and not uploaded_manuscript_file: # File was removed by user
        st.session_state.extracted_manuscript_text = ""
        st.session_state.last_uploaded_filename = None
        st.info("Manuscript file removed.")

    if st.button("🤖 Auto-fill from Manuscript", key="autofill_button_sidebar", use_container_width=True,
                  disabled=(not st.session_state.extracted_manuscript_text or not st.session_state.bedrock_client_initialized)):
        if st.session_state.extracted_manuscript_text and st.session_state.bedrock_client_initialized:
            with st.spinner("🤖 AI is attempting to auto-fill details... This may take a moment."):
                autofill_suggestions, autofill_msg = aia.ai_extract_details_for_autofill(st.session_state.extracted_manuscript_text)

            if "Error" in autofill_msg: st.error(autofill_msg)
            elif "Warning" in autofill_msg or "ℹ️" in autofill_msg : st.warning(autofill_msg)
            else: st.success(autofill_msg)

            # Apply suggestions to session state
            if autofill_suggestions.get("title"): st.session_state.book_title_metadata = autofill_suggestions["title"]
            if autofill_suggestions.get("author"): st.session_state.author_name_metadata = autofill_suggestions["author"]
            if autofill_suggestions.get("language"):
                detected_lang_auto = autofill_suggestions["language"]
                matched_supported_lang = next((lang for lang in SUPPORTED_LANGUAGES if detected_lang_auto.lower() in lang.lower()), None)
                if matched_supported_lang: st.session_state.selected_language = matched_supported_lang
            if autofill_suggestions.get("description_draft"): st.session_state.description_text = autofill_suggestions["description_draft"]
            if autofill_suggestions.get("keywords"):
                current_kws = [""] * 7
                for i in range(min(len(autofill_suggestions["keywords"]), 7)): current_kws[i] = autofill_suggestions["keywords"][i]
                st.session_state.keywords_input_list = current_kws
            if autofill_suggestions.get("categories"):
                current_cats = ["", "", ""]
                for i in range(min(len(autofill_suggestions["categories"]), 3)): current_cats[i] = autofill_suggestions["categories"][i]
                st.session_state.categories_input_list = current_cats
            if autofill_suggestions.get("series_title"):
                st.session_state.series_name = autofill_suggestions["series_title"]
                if autofill_suggestions["series_title"]: st.session_state.is_series = True # Only set to true if a title was found
            if autofill_suggestions.get("series_number"): st.session_state.series_number = autofill_suggestions["series_number"]
            if autofill_suggestions.get("is_translation_hint"): st.session_state.is_translation = True
            if autofill_suggestions.get("original_author_hint"): st.session_state.original_author_translation = autofill_suggestions["original_author_hint"]
            if autofill_suggestions.get("translator_hint"): st.session_state.translator_name_translation = autofill_suggestions["translator_hint"]
            # No st.rerun() needed due to direct session state binding
        elif not st.session_state.bedrock_client_initialized:
            st.warning("Bedrock client not initialized. Cannot auto-fill.")
        else:
            st.warning("Upload a manuscript first to use the auto-fill feature.")

    st.markdown("---")
    validate_clicked = st.button("✨ Validate with Sentinel AI", key="validate_button_main", use_container_width=True, type="primary",
                                 disabled=not st.session_state.bedrock_client_initialized)
    if not st.session_state.bedrock_client_initialized:
        st.caption("Validation disabled: Bedrock client not initialized.")


    if st.button("🧹 Clear All Inputs & Results", key="clear_inputs_button_main", use_container_width=True):
        # Preserve Bedrock client status
        bedrock_status = st.session_state.bedrock_client_initialized
        bedrock_msg = st.session_state.bedrock_client_message
        initialize_session_state_values() # Re-initialize to defaults
        st.session_state.bedrock_client_initialized = bedrock_status
        st.session_state.bedrock_client_message = bedrock_msg
        st.toast("All inputs and results cleared!", icon="🧹")
        st.rerun()

    st.markdown("---")
    st.subheader("📋 Save/Load Session")
    if st.button("🔗 Generate Sharable Input Data", key="generate_json_button_sidebar", use_container_width=True):
        serializable_inputs = {}
        for key, value in st.session_state.items():
            if key not in ['validation_results_grouped', 'ai_analysis_feedbacks', 'error_count', 'warning_count',
                           'extracted_manuscript_text', 'last_uploaded_filename', 'bedrock_client_initialized', 'bedrock_client_message'] and \
               not key.startswith("widget_"): # Exclude internal/widget keys
                try:
                    json.dumps({key: value}) # Test serializability
                    serializable_inputs[key] = value
                except TypeError:
                    serializable_inputs[key] = f"UNSERIALIZABLE_OBJECT_TYPE_{type(value).__name__}" # Should not happen with DEFAULT_SESSION_STATE
        if serializable_inputs:
            st.session_state.json_inputs_to_share = json.dumps(serializable_inputs, indent=2, default=str)
            st.toast("Input data generated! You can copy it below.")
        else:
            st.toast("No inputs to generate data from.", icon="ℹ️")

    if st.session_state.json_inputs_to_share:
        st.text_area("Copy this data:", value=st.session_state.json_inputs_to_share, height=150, key="widget_json_display_area")

    st.session_state.json_load_area_text = st.text_area("Paste saved input data here to load:", value=st.session_state.json_load_area_text, height=100, key="widget_json_load_area")
    if st.button("📥 Load Inputs from Data", key="load_json_button_sidebar", use_container_width=True):
        if st.session_state.json_load_area_text:
            try:
                loaded_inputs = json.loads(st.session_state.json_load_area_text)
                # Preserve Bedrock client status
                bedrock_status = st.session_state.bedrock_client_initialized
                bedrock_msg = st.session_state.bedrock_client_message
                # Initialize first to ensure all keys exist, then update
                initialize_session_state_values()
                st.session_state.bedrock_client_initialized = bedrock_status
                st.session_state.bedrock_client_message = bedrock_msg

                for key, value in loaded_inputs.items():
                    if key in st.session_state: # Only load keys that are part of our defined state
                        st.session_state[key] = value
                st.success("Inputs loaded successfully! Please re-upload any manuscript files if they were part of the saved state.")
                st.session_state.json_inputs_to_share = "" # Clear generated one if any
                st.session_state.json_load_area_text = "" # Clear paste area
                st.rerun()
            except json.JSONDecodeError:
                st.error("Invalid data format. Please ensure it's valid JSON copied from 'Generate Sharable Input Data'.")
            except Exception as e:
                st.error(f"Error loading inputs: {e}")
        else:
            st.warning("Paste data into the area above before attempting to load.")

    st.markdown("---")
    st.subheader("About Sentinel AI")
    st.info(
        "Sentinel AI helps KDP authors validate book details against KDP guidelines *before* submission. "
        "It aims to improve productivity, reduce rejections, and enhance content quality. "
        "This tool uses Amazon Bedrock (Claude Sonnet) for AI-powered analysis. "
        "Developed for the Amazon Internal Hackathon."
    )
    st.markdown("---")
    st.caption(f"Bedrock Client Status: {st.session_state.bedrock_client_message if 'bedrock_client_message' in st.session_state else 'Initializing...'}")


# --- Main Area with Tabs for Inputs ---
tab_titles = [
    "📘 Core Book & Author",
    "📝 Description & Discoverability",
    "🎯 Audience & Special Types",
    "🤖 AI Content Declaration",
    "🖨️ Print Book Setup (if applicable)"
]
tab_core, tab_marketing, tab_audience, tab_ai, tab_print = st.tabs(tab_titles)

with tab_core:
    st.header("Core Book & Author Information")
    sub_col1, sub_col2 = st.columns(2)
    with sub_col1:
        create_selectbox("Intended Book Format:", "book_format", BOOK_FORMAT_OPTIONS, help_text="Select the primary format you are preparing for KDP.")
        create_text_input("Book Title (as in KDP metadata):", "book_title_metadata", "Max 200 chars. Must match cover exactly. Guideline 2, 7.", max_chars=200)
    with sub_col2:
        create_selectbox("Book Language (Content & Metadata):", "selected_language", SUPPORTED_LANGUAGES, help_text="Primary language of your book. Guideline 11.")
        create_text_input("Subtitle (Metadata, Optional):", "subtitle_metadata", "Max 200 chars (Title + Subtitle). Guideline 2, 7.", max_chars=200)

    create_text_input("Primary Author Name (as in KDP metadata):", "author_name_metadata", "Cannot be changed after publishing. Guideline 7.")

    st.subheader("Cover Text (Exactly as on Artwork)")
    help_cover_text = "Ensure this matches your KDP metadata title/author exactly. Guideline 2, 4, 12."
    create_text_input("Exact Title on Cover Artwork:", "title_on_cover", help_cover_text)
    create_text_input("Exact Author Name on Cover Artwork:", "author_on_cover", help_cover_text)


with tab_marketing:
    st.header("Description & Discoverability")
    create_text_area("Book Description (Max 4000 chars):", "description_text", "Plain text or KDP-supported HTML. Guideline 8, 10.", height=250)

    st.subheader("🏷️ Categories (Up to 3)")
    st.caption("Choose categories that accurately reflect your book's content. Guideline 2.")
    cols_cat = st.columns(3)
    for i in range(3):
        with cols_cat[i]:
            st.session_state.categories_input_list[i] = st.text_input(
                f"Category {i+1}",
                value=st.session_state.categories_input_list[i], # Use value parameter
                key=f"widget_cat_{i}",
                help="e.g., Fiction > Fantasy > Epic" # Corrected parameter
            )

    st.subheader("🔍 Keywords (Up to 7)")
    st.caption("Use relevant phrases customers might search for. Avoid prohibited terms. Guideline 9, 10.")
    cols_kw = st.columns(4)
    for i in range(7):
        container = cols_kw[i % 4]
        with container:
            st.session_state.keywords_input_list[i] = st.text_input(
                f"Keyword {i+1}",
                value=st.session_state.keywords_input_list[i], # Use value parameter
                key=f"widget_kw_{i}",
                help="Max ~50 chars per keyword field." # Corrected parameter
            )

with tab_audience:
    st.header("Audience & Special Book Types")
    st.subheader("Primary Audience")
    create_radio("Book contains sexually explicit images or title?", "sexually_explicit", YES_NO_OPTIONS, "Guideline 2, 11. If Yes, ineligible for Children's categories.")

    st.caption("Reading Age (Optional, but recommended for Children's/YA books. Guideline 11.)")
    age_col1, age_col2 = st.columns(2)
    with age_col1:
        create_number_input("Minimum Reading Age (0 for Not Set):", "min_reading_age", 0, 100, 1, "Enter 0 if you do not want to set a minimum age.")
    with age_col2:
        create_number_input("Maximum Reading Age (0 for Not Set, up to 18+):", "max_reading_age", 0, 100, 1, "Enter 0 if you do not want to set a maximum age. Min age cannot be > Max age (unless Max is 0).")

    st.subheader("Special Book Types")
    create_checkbox("This book is in the Public Domain", "is_public_domain", "Guideline 1, 3. If yes, differentiation is required.")
    if st.session_state.is_public_domain:
        create_text_area("How is your Public Domain version differentiated?", "public_domain_differentiation_statement", "Explain unique value: e.g., new annotations, original translation, unique illustrations, scholarly introduction. Guideline 1.", height=100)

    create_checkbox("Is this book a translation?", "is_translation", "Guideline 1.")
    if st.session_state.is_translation:
        create_text_input("Original Author (if translation):", "original_author_translation", "Required if book is a translation. Guideline 1.")
        create_text_input("Translator Name (if translation):", "translator_name_translation", "Required. Use 'Anonymous' if unknown for an older work. Guideline 1.")

    create_checkbox("This is a Low-Content Book", "is_low_content", "e.g., journal, notebook, planner. Guideline 6.")
    create_text_input("ISBN (International Standard Book Number):", "isbn", "Optional for eBooks & Low-Content. Required for other print. Guideline 6, 7, 11.")


with tab_ai:
    st.header("🤖 AI Content Declaration")
    st.caption("Disclose use of AI-based tools for creating text, images, or translations, as per KDP Guideline 1.")
    create_radio("Did you use AI-based tools to *create* ANY content (text, images, or translations)?",
                 "ai_used_any", YES_NO_OPTIONS,
                 help_text="If AI only *assisted* with your own created content (e.g., editing, brainstorming), KDP generally considers that 'AI-assisted' and not requiring disclosure of 'AI-generated' content. Review KDP's definitions carefully.")

    if st.session_state.ai_used_any == "Yes":
        st.markdown("If AI tools *created* the actual content (even if you edited it substantially), please specify below:")
        create_selectbox("AI-Generated Text Details:", "ai_text_detail", AI_TEXT_OPTIONS)
        create_selectbox("AI-Generated Images Details:", "ai_images_detail", AI_IMAGE_OPTIONS)
        create_selectbox("AI-Generated Translations Details:", "ai_translation_detail", AI_TRANSLATION_OPTIONS)
    else: # Ensure details are reset to "None" if main question is "No"
        st.session_state.ai_text_detail = AI_TEXT_OPTIONS[0]
        st.session_state.ai_images_detail = AI_IMAGE_OPTIONS[0]
        st.session_state.ai_translation_detail = AI_TRANSLATION_OPTIONS[0]
        st.info("If AI was only used for assistance (editing, brainstorming, refining *your own* created content), and did not *generate* the content itself, you generally do not need to declare it as 'AI-Generated' to KDP. Always refer to the latest KDP guidelines.")

with tab_print:
    st.header("🖨️ Print Book Setup Details")
    is_print_format_selected = st.session_state.book_format in ["Paperback", "Hardcover"]
    if not is_print_format_selected:
        st.info("These options are for Paperback or Hardcover books. Please select one of those formats in the 'Core Book & Author' tab to enable these fields.")

    current_trim_options = TRIM_SIZE_OPTIONS_HARDCOVER if st.session_state.book_format == "Hardcover" else TRIM_SIZE_OPTIONS_PAPERBACK
    create_selectbox("Trim Size:", "trim_size", current_trim_options, "Physical dimensions of your printed book. Guideline 13.", disabled=not is_print_format_selected)

    current_ink_options = INK_PAPER_OPTIONS_HARDCOVER if st.session_state.book_format == "Hardcover" else INK_PAPER_OPTIONS_PAPERBACK
    create_selectbox("Ink & Paper Type:", "ink_paper_type", current_ink_options, "Guideline 13.", disabled=not is_print_format_selected)

    create_text_input("Final Page Count (approximate):", "page_count", "Number of pages in your final print-ready file. Guideline 13.", disabled=not is_print_format_selected)
    create_radio("Interior Pages Have Bleed?", "interior_bleed", YES_NO_OPTIONS, "Do images/colors extend to the very edge of the page? Guideline 13.", disabled=not is_print_format_selected)
    st.caption("Manuscript Upload Format for KDP (relevant for PDF language restrictions):")
    create_selectbox("Intended Manuscript Upload Format for KDP:", "manuscript_upload_format_for_kdp", MANUSCRIPT_UPLOAD_FORMAT_OPTIONS, help_text="What file type do you plan to upload to KDP for this print book? Guideline 11.", disabled=not is_print_format_selected)


# --- Validation Logic Trigger ---
if validate_clicked and st.session_state.bedrock_client_initialized:
    # Re-initialize results containers
    st.session_state.validation_results_grouped = {
        "📘 Core Book & Author": [], "📝 Description & Discoverability": [],
        "🎯 Audience & Special Types": [], "🤖 AI Content Declaration": [],
        "🖨️ Print Book Setup": [], "📖 Manuscript Content (General Rules)": []
    }
    st.session_state.ai_analysis_feedbacks = {
        "🔍 Content & Description AI Analysis": [], # For description quality, keywords, categories AI
        "✍️ Manuscript Quality AI Analysis": [],   # For typos, placeholders, links, duplications, general quality
        "📜 Specialized Content AI Analysis": []  # For PD differentiation, Infringing, Freely Available, Offensive, Language consistency
    }
    st.session_state.error_count = 0
    st.session_state.warning_count = 0

    s = st.session_state # For brevity

    # --- RULE-BASED VALIDATIONS ---
    with st.spinner("Performing rule-based validations..."):
        # Core Book & Author
        s.validation_results_grouped["📘 Core Book & Author"].extend(rbv.validate_title_and_subtitle(s.book_title_metadata, s.subtitle_metadata))
        s.validation_results_grouped["📘 Core Book & Author"].extend(rbv.validate_author_name(s.author_name_metadata))
        s.validation_results_grouped["📘 Core Book & Author"].extend(rbv.validate_cover_text_match(s.title_on_cover, s.author_on_cover, s.book_title_metadata, s.author_name_metadata))
        s.validation_results_grouped["📘 Core Book & Author"].extend(rbv.validate_language_and_format(s.selected_language, s.book_format, s.manuscript_upload_format_for_kdp if s.book_format != "eBook" else "Other"))


        # Description & Discoverability
        s.validation_results_grouped["📝 Description & Discoverability"].extend(rbv.validate_description_html(s.description_text))
        s.validation_results_grouped["📝 Description & Discoverability"].extend(rbv.validate_categories(s.categories_input_list))
        s.validation_results_grouped["📝 Description & Discoverability"].extend(rbv.validate_keywords(s.keywords_input_list, s.book_title_metadata, s.subtitle_metadata, s.categories_input_list))
        s.validation_results_grouped["📝 Description & Discoverability"].extend(rbv.validate_series_info(s.is_series, s.series_name, s.series_number, s.is_low_content, s.is_public_domain))

        # Audience & Special Types
        s.validation_results_grouped["🎯 Audience & Special Types"].extend(rbv.validate_primary_audience(s.sexually_explicit, s.min_reading_age, s.max_reading_age, s.categories_input_list))
        s.validation_results_grouped["🎯 Audience & Special Types"].extend(rbv.validate_isbn(s.isbn, s.is_low_content, s.book_format))
        s.validation_results_grouped["🎯 Audience & Special Types"].extend(rbv.validate_low_content_implications(s.is_low_content))
        s.validation_results_grouped["🎯 Audience & Special Types"].extend(rbv.validate_translation_info(s.is_translation, s.original_author_translation, s.translator_name_translation))
        s.validation_results_grouped["🎯 Audience & Special Types"].extend(rbv.validate_public_domain_differentiation(s.is_public_domain, s.public_domain_differentiation_statement, s.description_text))

        # AI Content Declaration
        s.validation_results_grouped["🤖 AI Content Declaration"].extend(rbv.validate_ai_content_declaration(s.ai_used_any, s.ai_text_detail, s.ai_images_detail, s.ai_translation_detail))

        # Print Book Setup
        if s.book_format in ["Paperback", "Hardcover"]:
            if s.trim_size != "Select Trim Size" and s.page_count and s.ink_paper_type != "Select Ink/Paper":
                s.validation_results_grouped["🖨️ Print Book Setup"].extend(
                    rbv.validate_print_specs(
                        s.trim_size, s.page_count, s.interior_bleed, s.ink_paper_type, s.book_format,
                        KDP_PAGE_COUNT_SPECS_PAPERBACK, KDP_PAGE_COUNT_SPECS_HARDCOVER, INK_PAPER_TO_KEY_MAP
                    )
                )
            else:
                s.validation_results_grouped["🖨️ Print Book Setup"].append("⚠️ Provide Trim Size, Page Count, & Ink/Paper Type for full print formatting guidance.")
    st.success("Rule-based validations complete.")

    # --- AI-POWERED ANALYSES ---
    man_text = s.extracted_manuscript_text
    ai_tasks_to_run_map = {
        ("Description Quality", "🔍 Content & Description AI Analysis"): (lambda: aia.ai_check_description_quality(s.description_text), bool(s.description_text)),
        ("Keyword Suggestions", "🔍 Content & Description AI Analysis"): (lambda: aia.ai_suggest_keywords(s.book_title_metadata, s.description_text, "; ".join(k for k in s.keywords_input_list if k.strip())), bool(s.book_title_metadata or s.description_text)),
        ("Category Suggestions", "🔍 Content & Description AI Analysis"): (lambda: aia.ai_suggest_categories(s.book_title_metadata, s.description_text, "; ".join(c for c in s.categories_input_list if c.strip())), bool(s.book_title_metadata or s.description_text)),

        ("Manuscript Snippet Quality (Typos, Placeholders, Links, Duplicates, etc.)", "✍️ Manuscript Quality AI Analysis"): (lambda: aia.ai_check_manuscript_quality_snippets(man_text), bool(man_text and len(man_text) >= 200)),

        ("Offensive Content Scan (Manuscript Snippet)", "📜 Specialized Content AI Analysis"): (lambda: aia.ai_check_offensive_content(man_text), bool(man_text and len(man_text) >= 50)),
        ("Freely Available & Infringing Content (Title & Manuscript Snippet)", "📜 Specialized Content AI Analysis"): (lambda: aia.ai_check_freely_available_and_infringing_content(s.book_title_metadata, man_text), bool(man_text and len(man_text) >= 300)),
        ("Public Domain Differentiation Statement AI Review", "📜 Specialized Content AI Analysis"): (lambda: aia.ai_check_public_domain_differentiation_statement(s.is_public_domain, s.public_domain_differentiation_statement), bool(s.is_public_domain and s.public_domain_differentiation_statement.strip())),
        ("Manuscript Language Consistency", "📜 Specialized Content AI Analysis"): (lambda: aia.ai_check_language_consistency(s.selected_language, man_text), bool(man_text and len(man_text) >= 100 and s.selected_language)),
    }

    active_ai_tasks = {task_key_tuple: task_details for task_key_tuple, task_details in ai_tasks_to_run_map.items() if task_details[1]}

    if active_ai_tasks:
        total_ai_tasks_to_run = len(active_ai_tasks)
        completed_ai_tasks = 0
        progress_bar_placeholder = st.empty()
        progress_bar = progress_bar_placeholder.progress(0)

        with st.spinner(f"Performing {total_ai_tasks_to_run} AI analyses... This may take several minutes."):
            for (task_name, result_category), (task_func, _) in active_ai_tasks.items():
                st.caption(f"🧠 Running AI Analysis: {task_name}...")
                feedback_list = task_func() # Should return a list of strings
                if feedback_list:
                    s.ai_analysis_feedbacks[result_category].extend(feedback_list)
                completed_ai_tasks += 1
                progress_bar.progress(completed_ai_tasks / total_ai_tasks_to_run)
            progress_bar_placeholder.empty()
        st.success("AI analyses complete!")
    else:
        st.info("No AI analyses were triggered based on current inputs or lack of manuscript text.")


    # --- CALCULATE FINAL ERROR/WARNING COUNTS & DISPLAY RESULTS ---
    # Rule-based counts
    for section_key, messages in s.validation_results_grouped.items():
        if not messages: s.validation_results_grouped[section_key] = ["✅ All rule-based checks in this section passed or no specific issues noted."]
        for msg in messages:
            if isinstance(msg, str):
                if "❌" in msg: s.error_count += 1
                elif "⚠️" in msg: s.warning_count += 1

    # AI feedback heuristic counts (can be refined)
    for section_key, messages in s.ai_analysis_feedbacks.items():
        if not messages: s.ai_analysis_feedbacks[section_key] = ["ℹ️ No specific AI feedback generated for this section based on inputs, or AI check was not applicable."]
        for msg in messages:
            if isinstance(msg, str):
                # Simple heuristic for AI feedback indicating potential problems
                if "potential issue" in msg.lower() or "recommend review" in msg.lower() or "mismatch" in msg.lower() or "problematic" in msg.lower() or "unsupported" in msg.lower() or "unintentional duplication" in msg.lower() or "poorly translated" in msg.lower() or "not allowed" in msg.lower() or "unclear" in msg.lower():
                    if "no potential issue" not in msg.lower() and "no obvious" not in msg.lower() and "not immediately raise" not in msg.lower(): # Avoid false positives from "no issues found" type messages
                        s.warning_count += 1 # Treat most actionable AI feedback as warnings

    # --- Display Results Area ---
    st.markdown("---")
    st.header("📊 Validation Report")

    # Submission Readiness Indicator
    if s.error_count > 0 :
        st.error(f"🔴 **High Risk of Rejection/Issues:** {s.error_count} critical error(s) ❌ found. These MUST be addressed.")
    elif s.warning_count > 5 :
        st.warning(f"🟠 **Moderate Risk/Review Needed:** {s.warning_count} warnings ⚠️ found. Review all feedback carefully.")
    elif s.warning_count > 0:
        st.warning(f"🟡 **Low Risk/Review Recommended:** {s.warning_count} warning(s) ⚠️ found. Please review.")
    else: # No errors and few/no warnings
        st.success("🟢 **Looking Good!** No critical errors ❌ from automated rules. Please carefully review any AI feedback and informational notes ℹ️.")
    st.caption("This is a heuristic indicator. *Always review all feedback sections below before submitting to KDP.*")

    st.markdown("---")
    st.markdown(
        "💡 **Amazon Q Business Integration Idea:** Sentinel AI's findings and the underlying KDP guidelines could power an internal Amazon Q Business application. This would allow support teams to quickly query specific KDP policies, understand common publisher issues flagged by Sentinel AI, and get AI-assisted guidance on resolving complex cases, boosting operational efficiency across publishing support."
    )
    st.markdown("---")

    # Display Rule-Based Validation Results
    st.subheader("📋 Rule-Based Validation Checks")
    for section, messages in s.validation_results_grouped.items():
        # Only show expander if there are non-OK messages or if it's print details for a print book
        show_expander = any("❌" in str(m) or "⚠️" in str(m) for m in messages if isinstance(m, str)) or \
                        (section == "🖨️ Print Book Setup" and s.book_format in ["Paperback", "Hardcover"])

        with st.expander(f"{section} ({sum(1 for m in messages if '❌' in str(m) or '⚠️' in str(m))} issues)", expanded=show_expander):
            for msg_content in messages:
                if isinstance(msg_content, str):
                    if "❌" in msg_content: st.error(msg_content)
                    elif "⚠️" in msg_content: st.warning(msg_content)
                    elif "✅" in msg_content: st.success(msg_content)
                    else: st.info(msg_content) # Mostly for ℹ️
                else: st.write(msg_content) # Should not happen if all validators return strings

    # Display AI-Powered Analysis
    st.subheader("🤖 AI-Powered Deep Analysis")
    has_substantive_ai_feedback_overall = any(
        any(isinstance(m, str) and m.strip() and not m.startswith("ℹ️") and not m.startswith("✅") for m in msg_list)
        for msg_list in s.ai_analysis_feedbacks.values() if msg_list
    )
    with st.expander("View AI Analysis Details", expanded=has_substantive_ai_feedback_overall or s.error_count > 0 or s.warning_count > 0):
        for ai_section_title, ai_messages_list in s.ai_analysis_feedbacks.items():
            # Filter out purely informational messages if there's more substantive feedback in the section
            substantive_messages_in_section = [m for m in ai_messages_list if isinstance(m, str) and m.strip() and not m.startswith("ℹ️") and not m.startswith("✅")]
            if substantive_messages_in_section:
                st.markdown(f"##### {ai_section_title.replace('AI Analysis', '').strip()}")
                for ai_msg_idx, ai_msg_content in enumerate(substantive_messages_in_section):
                    if isinstance(ai_msg_content, str) and ai_msg_content.strip():
                        # Using markdown for better formatting of AI's structured output
                        st.markdown(ai_msg_content)
                        if ai_msg_idx < len(substantive_messages_in_section) - 1: st.markdown("---") # Separator
            elif ai_messages_list: # Show info messages if that's all there is for the section
                 st.markdown(f"##### {ai_section_title.replace('AI Analysis', '').strip()}")
                 for info_msg in ai_messages_list: st.info(info_msg)

    if s.error_count == 0 and s.warning_count == 0 and not has_substantive_ai_feedback_overall:
        st.balloons()
        st.success(
            "🎉 Excellent! All rule-based checks passed and AI analysis did not flag major concerns. "
            "Please give a final manual review of all inputs and KDP guidelines before submitting."
        )
    elif s.error_count == 0 and s.warning_count == 0 and has_substantive_ai_feedback_overall:
        st.success(
            "✅ Rule-based checks passed! Please carefully review the detailed AI analysis sections for further insights, "
            "potential improvements, and any advisories before submitting to KDP."
        )

elif validate_clicked and not st.session_state.bedrock_client_initialized:
    st.error("🔴 Validation Aborted: Bedrock client is not initialized. Please check AWS setup and permissions in the console, then refresh the app.")