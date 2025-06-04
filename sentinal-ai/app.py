# sentinel_ai_app.py
import streamlit as st
import boto3
import json
import re
from io import StringIO, BytesIO
import docx  # pip install python-docx
import random

# Attempt to import optional libraries and set them to None if not found
try:
    import PyPDF2
except ImportError:
    st.sidebar.warning("PyPDF2 library not found. PDF processing will be unavailable. Install with: pip install PyPDF2")
    PyPDF2 = None

try:
    from ebooklib import epub
    import ebooklib  # For ebooklib.ITEM_DOCUMENT
except ImportError:
    st.sidebar.warning(
        "EbookLib library not found. EPUB processing will be unavailable. Install with: pip install EbookLib")
    epub = None
    ebooklib = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    st.sidebar.warning(
        "BeautifulSoup4 library not found. EPUB/HTML processing will be impacted. Install with: pip install beautifulsoup4")
    BeautifulSoup = None

# --- Bedrock Client Initialization ---
BEDROCK_REGION = "us-east-1"
bedrock_runtime_client = None
try:
    bedrock_runtime_client = boto3.client(
        service_name="bedrock-runtime",
        region_name=BEDROCK_REGION
    )
except Exception as e:
    st.error(f"CRITICAL ERROR: Could not initialize Bedrock client in region '{BEDROCK_REGION}': {e}. "
             f"Please ensure your AWS credentials and Bedrock model access are correctly configured for this region.")
    # No st.stop() here, allow the app to load and show the error. invoke_claude_model will handle client being None.


# --- Helper Function to Invoke Claude ---
def invoke_claude_model(prompt, model_id="anthropic.claude-3-sonnet-20240229-v1:0", max_tokens=2500):
    if not bedrock_runtime_client:
        return "Error: Bedrock client not available. Cannot perform AI analysis."
    if not isinstance(prompt, str):
        return "Error: Invalid prompt type provided to AI model."

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    })
    try:
        response = bedrock_runtime_client.invoke_model(
            body=body, modelId=model_id, accept="application/json", contentType="application/json"
        )
        response_body = json.loads(response.get("body").read())
        content_list = response_body.get("content")
        if isinstance(content_list, list) and content_list and "text" in content_list[0]:
            return content_list[0].get("text")
        else:
            return f"Informational: AI model returned no specific feedback or an unexpected response structure for this check."
    except Exception as e:
        return f"Error: Could not get a response from the AI model for this check due to an error: {str(e)[:100]}..."


# --- Text Extraction Function ---
def extract_text_from_file(uploaded_file):
    if uploaded_file is None: return ""
    file_name = uploaded_file.name.lower()
    text_content = ""
    try:
        if file_name.endswith(".txt"):
            try:
                text_content = StringIO(uploaded_file.getvalue().decode("utf-8")).read()
            except UnicodeDecodeError:
                text_content = StringIO(uploaded_file.getvalue().decode("latin-1")).read()
        elif file_name.endswith(".docx"):
            if docx:
                doc = docx.Document(BytesIO(uploaded_file.getvalue())); text_content = '\n'.join(
                    [para.text for para in doc.paragraphs])
            else:
                return "Error: python-docx library not available. Cannot process .docx files."
        elif file_name.endswith(".pdf"):
            if PyPDF2:
                pdf_reader = PyPDF2.PdfReader(BytesIO(uploaded_file.getvalue()))
                if not pdf_reader.pages: return "Warning: PDF file appears to be empty or unreadable."
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text: text_content += page_text + "\n"
            else:
                return "Error: PyPDF2 library not available. Cannot process .pdf files."
        elif file_name.endswith(".epub"):
            if epub and BeautifulSoup and ebooklib:
                book = epub.read_epub(BytesIO(uploaded_file.getvalue()))
                for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    for script_or_style in soup(["script", "style"]): script_or_style.decompose()
                    text_content += soup.get_text(separator='\n', strip=True) + "\n\n"
            else:
                return "Error: EbookLib or BeautifulSoup4 not available. Cannot process .epub files."
        elif file_name.endswith((".html", ".htm", ".xhtml")):
            if BeautifulSoup:
                soup = BeautifulSoup(uploaded_file.getvalue(), 'html.parser')
                for script_or_style in soup(["script", "style"]): script_or_style.decompose()
                text_content = soup.get_text(separator='\n', strip=True)
            else:
                return "Error: BeautifulSoup4 not available. Cannot process HTML files."
        else:
            return f"Warning: Unsupported file type for text extraction: {uploaded_file.name}. Please upload .txt, .docx, .pdf, .epub, or .html."
    except Exception as e:
        return f"Error processing file '{uploaded_file.name}': {str(e)[:100]}..."
    return text_content.strip()


# --- KDP Print Specifications Data (Guideline 13) ---
KDP_PAGE_COUNT_SPECS = {
    "5\" x 8\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600),
                  "prem_color_white": (24, 828)},
    "5.06\" x 7.81\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600),
                        "prem_color_white": (24, 828)},
    "5.25\" x 8\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600),
                     "prem_color_white": (24, 828)},
    "5.5\" x 8.5\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600),
                      "prem_color_white": (24, 828), "hc_bw_white": (75, 550), "hc_bw_cream": (75, 550),
                      "hc_prem_color_white": (75, 550)},
    "6\" x 9\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600),
                  "prem_color_white": (24, 828), "hc_bw_white": (75, 550), "hc_bw_cream": (75, 550),
                  "hc_prem_color_white": (75, 550)},
    "6.14\" x 9.21\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600),
                        "prem_color_white": (24, 828), "hc_bw_white": (75, 550), "hc_bw_cream": (75, 550),
                        "hc_prem_color_white": (75, 550)},
    "6.69\" x 9.61\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600),
                        "prem_color_white": (24, 828)},
    "7\" x 10\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600),
                   "prem_color_white": (24, 828), "hc_bw_white": (75, 550), "hc_bw_cream": (75, 550),
                   "hc_prem_color_white": (75, 550)},
    "7.44\" x 9.69\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600),
                        "prem_color_white": (24, 828)},
    "7.5\" x 9.25\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600),
                       "prem_color_white": (24, 828)},
    "8\" x 10\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600),
                   "prem_color_white": (24, 828)},
    "8.25\" x 6\"": {"bw_white": (24, 800), "bw_cream": (24, 750), "std_color_white": (72, 600),
                     "prem_color_white": (24, 800)},
    "8.25\" x 8.25\"": {"bw_white": (24, 800), "bw_cream": (24, 750), "std_color_white": (72, 600),
                        "prem_color_white": (24, 800)},
    "8.5\" x 8.5\"": {"bw_white": (24, 590), "bw_cream": (24, 550), "std_color_white": (72, 600),
                      "prem_color_white": (24, 590)},
    "8.5\" x 11\"": {"bw_white": (24, 590), "bw_cream": (24, 550), "std_color_white": (72, 600),
                     "prem_color_white": (24, 590), "hc_bw_white": (75, 550), "hc_bw_cream": (75, 550),
                     "hc_prem_color_white": (75, 550)},
    "8.27\" x 11.69\" (A4)": {"bw_white": (24, 780), "bw_cream": (24, 730), "prem_color_white": (24, 590)},
}
INK_PAPER_TO_KEY_MAP = {
    "Black & white interior with cream paper": "bw_cream",
    "Black & white interior with white paper": "bw_white",
    "Standard color interior with white paper": "std_color_white",
    "Premium color interior with white paper": "prem_color_white"
}


# --- Validation Functions (Rule-Based) ---
def validate_title_and_subtitle(book_title, subtitle, field_name="Title/Subtitle"):
    validation_results = []
    base_field_name = field_name.split("/")[0]
    if not book_title:
        validation_results.append(f"❌ **{base_field_name}:** {base_field_name} is missing. [Guideline 2, 7]")
    else:
        if field_name == "Title/Subtitle" and len(book_title) + len(subtitle) > 200:
            validation_results.append(
                f"❌ **{field_name} Length:** Combined length ({len(book_title) + len(subtitle)}) exceeds 200 chars. [Guideline 2, 7]")
        prohibited_keywords = ["free", "bestselling", "best seller", "best book", "sale", "discount", "notebook",
                               "journal", "gifts", "books"]
        title_text_combined = book_title.lower() + (" " + subtitle.lower() if subtitle else "")
        for keyword in prohibited_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', title_text_combined):
                if keyword in ["notebook", "journal", "gifts", "books"] and title_text_combined.count(
                    keyword) == 1 and len(title_text_combined.split()) > 2: continue
                validation_results.append(
                    f"⚠️ **{field_name} Content:** Contains potentially problematic term '{keyword}'. Review Guideline 2 & 7 for appropriate usage.")
        if re.search(r'<[^>]+>', book_title) or (subtitle and re.search(r'<[^>]+>', subtitle)):
            validation_results.append(f"❌ **{field_name} Content:** Contains HTML tags. Not allowed. [Guideline 2, 7]")
        if re.fullmatch(r'[^\w\s]+', book_title) or (subtitle and re.fullmatch(r'[^\w\s]+', subtitle)):
            validation_results.append(f"❌ **{field_name} Content:** Consists only of punctuation. [Guideline 2, 7]")
        placeholders = ["unknown", "n/a", "na", "blank", "none", "null", "not applicable", "untitled"]
        if book_title.lower() in placeholders or (subtitle and subtitle.lower() in placeholders):
            validation_results.append(
                f"❌ **{field_name} Content:** Uses placeholder text (e.g., 'unknown', 'untitled'). [Guideline 2, 7]")
    return validation_results


def validate_author_name_rules(author_name):
    validation_results = []
    if not author_name:
        validation_results.append(
            "❌ **Author Name:** Primary author name is missing. Mandatory and cannot be changed after publishing. [Guideline 7]")
    else:
        if re.search(r'<[^>]+>', author_name):
            validation_results.append("❌ **Author Name:** Contains HTML tags. Not allowed. [Guideline 7]")
        if not re.fullmatch(r"^[a-zA-Z0-9À-ÖØ-öø-ÿĀ-žḀ-ỿ\s.'-]+$", author_name):
            validation_results.append(
                "⚠️ **Author Name:** Contains characters that might be considered unusual beyond letters, numbers, spaces, periods, hyphens, or apostrophes. Please review. [Guideline 7]")
    return validation_results


def validate_description_basic_html_rules(description_text):
    validation_results = []
    if not description_text: return ["ℹ️ **Description:** No description provided for HTML check."]
    unsupported_tags_pattern = r"<(/?)((h[1-3])|script|style|img|font|map|object|embed|iframe|applet|form|input|button|select|textarea|frameset|frame|noframes|link|meta)([\s>][^>]*)?>"
    found_unsupported = re.findall(unsupported_tags_pattern, description_text, re.IGNORECASE)
    if found_unsupported:
        unique_unsupported_tags = sorted(list(set([tag[1].lower() for tag in found_unsupported])))
        validation_results.append(
            f"⚠️ **Description HTML:** Found potentially unsupported HTML tags: {', '.join(unique_unsupported_tags)}. KDP only supports a limited set including <br>, <p>, <b>, <em>, <i>, <u>, <h4>-<h6>, <ol>, <ul>, <li>. Review Guideline 10.")
    return validation_results


def validate_keywords_rules(keywords_list):
    validation_results = []
    if not any(kw.strip() for kw in keywords_list):
        validation_results.append(
            "ℹ️ **Keywords:** No keywords provided. Crucial for discoverability. [Guideline 9, 10]")
        return validation_results
    filled_keywords = [k for k in keywords_list if k.strip()]
    if len(filled_keywords) > 7:
        validation_results.append(
            f"❌ **Keywords Count:** {len(filled_keywords)} entered. KDP allows up to 7. [Guideline 9]")
    prohibited_keyword_terms = ["free", "bestselling", "on sale", "new", "available now", "kindle unlimited",
                                "kdp select"]
    for i, kw in enumerate(filled_keywords):
        kw_lower = kw.lower()
        if re.search(r'<[^>]+>', kw):
            validation_results.append(f"❌ **Keyword {i + 1} ('{kw}'):** Contains HTML tags. [Guideline 9, 10]")
        for term in prohibited_keyword_terms:
            if term in kw_lower:
                if term in ["book", "ebook"] and len(kw_lower.split()) > 1: continue
                validation_results.append(
                    f"⚠️ **Keyword {i + 1} ('{kw}'):** Contains potentially prohibited term '{term}'. Review Guideline 9.")
        if '"' in kw:
            validation_results.append(
                f"⚠️ **Keyword {i + 1} ('{kw}'):** Contains quotation marks. Not recommended. [Guideline 9]")
    return validation_results


def validate_isbn_rules(isbn_str, is_low_content, book_format):
    validation_results = []
    is_print_format = book_format in ["Paperback", "Hardcover"]
    if not isbn_str:
        if is_print_format and not is_low_content:
            validation_results.append(
                "ℹ️ **ISBN:** No ISBN provided. For non-low-content print books, an ISBN is required. KDP can provide one. [Guideline 11]")
        elif is_low_content:
            validation_results.append(
                "ℹ️ **ISBN:** No ISBN provided. Acceptable for low-content books. Note: Free KDP ISBNs are not available for low-content. [Guideline 6, 11]")
        return validation_results
    cleaned_isbn = isbn_str.replace("-", "").replace(" ", "")
    if not cleaned_isbn.isdigit():
        validation_results.append(f"❌ **ISBN ('{isbn_str}'):** Should primarily contain digits. [Guideline 11]")
        return validation_results
    length = len(cleaned_isbn)
    if length not in [10, 13]:
        validation_results.append(
            f"❌ **ISBN ('{isbn_str}'):** Must be 10 or 13 digits long (excluding hyphens). Found {length} digits. [Guideline 11]")
    if is_low_content:
        validation_results.append(
            "⚠️ **ISBN & Low Content:** You've provided an ISBN for a low-content book. Free KDP ISBNs are not available for low-content. If this is your own, ensure it's registered correctly. [Guideline 6, 11]")
    return validation_results


def validate_language_and_format_rules(selected_language_metadata, book_format, manuscript_upload_format="Other"):
    validation_results = []
    ebook_only_langs = ["Arabic", "Chinese (Traditional)", "Gujarati", "Hindi", "Malayalam", "Marathi", "Tamil"]
    paperback_centric_langs = ["Hebrew", "Polish", "Latin", "Ukrainian", "Yiddish"]
    if book_format == "eBook":
        if selected_language_metadata in paperback_centric_langs:
            validation_results.append(
                f"❌ **Language/Format:** '{selected_language_metadata}' is primarily print-supported. Verify KDP. [Guideline 11]")
    elif book_format in ["Paperback", "Hardcover"]:
        if selected_language_metadata in ebook_only_langs:
            validation_results.append(
                f"❌ **Language/Format:** '{selected_language_metadata}' is eBooks *only*. [Guideline 11]")
        if selected_language_metadata == "Japanese" and book_format == "Hardcover":
            validation_results.append(
                f"⚠️ **Language/Format:** Japanese Hardcover may have specific KDP requirements. Verify. [Guideline 11]")
        if selected_language_metadata == "Yiddish" and book_format == "Hardcover":
            validation_results.append("ℹ️ **Language/Format:** Yiddish Hardcovers should be LTR. [Guideline 11]")
        if selected_language_metadata == "Japanese":
            validation_results.append("ℹ️ **Japanese Reading Direction:** Ensure correct KDP setup. [Guideline 11]")
    pdf_supported_langs = ["English", "French", "German", "Italian", "Portuguese", "Spanish", "Catalan", "Galician",
                           "Basque"]
    if manuscript_upload_format == "PDF" and selected_language_metadata not in pdf_supported_langs:
        validation_results.append(
            f"⚠️ **Manuscript Format/Language:** PDF uploads for '{selected_language_metadata}' may not be supported. KDP primarily supports PDF for: {', '.join(pdf_supported_langs)}. [Guideline 11]")
    return validation_results


def validate_ai_content_declaration_rules(ai_used_any, ai_text_detail, ai_images_detail, ai_translation_detail):
    validation_results = []
    if ai_used_any == "No":
        validation_results.append(
            "📝 **AI Content Declaration:** User states no AI tools were used to create content. [Guideline 1]")
        return validation_results
    validation_results.append("📝 **AI Content Declaration: User indicated use of AI tools.** [Guideline 1]")
    if "None" not in ai_text_detail:
        if "minimal or no editing" in ai_text_detail or "Entire work" in ai_text_detail:
            validation_results.append(
                f"  - AI-Generated Text: '{ai_text_detail}'. **This requires disclosure to KDP.**")
        else:
            validation_results.append(
                f"  - AI-Assisted Text: '{ai_text_detail}'. KDP defines AI-assisted as user-created then refined by AI; this generally does not require disclosure. However, if AI *created* text sections (even with later extensive edits by user), it's AI-Generated and needs disclosure.")
    else:
        validation_results.append("  - AI Text: None.")
    if "None" not in ai_images_detail:
        validation_results.append(
            f"  - AI-Generated Images: '{ai_images_detail}'. **This requires disclosure to KDP.** (KDP considers all AI-created images as 'AI-Generated' regardless of edits).")
    else:
        validation_results.append("  - AI Images: None.")
    if "None" not in ai_translation_detail:
        if "minimal or no editing" in ai_translation_detail or "Entire work" in ai_translation_detail:
            validation_results.append(
                f"  - AI-Generated Translation: '{ai_translation_detail}'. **This requires disclosure to KDP.**")
        else:
            validation_results.append(
                f"  - AI-Assisted Translation: '{ai_translation_detail}'. Similar to text, if AI *created* translated sections, it's AI-Generated. If user translated and AI refined, it's AI-Assisted. Disclosure depends on KDP definitions.")
    else:
        validation_results.append("  - AI Translation: None.")
    validation_results.append(
        "  Please carefully review KDP's definitions of 'AI-Generated' vs. 'AI-Assisted' content and ensure your declarations to KDP are accurate. You are responsible for all content adhering to guidelines, including IP rights.")
    return validation_results


def validate_low_content_implications_rules(is_low_content):
    validation_results = []
    if is_low_content:
        validation_results.append("ℹ️ **Low-Content Book:** Noted. Remember: [Guideline 6]")
        validation_results.append("  - Free KDP ISBNs not available.")
        validation_results.append("  - Not eligible for KDP Series.")
        validation_results.append("  - 'Look Inside' may not be supported without own ISBN (use A+ Content).")
        validation_results.append("  - Transparency codes not available without own ISBN.")
        validation_results.append("  - No 'Set Release Date' option.")
        validation_results.append("  - Ensure no barcode in cover's bottom-right if KDP places one.")
    return validation_results


def validate_series_info_rules(is_series, series_name, series_number_str, is_low_content, is_public_domain):
    validation_results = []
    if is_series:
        if is_low_content: validation_results.append(
            "❌ **Series & Low Content:** Low-content books ineligible for series. [Guideline 6, 11]")
        if is_public_domain: validation_results.append(
            "❌ **Series & Public Domain:** Public domain books ineligible for series. [Guideline 2, 11]")
        series_title_results = validate_title_and_subtitle(series_name, "", field_name="Series Title")
        if any("❌" in res or "⚠️" in res for res in series_title_results): validation_results.append(
            "--- Issues in Series Title ---")
        validation_results.extend(series_title_results)
        if any("❌" in res or "⚠️" in res for res in series_title_results): validation_results.append(
            "--- End of Issues in Series Title ---")
        if series_number_str:
            if not series_number_str.isdigit():
                validation_results.append(
                    f"❌ **Series Number ('{series_number_str}'):** Must be digits only. [Guideline 2]")
            elif series_name and re.search(r'\b' + re.escape(series_number_str) + r'\b', series_name, re.IGNORECASE):
                validation_results.append(
                    f"⚠️ **Series Name & Number:** Series name ('{series_name}') appears to contain series number ('{series_number_str}'). Usually only series name here. [Guideline 2]")
        else:
            validation_results.append("ℹ️ **Series Number:** Not provided. Usually required for numbered series.")
    return validation_results


def validate_primary_audience_rules(sexually_explicit, min_age_input, max_age_input, categories_str_list):
    validation_results = []
    children_category_keywords = ["children", "kids", "juvenile", "baby", "toddler", "picture book", "early reader",
                                  "middle grade"]
    min_age, max_age = None, None
    try:
        min_age = int(min_age_input) if min_age_input is not None and min_age_input != 0 else None
    except ValueError:
        validation_results.append("⚠️ **Reading Age:** Minimum reading age must be a number if not 0 for 'Not Set'.")
    try:
        max_age = int(max_age_input) if max_age_input is not None and max_age_input != 0 else None
    except ValueError:
        validation_results.append("⚠️ **Reading Age:** Maximum reading age must be a number if not 0 for 'Not Set'.")

    if sexually_explicit == "Yes":
        validation_results.append(
            "⚠️ **Sexually Explicit Content:** Declared. Ineligible for Children’s categories. [Guideline 2, 11]")
        if min_age is not None and min_age < 18:
            validation_results.append(
                f"⚠️ **Sexually Explicit & Reading Age:** Explicit content but min reading age is {min_age}. Contradictory. [Guideline 2, 11]")
        for cat_str in categories_str_list:
            if cat_str and any(child_kw in cat_str.lower() for child_kw in children_category_keywords):
                validation_results.append(
                    f"❌ **Sexually Explicit & Category:** Explicit content, but category '{cat_str}' seems for children. Not allowed. [Guideline 2, 11]")
    if min_age is not None and max_age is not None:
        if min_age < 0 or max_age < 0:
            validation_results.append("❌ **Reading Age:** Ages cannot be negative.")
        elif min_age > max_age:
            validation_results.append(f"❌ **Reading Age:** Min age ({min_age}) > Max age ({max_age}). [Guideline 11]")
    elif min_age is not None and max_age is None:
        validation_results.append(
            "ℹ️ **Reading Age:** Min age set, but Max is not. Consider setting Max. [Guideline 11]")
    elif min_age is None and max_age is not None:
        validation_results.append(
            "ℹ️ **Reading Age:** Max age set, but Min is not. Consider setting Min. [Guideline 11]")

    is_children_ya_category = any(any(child_kw in cat.lower() for child_kw in children_category_keywords) or \
                                  any(teen_kw in cat.lower() for teen_kw in ["teen", "young adult", "ya"]) for cat in
                                  categories_str_list if cat)
    if is_children_ya_category and min_age is None:
        validation_results.append(
            "⚠️ **Reading Age & Category:** Children/YA category selected. Setting Min/Max reading age is highly recommended. [Guideline 11]")
    elif min_age is not None and (min_age > 17 or (max_age is not None and max_age > 18)) and is_children_ya_category:
        validation_results.append(
            "⚠️ **Reading Age & Category:** Reading age seems for adults, but a Children/YA category is selected. Verify. [Guideline 11]")
    return validation_results


def validate_categories_rules(categories_list):
    validation_results = []
    filled_categories = [c.strip() for c in categories_list if c.strip()]
    if len(filled_categories) > 3:
        validation_results.append(
            f"❌ **Categories Count:** {len(filled_categories)} selected. KDP allows up to 3. [Guideline 2]")
    if not filled_categories:
        validation_results.append(
            "ℹ️ **Categories:** No categories provided. Crucial for discoverability. [Guideline 2]")
    return validation_results


def calculate_and_display_print_specs_rules(trim_size_str, page_count_str, interior_bleed_str, ink_paper_type_str,
                                            book_format_str):
    results = []
    if trim_size_str == "Select Trim Size": results.append(
        "❌ **Print Specs - Trim Size:** Please select."); return results
    if ink_paper_type_str == "Select Ink/Paper": results.append(
        "❌ **Print Specs - Ink & Paper:** Please select."); return results
    try:
        trim_size_clean = trim_size_str.replace("\"", "").replace("“", "").replace("”", "").replace("(A4)", "").strip()
        parts = [p.strip() for p in trim_size_clean.lower().split('x')]
        if len(parts) != 2: raise ValueError("Trim size format")
        width, height = float(parts[0]), float(parts[1])
    except ValueError:
        results.append(f"❌ **Print Specs - Trim Size ('{trim_size_str}'):** Parse error."); return results
    try:
        page_count = int(page_count_str)
        if page_count < 1: raise ValueError("Page count positive")
    except ValueError:
        results.append("❌ **Print Specs - Page Count:** Must be positive whole number."); return results
    has_bleed = interior_bleed_str == "Yes"
    results.append(
        f"**Selected Trim:** {trim_size_str}, **Ink/Paper:** {ink_paper_type_str}, **Bleed:** {interior_bleed_str}, **Format:** {book_format_str}")
    ink_key_segment = INK_PAPER_TO_KEY_MAP.get(ink_paper_type_str)
    ink_key = (
        "hc_" + ink_key_segment if ink_key_segment else None) if book_format_str == "Hardcover" else ink_key_segment
    if book_format_str == "Hardcover" and ink_paper_type_str == "Standard color interior with white paper":
        results.append(
            f"❌ **Print Specs - Ink/Paper:** 'Standard color' not usually for Hardcovers. Choose Premium Color or Black Ink. [Guideline 13]");
        ink_key = None

    page_count_ok_msg = f"⚠️ **Print Specs - Page Count Check:** Could not auto-verify limits for '{trim_size_str}', '{ink_paper_type_str}', '{book_format_str}'. Verify KDP Guideline 13 table carefully."
    if trim_size_str in KDP_PAGE_COUNT_SPECS and ink_key and ink_key in KDP_PAGE_COUNT_SPECS[trim_size_str]:
        min_pages, max_pages = KDP_PAGE_COUNT_SPECS[trim_size_str][ink_key]
        if not (min_pages <= page_count <= max_pages):
            page_count_ok_msg = f"❌ **Print Specs - Page Count Error:** For {trim_size_str} ({ink_paper_type_str}, {book_format_str}), pages must be {min_pages}-{max_pages}. Yours: {page_count}. [Guideline 13]"
        else:
            page_count_ok_msg = f"✅ **Print Specs - Page Count OK:** {page_count} pages is within {min_pages}-{max_pages} for {trim_size_str} ({ink_paper_type_str}, {book_format_str})."
    results.append(page_count_ok_msg)
    doc_width, doc_height = width, height
    if has_bleed: doc_width += 0.125; doc_height += 0.250
    results.append(
        f"✅ **Document Page Setup Size ({'with' if has_bleed else 'no'} bleed):** {doc_width:.3f}\" W x {doc_height:.3f}\" H.")
    if has_bleed: results.append("   Ensure bleed elements extend to these full dimensions.")
    inside_margin, inside_margin_str = 0.0, "Verify KDP for this page count/format"
    if 24 <= page_count <= 150:
        inside_margin = 0.375
    elif 151 <= page_count <= 300:
        inside_margin = 0.5
    elif 301 <= page_count <= 500:
        inside_margin = 0.625
    elif 501 <= page_count <= 700:
        inside_margin = 0.75
    elif 701 <= page_count <= 828:
        inside_margin = 0.875
    if book_format_str == "Hardcover":
        if 75 <= page_count <= 550:
            inside_margin = 0.625
        else:
            results.append(
                f"⚠️ **Print Specs - Margins:** Page count {page_count} for Hardcover. Verify specific KDP margin tables as they are highly detailed.")

    if inside_margin > 0:
        inside_margin_str = f"{inside_margin:.3f}\""
    elif not any("Margins:" in r for r in results if "⚠️" in r):
        results.append(f"⚠️ **Print Specs - Margins:** Page count {page_count}. Verify KDP tables.")
    outside_margin_min = 0.375 if has_bleed else 0.25
    results.append(
        f"**Minimum Margin Requirements (General - Verify KDP Guideline 13):** Inside (Gutter): {inside_margin_str}, Outside (Top, Bottom, Outer Edge): At least {outside_margin_min:.3f}\"")
    results.append(
        "   *Note: Hardcover margins are particularly specific; always consult KDP's official tables for your exact trim size, page count, and format to ensure compliance.*")
    return results


def validate_cover_text_match_rules(title_on_cover, author_on_cover, metadata_title, metadata_author):
    validation_results = []
    if not title_on_cover and not author_on_cover: return ["ℹ️ **Cover Text:** No cover text provided for checking."]
    title_match, author_match = True, True
    if title_on_cover and metadata_title and title_on_cover.strip().lower() != metadata_title.strip().lower():
        validation_results.append(
            f"⚠️ **Cover Text Mismatch (Title):** Cover ('{title_on_cover}') != Metadata ('{metadata_title}'). Must match exactly. [Guideline 12]");
        title_match = False
    elif title_on_cover and not metadata_title:
        validation_results.append(
            "⚠️ **Cover Text (Title):** Cover title provided, metadata title missing."); title_match = False
    if author_on_cover and metadata_author and author_on_cover.strip().lower() != metadata_author.strip().lower():
        validation_results.append(
            f"⚠️ **Cover Text Mismatch (Author):** Cover ('{author_on_cover}') != Metadata ('{metadata_author}'). Must match exactly. [Guideline 12]");
        author_match = False
    elif author_on_cover and not metadata_author:
        validation_results.append(
            "⚠️ **Cover Text (Author):** Cover author provided, metadata author missing."); author_match = False
    if title_match and author_match and (title_on_cover or author_on_cover):
        validation_results.append("✅ **Cover Text Match:** Provided cover text appears to match metadata.")
    return validation_results


def validate_translation_info_rules(is_translation, original_author, translator_name):
    validation_results = []
    if is_translation:
        if not original_author:
            validation_results.append("❌ **Original Author (Translation):** Must be provided. [Guideline 1]")
        else:
            validation_results.append("✅ Original Author (Translation) provided.")
        if not translator_name:
            validation_results.append(
                "⚠️ **Translator (Translation):** Must be provided. Use 'Anonymous' if unknown. [Guideline 1]")
        else:
            validation_results.append("✅ Translator Name (Translation) provided.")
    return validation_results


def validate_public_domain_differentiation_rules(is_public_domain, description_text,
                                                 public_domain_differentiation_statement=""):
    validation_results = []
    if is_public_domain:
        validation_results.append("ℹ️ **Public Domain Book:** Noted.")
        validation_results.append(
            "  - Reminder: Undifferentiated public domain titles are not allowed if a free version is already in the Kindle store. Your version must be *substantially* differentiated. [Guideline 1]")
        differentiation_keywords = ["annotated", "annotation", "illustrated", "illustration", "introduction by",
                                    "commentary by", "critical edition", "new translation", "foreword by",
                                    "translated by", "edited by", "with original artwork", "unique collection",
                                    "scholarly analysis", "new research"]
        text_to_check_for_keywords = description_text.lower() + " " + public_domain_differentiation_statement.lower()
        if not public_domain_differentiation_statement.strip() and not any(
                kw in description_text.lower() for kw in differentiation_keywords):
            validation_results.append(
                "  ❌ **Differentiation Not Stated:** Please describe how your public domain version is *substantially differentiated* (e.g., unique annotations, new translation, original illustrations, scholarly introduction) in the dedicated field or ensure it's very clear in your book description. This is crucial. [Guideline 1]")
        elif public_domain_differentiation_statement.strip() and not any(
                kw in public_domain_differentiation_statement.lower() for kw in differentiation_keywords):
            validation_results.append(
                "  ⚠️ **Differentiation Statement Lacks Clarity:** Your differentiation statement ('" + public_domain_differentiation_statement[
                                                                                                        :50] + "...') does not clearly use common terms for substantial differentiation like 'annotated', 'new translation', 'original illustrations', 'scholarly introduction'. Please ensure your statement clearly conveys unique, KDP-acceptable value. [Guideline 1]")
        elif any(kw in text_to_check_for_keywords for kw in differentiation_keywords):
            validation_results.append(
                "  ✅ Description/Statement appears to mention potential differentiation. Ensure this reflects substantial unique value (e.g., not just minor formatting changes).")
        else:
            validation_results.append(
                "  ⚠️ **Differentiation Not Clear:** Could not identify clear terms of substantial differentiation in your description or statement. Please explicitly describe the unique value added. [Guideline 1]")
    return validation_results


# --- AI Check Functions ---
def ai_check_infringing_content(title, subtitle, description):
    results = []
    if not title and not description: return ["ℹ️ Title and description needed for infringing content check."]
    combined_text = f"Title: {title}\nSubtitle: {subtitle}\nDescription Snippet: {description[:300]}"
    prompt = f"""You are a KDP content policy assistant. Review book details: {combined_text}
    Does this content strongly suggest it might be a summary, study guide, analysis, or unauthorized companion book to another well-known copyrighted work (e.g., a famous novel or series)?
    If yes, provide actionable feedback as a bullet point:
    - State that it *might* be a companion/summary, briefly why (e.g., "Uses terms like 'summary of...'").
    - Strongly advise the user to ensure they possess all necessary publishing rights and permissions, especially for sales outside the U.S., to avoid infringing on copyright, as per KDP Guideline 1.
    If no, state: "Content does not immediately raise concerns as an infringing companion book/summary based on provided text."
    """
    ai_feedback = invoke_claude_model(prompt, max_tokens=350)
    if ai_feedback:
        results.append(ai_feedback)
    else:
        results.append("⚠️ AI check for infringing content failed or returned no response.")
    return results


def ai_check_misleading_description(description, manuscript_text):
    results = []
    if not description: return ["ℹ️ No description provided for misleading content check."]
    if not manuscript_text or len(manuscript_text) < 200:
        return ["ℹ️ Manuscript text too short/not provided for a meaningful description vs. content comparison."]
    prompt = f"""You are a KDP content quality assistant. Compare the book description with the manuscript text snippet.
    Book Description: --- {description} ---
    Manuscript Snippet (first ~1000 chars): --- {manuscript_text[:1000]} ---
    Identify potential discrepancies that might lead to a poor customer experience due to a misleading description.
    Specifically look for:
    - Claims in the description (e.g., specific content, number of items, key topics, outcomes, audience) NOT clearly supported or seem contradicted by the manuscript snippet.
    - Overstated benefits not reflected in the manuscript.
    List significant discrepancies as actionable bullet points. For each, explain the mismatch and suggest specific ways to make the description more accurate or to align it with the manuscript content.
    If generally aligned, state: "Description and manuscript snippet appear generally aligned regarding key claims based on this limited comparison."
    """
    ai_feedback = invoke_claude_model(prompt, max_tokens=500)
    if ai_feedback:
        results.append(ai_feedback)
    else:
        results.append("⚠️ AI check for misleading description failed or returned no response.")
    return results


def ai_check_freely_available_content(manuscript_text):
    results = []
    if not manuscript_text or len(manuscript_text) < 300:
        return ["ℹ️ Manuscript text too short/not provided for 'freely available content' check."]
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', manuscript_text.strip())
    candidate_sentences = sorted(list(set(s.strip() for s in sentences if 15 < len(s.split()) < 60 and len(s) > 80)),
                                 key=len, reverse=True)
    if not candidate_sentences: return [
        "ℹ️ Could not find enough distinct, long sentences for 'freely available content' check."]
    sentences_to_check = random.sample(candidate_sentences, min(len(candidate_sentences), 3))
    prompt_sentences_block = "Sentences to assess:\n" + "".join(
        f"{i + 1}. \"{sent}\"\n" for i, sent in enumerate(sentences_to_check))
    prompt = f"""{prompt_sentences_block}
    For each numbered sentence above:
    - Assess its likelihood (Low, Medium, High) of being commonly found verbatim on the public web.
    - Provide a brief justification for your assessment.
    - Format as a bullet point: "* Sentence X: [Likelihood] - [Justification]"
    Conclude with a strong reminder: "Ensure you hold all necessary publishing rights. KDP strictly prohibits publishing copyrighted content that is freely available on the web unless you are the copyright owner or have explicit permission."
    Present the entire response as a structured list.
    """
    ai_feedback = invoke_claude_model(prompt, max_tokens=700)
    if ai_feedback:
        results.append(ai_feedback)
    else:
        results.append("⚠️ AI check for freely available content failed or returned no response.")
    return results


def ai_check_manuscript_typos_placeholders_accessibility(manuscript_text):
    results = []
    if not manuscript_text or len(manuscript_text) < 100:
        return ["ℹ️ Manuscript text too short/not provided for detailed quality/placeholder/accessibility checks."]
    text_chunk_for_analysis = manuscript_text[:4000]
    prompt = f"""You are a KDP manuscript quality assistant. Review the manuscript snippet (approx first {len(text_chunk_for_analysis)} characters) for three areas. Provide feedback as a bulleted list under each subheading. If no issues found in a category, state "No specific issues noted in this snippet." for that category.

    1.  **Typos and Grammatical Errors:**
        - List up to 5-7 noticeable typos or grammatical errors. For each, show the original text snippet and your suggested correction. (Example: - Original: "Its a nice day." -> Suggested: "It's a nice day.")

    2.  **Placeholder Text Scan:**
        - Identify and list any common placeholder text (e.g., "Lorem Ipsum", "Insert Chapter Title Here", "[Editor's Note]", "TBD", "Placeholder for image", "Coming Soon...", "your text here", "Add content here").

    3.  **Content Accessibility Hints (Advisory):**
        - Identify elements that might require specific accessibility considerations for the final book. Provide actionable suggestions. (Examples:
            - "Text near '...' describes an image; ensure detailed alt text is planned."
            - "A list near '...' might need proper HTML list formatting (ul/ol) for screen readers in an ebook. Review its current structure.")

    Manuscript Snippet: --- {text_chunk_for_analysis} ---
    """
    ai_feedback = invoke_claude_model(prompt, max_tokens=1800)
    if ai_feedback:
        results.append(ai_feedback)
    else:
        results.append("⚠️ AI check for typos/placeholders/accessibility failed.")
    return results


def ai_check_manuscript_general_quality_issues(manuscript_text):
    results = []
    if not manuscript_text or len(manuscript_text) < 200:
        return ["ℹ️ Manuscript text too short/not provided for general quality check."]
    text_chunk = manuscript_text[:3000]
    prompt = f"""You are a KDP content quality reviewer. Analyze the manuscript snippet (approx first {len(text_chunk)} characters) for general quality issues per Kindle Content Quality Guides. Provide feedback as actionable bullet points under each category if issues are found. If no issues noted for a category, state "No specific issues noted in this snippet."

    1.  **Incomplete Content or Abrupt Endings:**
        - Any signs the content ends abruptly, might be missing chapters/sections, or refers to content not present? (e.g., "Conclusion:" followed by very little text, or "As discussed in the next chapter..." with no more text). Provide specific examples and suggest checking manuscript completeness.

    2.  **Distracting Formatting (from text patterns):**
        - Evidence of overuse of ALL CAPS (e.g., multiple consecutive sentences), or seemingly excessive/inconsistent use of **bolding** or *italics* that might hinder readability? Provide specific examples of the pattern and advise review for consistency and reader experience.

    3.  **Inappropriate Solicitation in Narrative:**
        - Any direct requests for reviews, ratings, or social media follows *within the main narrative text* (not end matter)? Quote the problematic phrase and advise removing or relocating it.

    4.  **Basic Structure Issues (from text patterns):**
        - Obvious issues with list formatting (e.g., items run together without clear bulleting/numbering patterns)? Suggest reviewing list structure for clarity.
        - Dialogue presentation that seems consistently confusing due to lack of clear speaker attribution or standard dialogue formatting (e.g., missing quotation marks often)? Advise reviewing dialogue for clarity.

    Manuscript Snippet: --- {text_chunk} ---
    Be specific with examples from the text where possible and suggest what the author should review or fix.
    """
    ai_feedback = invoke_claude_model(prompt, max_tokens=1200)
    if ai_feedback:
        results.append(ai_feedback)
    else:
        results.append("⚠️ AI check for general manuscript quality failed.")
    return results


def ai_check_links_in_manuscript(manuscript_text):
    results = []
    if not manuscript_text or len(manuscript_text) < 50:
        return ["ℹ️ Manuscript text too short/not provided for link analysis."]
    url_pattern = r'(?:(?:https?|ftp):\/\/|www\.)[\w\/\-?=%.~+#&;]+[\w\/\-?=%.~+#&;]'
    found_urls = re.findall(url_pattern, manuscript_text)
    if not found_urls: return ["ℹ️ No URLs automatically detected in the manuscript text for AI review."]
    urls_to_check_str = "\n".join(list(set(found_urls))[:5])
    prompt = f"""You are a KDP content policy assistant. URLs were found in a manuscript:
    Detected URLs (up to 5 unique shown): {urls_to_check_str}

    Provide feedback based on KDP's Link Guidelines as actionable bullet points:
    1.  **Functionality & Relevance:** Stress that all links *must* be functional and navigate to the expected, relevant destination.
    2.  **Prohibited Link Types:** Explicitly warn that links to pornography, other commercial eBook stores (besides Amazon), web forms collecting extensive personal data, illegal/harmful/infringing/offensive content, or malicious sites are strictly prohibited and can lead to content rejection or account action.
    3.  **Descriptive Link Text:** Advise using descriptive hyperlink text (e.g., "View our author page on Amazon") not generic phrases like "click here" or just the raw URL.
    4.  **Bonus Content Placement:** Remind that bonus content (like previews of other books) should not be frontloaded or use links that disruptively take readers from primary content.
    5.  **Mandatory Action:** State that the user *must manually test every link* using Kindle Previewer before publishing to ensure they work correctly and lead to appropriate content.
    """
    ai_feedback = invoke_claude_model(prompt, max_tokens=800)
    if ai_feedback:
        results.append(
            f"Detected URLs for review: {', '.join(list(set(found_urls))[:5])}{' (and potentially more)' if len(set(found_urls)) > 5 else ''}")
        results.append(ai_feedback)
    else:
        results.append("⚠️ Could not get AI feedback on detected links.")
    return results


def ai_check_duplicated_text_in_manuscript(manuscript_text):
    results = []
    if not manuscript_text or len(manuscript_text) < 500:
        return ["ℹ️ Manuscript text too short/not provided for duplicated text analysis."]
    text_chunk = manuscript_text[:5000]
    prompt = f"""You are a KDP content quality assistant. Analyze manuscript snippet (approx first {len(text_chunk)} characters) for potentially unintentional duplicated text blocks.
    Focus on substantial verbatim or very near-verbatim repetitions of text (e.g., one or more full sentences, or entire paragraphs) that appear close to each other or in a way that seems like a copy-paste error, rather than an intentional literary device.

    For each suspected unintentional duplication (list up to 3 examples for brevity):
    1.  Provide a short snippet (first 10-15 words) of the duplicated text.
    2.  Briefly explain why it seems unintentional (e.g., "This exact paragraph appears twice consecutively...").
    3.  Suggest the author carefully review the manuscript for such errors.

    If no obvious unintentional duplications found, state: "No significant unintentional text duplications identified in this snippet."
    Present findings as a bulleted list.
    Manuscript Snippet: --- {text_chunk} ---
    """
    ai_feedback = invoke_claude_model(prompt, max_tokens=800)
    if ai_feedback:
        results.append(ai_feedback)
    else:
        results.append("⚠️ Could not perform AI check for duplicated text.")
    return results


def ai_check_disappointing_content_issues(manuscript_text, description_text, is_translation):
    results = []
    if not manuscript_text and not description_text:
        return ["ℹ️ Manuscript and description needed for disappointing content checks."]
    text_chunk = manuscript_text[:2000] if manuscript_text else ""
    prompt = f"""You are a KDP content quality assistant. Review for potential "Disappointing Content" issues per KDP guidelines. Provide actionable bullet points.

    Book Description: "{description_text[:500]}..."
    Manuscript Snippet (approx first {len(text_chunk)} chars): "{text_chunk}..."
    Is this a Translation: {is_translation}

    Check for:
    1.  **Content Too Short (Impression):** Based *only* on the snippet and description, does content seem unusually brief for what description implies (e.g., description of novel, snippet is few paragraphs)? This is a rough impression. If so, suggest user verify full length meets expectations and provides a complete experience.
    2.  **Poorly Translated (if applicable):** If a translation, does snippet contain awkward phrasing, unnatural grammar, or word choices suggesting poor translation? Provide a specific example and strongly suggest professional review if so. If not translation or quality seems fine, state that.
    3.  **Primary Purpose - Solicitation/Advertisement:** Does description or snippet seem *overwhelmingly* focused on soliciting/advertising rather than substantive content? Suggest toning down and focusing on reader value.
    4.  **Bonus Content Placement (Advisory):** Remind that any bonus content (previews) must not appear before book's primary content and should not be disruptive.

    If no specific issues are noted for a point, state "No immediate concerns noted for [point name] based on provided text."
    """
    ai_feedback = invoke_claude_model(prompt, max_tokens=1000)
    if ai_feedback:
        results.append(ai_feedback)
    else:
        results.append("⚠️ AI check for disappointing content issues failed.")
    return results


def ai_check_public_domain_differentiation(is_public_domain, differentiation_statement):
    results = []
    if not is_public_domain: return []
    if not differentiation_statement.strip():
        return [
            "ℹ️ Public domain selected, but no differentiation statement provided for AI assessment. Please provide one or ensure differentiation is clear in your book description."]
    prompt = f"""A KDP user states their book is public domain and provided this differentiation statement:
    Statement: "{differentiation_statement}"
    Assess this statement for KDP's requirement of *substantial* differentiation (e.g., unique translation, original annotations, scholarly analysis, unique illustrative content).
    - Does the statement clearly convey unique, added value?
    - Does it sound substantial, or like minor changes/repackaging?
    - Provide a brief assessment (e.g., "Statement appears to describe substantial differentiation like...", "Statement is vague and may not meet KDP requirements because...").
    - Offer 1-2 actionable bullet points for strengthening the statement if weak/unclear, focusing on KDP-acceptable differentiation types like original scholarly contributions, unique annotations, or new illustrative/translated content.
    """
    ai_feedback = invoke_claude_model(prompt, max_tokens=500)
    if ai_feedback:
        results.append(ai_feedback)
    else:
        results.append("⚠️ Could not get AI feedback on public domain differentiation statement.")
    return results


def ai_extract_details_for_autofill(manuscript_text):
    suggestions = {"title": "", "author": "", "language": "", "description_draft": "", "keywords": [], "categories": [],
                   "series_title": "", "series_number": "", "is_translation_hint": False, "original_author_hint": "",
                   "translator_hint": ""}
    if not manuscript_text or len(manuscript_text) < 200:
        st.toast("ℹ️ Manuscript text too short for comprehensive auto-fill.", icon="INFO")
        return suggestions
    text_chunk = manuscript_text[:7000]
    prompt = f"""Analyze the manuscript text snippet (approx first {len(text_chunk)} characters)
    and attempt to extract or infer the following information.
    Provide your response strictly in JSON format with the exact keys listed below.
    If a piece of information cannot be confidently determined, use an empty string "" or an empty list [].

    Keys to extract:
    - "title_suggestion": The most likely book title.
    - "author_suggestion": The most likely primary author's name.
    - "language_suggestion": The primary language of the text (e.g., "English", "Spanish").
    - "description_draft_suggestion": A short, compelling draft book description (2-3 sentences, ~50-75 words) based on the initial content.
    - "keyword_suggestions": A list of 3-5 relevant keywords or short phrases (2-3 words each).
    - "category_suggestions": A list of 1-2 broad genre categories that seem appropriate (e.g., "Science Fiction", "Historical Romance", "Self-Help").
    - "series_title_suggestion": If the text strongly indicates it's part of a series (e.g., "Book Two of The Great Chronicles"), suggest the series title.
    - "series_number_suggestion": If a series number is clearly indicated with the series title, suggest the number (digits only).
    - "is_translation_hint": true if there are strong textual cues like "translated by" or "original title:", otherwise false.
    - "original_author_hint": If is_translation_hint is true and an original author is mentioned, suggest their name.
    - "translator_hint": If is_translation_hint is true and a translator is mentioned, suggest their name.

    Prioritize information found early in the text (e.g., title page, first few paragraphs).
    For description and keywords, try to capture the essence of the beginning of the story/content.

    Manuscript Snippet:
    ---
    {text_chunk}
    ---

    JSON Response:
    """
    ai_feedback_str = invoke_claude_model(prompt, max_tokens=1500)
    if ai_feedback_str and not ai_feedback_str.startswith("Error:") and not ai_feedback_str.startswith(
            "Informational:"):
        try:
            json_match = re.search(r"\{.*\}", ai_feedback_str, re.DOTALL)
            if json_match:
                ai_suggestions = json.loads(json_match.group(0))
                suggestions["title"] = ai_suggestions.get("title_suggestion", "").strip()
                suggestions["author"] = ai_suggestions.get("author_suggestion", "").strip()
                suggestions["language"] = ai_suggestions.get("language_suggestion", "").strip()
                suggestions["description_draft"] = ai_suggestions.get("description_draft_suggestion", "").strip()
                suggestions["keywords"] = [kw.strip() for kw in ai_suggestions.get("keyword_suggestions", []) if
                                           kw.strip()]
                suggestions["categories"] = [cat.strip() for cat in ai_suggestions.get("category_suggestions", []) if
                                             cat.strip()]
                suggestions["series_title"] = ai_suggestions.get("series_title_suggestion", "").strip()
                suggestions["series_number"] = ai_suggestions.get("series_number_suggestion", "").strip()
                suggestions["is_translation_hint"] = ai_suggestions.get("is_translation_hint", False)
                suggestions["original_author_hint"] = ai_suggestions.get("original_author_hint", "").strip()
                suggestions["translator_hint"] = ai_suggestions.get("translator_hint", "").strip()
                st.toast("✅ AI extracted some details! Please review.", icon="🤖")
            else:
                st.toast("⚠️ AI response for auto-fill was not in expected JSON format.", icon="⚠️")
        except json.JSONDecodeError:
            st.toast("⚠️ Error decoding AI response for auto-fill.", icon="⚠️")
        except Exception as e:
            st.toast(f"⚠️ Error processing AI auto-fill: {e}", icon="⚠️")
    elif ai_feedback_str:  # AI returned an error/info message
        st.toast(ai_feedback_str, icon="🤖")
    else:
        st.toast("⚠️ AI did not provide suggestions for auto-fill.", icon="⚠️")
    return suggestions


# --- Main App Logic ---
def main():
    st.set_page_config(page_title="Sentinel AI - KDP Validation Assistant", layout="wide")
    st.title("📚 Sentinel AI")
    st.caption("Your AI-powered KDP Pre-submission Validation Assistant")

    # Initialize session state keys
    default_text_inputs = ['sb_book_title_meta', 'sb_subtitle_meta', 'sb_author_name_meta', 'sb_title_on_cover',
                           'sb_author_on_cover', 'sb_original_author_translation', 'sb_translator_name_translation',
                           'sb_description_text', 'sb_series_name_val', 'sb_series_number_str_val', 'sb_isbn_val',
                           'sb_page_count_input_val', 'sb_public_domain_differentiation_statement']
    default_bool_inputs = ['sb_is_public_domain', 'sb_is_translation', 'sb_is_series_val', 'sb_is_low_content_val']
    updated_ink_paper_options = ["Select Ink/Paper", "Black & white interior with cream paper",
                                 "Black & white interior with white paper", "Standard color interior with white paper",
                                 "Premium color interior with white paper"]
    default_select_radios = {
        'sb_book_format': (["eBook", "Paperback", "Hardcover"], "eBook"),
        'sb_sexually_explicit_val': (("No", "Yes"), "No"),
        'sb_ai_used_any': (("No", "Yes"), "No"),
        'sb_ai_text_detail': (
            ["None", "Some sections, with minimal or no editing", "Some sections, with extensive editing",
             "Entire work, with minimal or no editing", "Entire work, with extensive editing"], "None"),
        'sb_ai_images_detail': (
            ["None", "One or a few, with minimal or no editing", "One or a few, with extensive editing",
             "Many, with minimal or no editing", "Many, with extensive editing"], "None"),
        'sb_ai_translation_detail': (
            ["None", "Some sections, with minimal or no editing", "Some sections, with extensive editing",
             "Entire work, with minimal or no editing", "Entire work, with extensive editing"], "None"),
        'sb_selected_language_val': (sorted(list(
            set(["English", "French", "German", "Italian", "Japanese", "Spanish", "Portuguese", "Arabic",
                 "Chinese (Traditional)", "Dutch/Flemish", "Hebrew", "Hindi", "Polish"]))), "English"),
        'sb_manuscript_upload_format_val': (["Other", "PDF", "DOCX", "EPUB", "HTML", "TXT"], "Other"),
        'sb_trim_size_selection_val': (
            ["Select Trim Size", "5\" x 8\"", "5.06\" x 7.81\"", "5.25\" x 8\"", "5.5\" x 8.5\"", "6\" x 9\"",
             "6.14\" x 9.21\"", "6.69\" x 9.61\"", "7\" x 10\"", "7.44\" x 9.69\"", "7.5\" x 9.25\"", "8\" x 10\"",
             "8.25\" x 6\"", "8.25\" x 8.25\"", "8.5\" x 8.5\"", "8.5\" x 11\"", "8.27\" x 11.69\" (A4)"],
            "Select Trim Size"),
        'sb_ink_paper_type_selection_val': (updated_ink_paper_options, "Select Ink/Paper"),
        'sb_interior_bleed_selection_val': (("No", "Yes"), "No")
    }
    list_inputs = {'sb_categories_input_list': 3, 'sb_keywords_input_list': 7}

    for key in ['validation_results_grouped', 'ai_analysis_feedbacks', 'error_count', 'warning_count',
                'extracted_manuscript_text', 'last_uploaded_filename', 'json_inputs_to_share', 'json_load_area']:
        if key not in st.session_state:
            if key in ['error_count', 'warning_count']:
                st.session_state[key] = 0
            elif key in ['validation_results_grouped', 'ai_analysis_feedbacks']:
                st.session_state[key] = {}
            else:
                st.session_state[key] = ""

    for key in default_text_inputs:
        if key not in st.session_state: st.session_state[key] = ""
    for key in default_bool_inputs:
        if key not in st.session_state: st.session_state[key] = False
    for key, (options, default) in default_select_radios.items():
        if key not in st.session_state: st.session_state[key] = default
    for key, length in list_inputs.items():
        if key not in st.session_state: st.session_state[key] = [""] * length
    if 'sb_min_reading_age_num_val' not in st.session_state: st.session_state.sb_min_reading_age_num_val = 0
    if 'sb_max_reading_age_num_val' not in st.session_state: st.session_state.sb_max_reading_age_num_val = 0

    st.sidebar.markdown("---")
    st.sidebar.subheader("About Sentinel AI")
    st.sidebar.info(
        "Sentinel AI is an AI-powered assistant designed to help KDP authors and publishers "
        "validate their book details and content against KDP guidelines *before* submission. "
        "Its goal is to improve productivity, reduce rejections, and enhance content quality. "
        "Developed for the Amazon Internal Hackathon."
    )
    st.sidebar.markdown("---")
    st.sidebar.header("📖 Book Details & Content")

    if st.sidebar.button("🤖 Auto-fill from Manuscript", key="autofill_button",
                         help="Extract details from uploaded manuscript to pre-fill fields.", use_container_width=True):
        man_text_for_autofill = st.session_state.get("extracted_manuscript_text", "")
        if man_text_for_autofill:
            with st.spinner("🤖 AI is attempting to auto-fill details..."):
                autofill_suggestions = ai_extract_details_for_autofill(man_text_for_autofill)

            if autofill_suggestions.get("title"): st.session_state.sb_book_title_meta = autofill_suggestions["title"]
            if autofill_suggestions.get("author"): st.session_state.sb_author_name_meta = autofill_suggestions["author"]
            if autofill_suggestions.get("language"):
                detected_lang_auto = autofill_suggestions["language"]
                # Attempt to match detected language with supported_languages list for dropdown
                # This list is defined later in the sidebar, so using the default_select_radios for now
                supported_lang_options = default_select_radios['sb_selected_language_val'][0]
                matched_supported_lang = next(
                    (lang for lang in supported_lang_options if detected_lang_auto.lower() in lang.lower()), None)
                if matched_supported_lang: st.session_state.sb_selected_language_val = matched_supported_lang
            if autofill_suggestions.get("description_draft"): st.session_state.sb_description_text = \
            autofill_suggestions["description_draft"]
            if autofill_suggestions.get("keywords"):
                for i in range(min(len(autofill_suggestions["keywords"]), 7)): st.session_state.sb_keywords_input_list[
                    i] = autofill_suggestions["keywords"][i]
            if autofill_suggestions.get("categories"):
                for i in range(min(len(autofill_suggestions["categories"]), 3)):
                    st.session_state.sb_categories_input_list[i] = autofill_suggestions["categories"][i]
            if autofill_suggestions.get("series_title"): st.session_state.sb_series_name_val = autofill_suggestions[
                "series_title"]; st.session_state.sb_is_series_val = True
            if autofill_suggestions.get("series_number"): st.session_state.sb_series_number_str_val = \
            autofill_suggestions["series_number"]
            if autofill_suggestions.get("is_translation_hint"): st.session_state.sb_is_translation = True
            if autofill_suggestions.get("original_author_hint"): st.session_state.sb_original_author_translation = \
            autofill_suggestions["original_author_hint"]
            if autofill_suggestions.get("translator_hint"): st.session_state.sb_translator_name_translation = \
            autofill_suggestions["translator_hint"]
            st.rerun()
        else:
            st.sidebar.warning("Please upload a manuscript first to use the auto-fill feature.")
    st.sidebar.markdown("---")

    # --- Sidebar Inputs ---
    with st.sidebar.expander("📚 Core Book Details", expanded=True):
        st.session_state.sb_book_format = st.selectbox("Intended Book Format",
                                                       default_select_radios['sb_book_format'][0],
                                                       index=default_select_radios['sb_book_format'][0].index(
                                                           st.session_state.sb_book_format),
                                                       key="widget_book_format_sb")
        st.session_state.sb_book_title_meta = st.text_input("Book Title (Metadata)",
                                                            value=st.session_state.sb_book_title_meta, max_chars=200,
                                                            key="widget_book_title_meta_sb")
        st.session_state.sb_subtitle_meta = st.text_input("Subtitle (Metadata, Optional)",
                                                          value=st.session_state.sb_subtitle_meta, max_chars=200,
                                                          key="widget_subtitle_meta_sb")
        st.session_state.sb_author_name_meta = st.text_input("Primary Author Name (Metadata)",
                                                             value=st.session_state.sb_author_name_meta,
                                                             key="widget_author_name_meta_sb")
        st.session_state.sb_is_public_domain = st.checkbox("This book is in the Public Domain",
                                                           value=st.session_state.sb_is_public_domain,
                                                           key="widget_public_domain_sb")
        if st.session_state.sb_is_public_domain:
            st.session_state.sb_public_domain_differentiation_statement = st.text_area(
                "How is your Public Domain version differentiated?",
                value=st.session_state.sb_public_domain_differentiation_statement, height=100,
                key="widget_pd_diff_statement_sb",
                help="Explain unique value: new annotations, translation, original illustrations etc.")
        st.sidebar.markdown("###### Cover Text (Exactly as on Artwork)")
        st.session_state.sb_title_on_cover = st.text_input("Exact Title on Cover",
                                                           value=st.session_state.sb_title_on_cover,
                                                           key="widget_title_on_cover_sb")
        st.session_state.sb_author_on_cover = st.text_input("Exact Author Name on Cover",
                                                            value=st.session_state.sb_author_on_cover,
                                                            key="widget_author_on_cover_sb")
        st.sidebar.markdown("###### Translation Details")
        st.session_state.sb_is_translation = st.checkbox("Is this book a translation?",
                                                         value=st.session_state.sb_is_translation,
                                                         key="widget_is_translation_sb")
        st.session_state.sb_original_author_translation = st.text_input("Original Author (if translation)",
                                                                        value=st.session_state.sb_original_author_translation,
                                                                        key="widget_original_author_translation_sb",
                                                                        disabled=not st.session_state.sb_is_translation)
        st.session_state.sb_translator_name_translation = st.text_input(
            "Translator Name (if translation, use 'Anonymous' if unknown)",
            value=st.session_state.sb_translator_name_translation, key="widget_translator_name_translation_sb",
            disabled=not st.session_state.sb_is_translation)

    with st.sidebar.expander("📝 Description, Categories & Keywords"):
        st.session_state.sb_description_text = st.text_area("Book Description (Plain text or KDP-supported HTML)",
                                                            value=st.session_state.sb_description_text, height=150,
                                                            key="widget_description_text_sb")
        st.sidebar.subheader("🏷️ Categories (Up to 3)")
        for i in range(3): st.session_state.sb_categories_input_list[i] = st.text_input(f"Category {i + 1}", value=
        st.session_state.sb_categories_input_list[i], key=f"widget_category_{i}_sb")
        st.sidebar.subheader("🔍 Keywords (Up to 7)")
        for i in range(7): st.session_state.sb_keywords_input_list[i] = st.text_input(f"Keyword {i + 1}", value=
        st.session_state.sb_keywords_input_list[i], key=f"widget_keyword_{i}_sb")

    with st.sidebar.expander("🧩 Series Information (Optional)"):
        st.session_state.sb_is_series_val = st.checkbox("Is this book part of a series?",
                                                        value=st.session_state.sb_is_series_val,
                                                        key="widget_is_series_val_sb")
        st.session_state.sb_series_name_val = st.text_input("Series Name", value=st.session_state.sb_series_name_val,
                                                            key="widget_series_name_val_sb",
                                                            disabled=not st.session_state.sb_is_series_val)
        st.session_state.sb_series_number_str_val = st.text_input("Series Number (e.g., 1, 2, 3)",
                                                                  value=st.session_state.sb_series_number_str_val,
                                                                  key="widget_series_number_str_val_sb",
                                                                  disabled=not st.session_state.sb_is_series_val)

    with st.sidebar.expander("🎯 Audience & Book Type"):
        st.subheader("Primary Audience")
        st.session_state.sb_sexually_explicit_val = st.radio("Book contains sexually explicit images or title?",
                                                             ("No", "Yes"), index=("No", "Yes").index(
                st.session_state.sb_sexually_explicit_val), key="widget_sexually_explicit_val_sb")
        st.session_state.sb_min_reading_age_num_val = st.number_input("Minimum Reading Age (0 for Not Set)",
                                                                      min_value=0, max_value=100,
                                                                      value=st.session_state.sb_min_reading_age_num_val,
                                                                      step=1, key="widget_min_reading_age_num_sb",
                                                                      help="Enter 0 if you do not want to set a minimum age.")
        st.session_state.sb_max_reading_age_num_val = st.number_input("Maximum Reading Age (0 for Not Set, up to 18+)",
                                                                      min_value=0, max_value=100,
                                                                      value=st.session_state.sb_max_reading_age_num_val,
                                                                      step=1, key="widget_max_reading_age_num_sb",
                                                                      help="Enter 0 if you do not want to set a maximum age.")

        st.subheader("AI Content Declaration")
        st.session_state.sb_ai_used_any = st.radio(
            "Did you use AI-based tools to create ANY content (text, images, or translations)?", ("No", "Yes"),
            index=("No", "Yes").index(st.session_state.sb_ai_used_any), key="widget_ai_used_any_sb")
        if st.session_state.sb_ai_used_any == "Yes":
            ai_text_options = ["None", "Some sections, with minimal or no editing",
                               "Some sections, with extensive editing", "Entire work, with minimal or no editing",
                               "Entire work, with extensive editing"]
            st.session_state.sb_ai_text_detail = st.selectbox("AI-Generated Text Details:", options=ai_text_options,
                                                              index=ai_text_options.index(
                                                                  st.session_state.sb_ai_text_detail),
                                                              key="widget_ai_text_detail_sb")
            ai_image_options = ["None", "One or a few, with minimal or no editing",
                                "One or a few, with extensive editing", "Many, with minimal or no editing",
                                "Many, with extensive editing"]
            st.session_state.sb_ai_images_detail = st.selectbox("AI-Generated Images Details:",
                                                                options=ai_image_options, index=ai_image_options.index(
                    st.session_state.sb_ai_images_detail), key="widget_ai_images_detail_sb")
            ai_translation_options = ["None", "Some sections, with minimal or no editing",
                                      "Some sections, with extensive editing",
                                      "Entire work, with minimal or no editing", "Entire work, with extensive editing"]
            st.session_state.sb_ai_translation_detail = st.selectbox("AI-Generated Translations Details:",
                                                                     options=ai_translation_options,
                                                                     index=ai_translation_options.index(
                                                                         st.session_state.sb_ai_translation_detail),
                                                                     key="widget_ai_translation_detail_sb")
        else:
            st.session_state.sb_ai_text_detail = "None";
            st.session_state.sb_ai_images_detail = "None";
            st.session_state.sb_ai_translation_detail = "None"

        st.subheader("Book Type")
        st.session_state.sb_is_low_content_val = st.checkbox("This is a Low-Content Book",
                                                             value=st.session_state.sb_is_low_content_val,
                                                             key="widget_is_low_content_val_sb")
        st.session_state.sb_isbn_val = st.text_input("ISBN (If applicable)", value=st.session_state.sb_isbn_val,
                                                     key="widget_isbn_val_sb")

    with st.sidebar.expander("🌍 Language & Manuscript File"):
        st.session_state.sb_selected_language_val = st.selectbox("Book Language (Metadata)", options=
        default_select_radios['sb_selected_language_val'][0], index=default_select_radios['sb_selected_language_val'][
            0].index(st.session_state.sb_selected_language_val), key="widget_selected_language_val_sb")
        st.session_state.sb_manuscript_upload_format_val = st.selectbox("Manuscript Upload Format (Intended for KDP)",
                                                                        options=default_select_radios[
                                                                            'sb_manuscript_upload_format_val'][0],
                                                                        index=default_select_radios[
                                                                            'sb_manuscript_upload_format_val'][0].index(
                                                                            st.session_state.sb_manuscript_upload_format_val),
                                                                        key="widget_manuscript_upload_format_val_sb")
        st.session_state.sb_uploaded_manuscript_file = st.file_uploader(
            "Upload Manuscript (.txt, .docx, .pdf, .epub, .html)",
            type=['txt', 'docx', 'pdf', 'epub', 'html', 'htm', 'xhtml'], key="widget_manuscript_file_sb")

        if st.session_state.sb_uploaded_manuscript_file:
            if st.session_state.get('last_uploaded_filename') != st.session_state.sb_uploaded_manuscript_file.name or \
                    'extracted_manuscript_text' not in st.session_state:
                with st.spinner(f"Extracting text..."):
                    st.session_state.extracted_manuscript_text = extract_text_from_file(
                        st.session_state.sb_uploaded_manuscript_file)
                    st.session_state.last_uploaded_filename = st.session_state.sb_uploaded_manuscript_file.name
                if st.session_state.extracted_manuscript_text and not st.session_state.extracted_manuscript_text.startswith(
                        "Error:") and not st.session_state.extracted_manuscript_text.startswith("Warning:"):
                    st.sidebar.success(f"Extracted {len(st.session_state.extracted_manuscript_text)} chars.")
                elif st.session_state.extracted_manuscript_text.startswith(
                        "Error:") or st.session_state.extracted_manuscript_text.startswith("Warning:"):
                    st.sidebar.warning(st.session_state.extracted_manuscript_text)
                elif st.session_state.sb_uploaded_manuscript_file:
                    st.sidebar.warning(f"Could not extract text or file was empty/unsupported.")
        elif 'extracted_manuscript_text' in st.session_state:
            del st.session_state.extracted_manuscript_text
            if 'last_uploaded_filename' in st.session_state: del st.session_state.last_uploaded_filename

    current_book_format_for_expander = st.session_state.get("sb_book_format", "eBook")
    with st.sidebar.expander("📏 Print Formatting (Paperback/Hardcover)",
                             expanded=(current_book_format_for_expander != "eBook")):
        st.write("Fill if creating Paperback/Hardcover.")
        st.session_state.sb_trim_size_selection_val = st.selectbox("Trim Size", options=
        default_select_radios['sb_trim_size_selection_val'][0], index=
                                                                   default_select_radios['sb_trim_size_selection_val'][
                                                                       0].index(
                                                                       st.session_state.sb_trim_size_selection_val),
                                                                   key="widget_trim_size_selection_val_sb")
        st.session_state.sb_ink_paper_type_selection_val = st.selectbox("Ink & Paper Type",
                                                                        options=updated_ink_paper_options,
                                                                        index=updated_ink_paper_options.index(
                                                                            st.session_state.sb_ink_paper_type_selection_val),
                                                                        key="widget_ink_paper_type_selection_val_sb")
        st.session_state.sb_page_count_input_val = st.text_input("Final Page Count (approx.)",
                                                                 value=st.session_state.sb_page_count_input_val,
                                                                 key="widget_page_count_input_val_sb")
        st.session_state.sb_interior_bleed_selection_val = st.radio("Interior Pages Have Bleed?", default_select_radios[
            'sb_interior_bleed_selection_val'][0], index=default_select_radios['sb_interior_bleed_selection_val'][
            0].index(st.session_state.sb_interior_bleed_selection_val), key="widget_interior_bleed_selection_val_sb")

    # --- Action Buttons ---
    col1, col2 = st.sidebar.columns(2)
    with col1:
        validate_clicked = st.button("✨ Validate with Sentinel AI", key="validate_button", use_container_width=True)
    with col2:
        if st.button("🧹 Clear All Inputs", key="clear_inputs_button", use_container_width=True):
            for key in default_text_inputs: st.session_state[key] = ""
            for key in default_bool_inputs: st.session_state[key] = False
            for key, (options, default) in default_select_radios.items(): st.session_state[key] = default
            for key_list_name, length in list_inputs.items(): st.session_state[key_list_name] = [""] * length
            st.session_state.sb_min_reading_age_num_val = 0
            st.session_state.sb_max_reading_age_num_val = 0
            st.session_state.widget_manuscript_file_sb = None  # Clears the file uploader widget
            if 'extracted_manuscript_text' in st.session_state: del st.session_state.extracted_manuscript_text
            if 'last_uploaded_filename' in st.session_state: del st.session_state.last_uploaded_filename
            st.session_state.validation_results_grouped = {};
            st.session_state.ai_analysis_feedbacks = {}
            st.session_state.error_count = 0;
            st.session_state.warning_count = 0
            if 'json_inputs_to_share' in st.session_state: del st.session_state.json_inputs_to_share
            st.session_state.json_load_area = ""
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Save/Load Input State")
    if st.sidebar.button("🔗 Generate Sharable Input Data", key="generate_json_button"):
        serializable_inputs = {}
        for key, value in st.session_state.items():
            if key.startswith("sb_"):
                if key == "sb_uploaded_manuscript_file":  # Exclude the file object
                    if value is not None: serializable_inputs[key + "_name_info"] = value.name
                    continue
                try:
                    json.dumps({key: value})  # Test serializability
                    serializable_inputs[key] = value
                except TypeError:
                    serializable_inputs[key] = f"UNSERIALIZABLE_OBJECT_TYPE_{type(value).__name__}"
        if serializable_inputs:
            st.session_state.json_inputs_to_share = json.dumps(serializable_inputs, indent=2, default=str)
            st.toast("Input data generated for sharing!")
        else:
            st.toast("No inputs to generate data from.", icon="ℹ️")

    if 'json_inputs_to_share' in st.session_state and st.session_state.json_inputs_to_share:
        st.sidebar.text_area("Copy this data:", value=st.session_state.json_inputs_to_share, height=150,
                             key="json_display_area")
    json_inputs_to_load = st.sidebar.text_area("Paste saved input data here to load:", height=100, key="json_load_area")
    if st.sidebar.button("📥 Load Inputs from Data", key="load_json_button"):
        if json_inputs_to_load:
            try:
                loaded_inputs = json.loads(json_inputs_to_load)
                for key, value in loaded_inputs.items():
                    if key.startswith("sb_") and key in st.session_state and not key.endswith("_name_info") and \
                            (not isinstance(value, str) or not value.startswith("UNSERIALIZABLE_OBJECT_TYPE_")):
                        st.session_state[key] = value
                st.sidebar.success("Inputs loaded successfully! Please re-upload any manuscript files if needed.")
                if 'json_inputs_to_share' in st.session_state: del st.session_state.json_inputs_to_share
                st.session_state.json_load_area = ""
                st.rerun()
            except json.JSONDecodeError:
                st.sidebar.error("Invalid data format.")
            except Exception as e:
                st.sidebar.error(f"Error loading inputs: {e}")
        else:
            st.sidebar.warning("Paste data into the area above before loading.")

    if validate_clicked:
        s = st.session_state
        s.error_count = 0;
        s.warning_count = 0
        s.validation_results_grouped = {
            "Core Details & Cover": [], "Translation Information": [], "Public Domain": [],
            "Description & Basic HTML": [], "Categories & Keywords (Rules)": [], "Series Information": [],
            "Audience, Type & AI Declaration": [], "Language & Manuscript File (Rules)": [],
            "Print Formatting Guidance": [],
        }
        s.ai_analysis_feedbacks = {
            "Content Guidelines (AI)": [], "Manuscript General Quality (AI)": [],
            "Manuscript Typos, Placeholders & Accessibility (AI)": [],
            "Manuscript Links & Duplicated Text (AI)": [],
            "Disappointing Content (AI)": [], "Public Domain Differentiation (AI)": [],
            "Description (AI)": [], "Keywords (AI)": [], "Categories (AI)": [],
            "Manuscript Language (AI)": [], "Manuscript Offensive Content (AI)": []
        }

        # --- Perform Rule-Based Validations ---
        s.validation_results_grouped["Core Details & Cover"].extend(
            validate_title_and_subtitle(s.sb_book_title_meta, s.sb_subtitle_meta))
        s.validation_results_grouped["Core Details & Cover"].extend(validate_author_name_rules(s.sb_author_name_meta))
        s.validation_results_grouped["Core Details & Cover"].extend(
            validate_cover_text_match_rules(s.sb_title_on_cover, s.sb_author_on_cover, s.sb_book_title_meta,
                                            s.sb_author_name_meta))
        s.validation_results_grouped["Translation Information"].extend(
            validate_translation_info_rules(s.sb_is_translation, s.sb_original_author_translation,
                                            s.sb_translator_name_translation))
        s.validation_results_grouped["Public Domain"].extend(
            validate_public_domain_differentiation_rules(s.sb_is_public_domain, s.sb_description_text,
                                                         s.get("sb_public_domain_differentiation_statement", "")))
        s.validation_results_grouped["Description & Basic HTML"].extend(
            validate_description_basic_html_rules(s.sb_description_text))
        s.validation_results_grouped["Categories & Keywords (Rules)"].extend(
            validate_categories_rules(s.sb_categories_input_list))
        s.validation_results_grouped["Categories & Keywords (Rules)"].extend(
            validate_keywords_rules(s.sb_keywords_input_list))
        s.validation_results_grouped["Series Information"].extend(
            validate_series_info_rules(s.sb_is_series_val, s.sb_series_name_val, s.sb_series_number_str_val,
                                       s.sb_is_low_content_val, s.sb_is_public_domain))
        s.validation_results_grouped["Audience, Type & AI Declaration"].extend(
            validate_primary_audience_rules(s.sb_sexually_explicit_val, s.sb_min_reading_age_num_val,
                                            s.sb_max_reading_age_num_val, s.sb_categories_input_list))
        s.validation_results_grouped["Audience, Type & AI Declaration"].extend(
            validate_isbn_rules(s.sb_isbn_val, s.sb_is_low_content_val, s.sb_book_format))
        s.validation_results_grouped["Audience, Type & AI Declaration"].extend(
            validate_ai_content_declaration_rules(s.sb_ai_used_any, s.get("sb_ai_text_detail", "None"),
                                                  s.get("sb_ai_images_detail", "None"),
                                                  s.get("sb_ai_translation_detail", "None")))
        s.validation_results_grouped["Audience, Type & AI Declaration"].extend(
            validate_low_content_implications_rules(s.sb_is_low_content_val))
        s.validation_results_grouped["Language & Manuscript File (Rules)"].extend(
            validate_language_and_format_rules(s.sb_selected_language_val, s.sb_book_format,
                                               s.sb_manuscript_upload_format_val))
        if s.sb_book_format in ["Paperback", "Hardcover"]:
            if s.sb_trim_size_selection_val != "Select Trim Size" and s.sb_page_count_input_val and s.sb_ink_paper_type_selection_val != "Select Ink/Paper":
                s.validation_results_grouped["Print Formatting Guidance"].extend(
                    calculate_and_display_print_specs_rules(s.sb_trim_size_selection_val, s.sb_page_count_input_val,
                                                            s.sb_interior_bleed_selection_val,
                                                            s.sb_ink_paper_type_selection_val, s.sb_book_format))
            else:
                s.validation_results_grouped["Print Formatting Guidance"].append(
                    "⚠️ Provide Trim Size, Page Count, & Ink/Paper Type for full print guidance.")

        # --- AI Analyses ---
        progress_bar_placeholder = st.empty()
        progress_bar = progress_bar_placeholder.progress(0)
        man_text = s.get("extracted_manuscript_text", "")

        ai_task_conditions_map = {
            "Content Guidelines (AI) - Infringing": (s.sb_book_title_meta or s.sb_description_text),
            "Content Guidelines (AI) - MisleadingDesc": (s.sb_description_text and man_text),
            "Content Guidelines (AI) - FreelyAvail": bool(man_text),
            "Disappointing Content (AI)": (man_text or s.sb_description_text),
            "Manuscript Typos, Placeholders & Accessibility (AI)": bool(man_text),
            "Manuscript General Quality (AI)": bool(man_text),
            "Manuscript Links & Duplicated Text (AI)": bool(man_text),
            "Public Domain Differentiation (AI)": (
                        s.sb_is_public_domain and s.get("sb_public_domain_differentiation_statement", "").strip()),
            "Description (AI)": bool(s.sb_description_text),
            "Keywords (AI)": any(k.strip() for k in s.sb_keywords_input_list),
            "Categories (AI)": any(c.strip() for c in s.sb_categories_input_list),
            "Manuscript Language (AI)": bool(man_text and len(man_text) > 50),
            "Manuscript Offensive Content (AI)": bool(man_text)
        }
        # Filter to only include tasks that will actually run for accurate progress
        tasks_that_will_run = {k: v for k, v in ai_task_conditions_map.items() if v}
        total_ai_tasks = len(tasks_that_will_run)
        if total_ai_tasks == 0: total_ai_tasks = 1  # Avoid division by zero
        completed_ai_tasks = 0

        def run_ai_task_and_update_progress(task_func, feedback_key, condition_to_run_flag, *args):
            nonlocal completed_ai_tasks
            if condition_to_run_flag:
                feedback = task_func(*args)
                if feedback:
                    substantive_feedback = [msg for msg in feedback if
                                            isinstance(msg, str) and msg.strip() and not msg.startswith("ℹ️")]
                    if substantive_feedback:
                        s.ai_analysis_feedbacks[feedback_key].extend(substantive_feedback)
                    elif feedback:
                        s.ai_analysis_feedbacks[feedback_key].extend(feedback)
                completed_ai_tasks += 1
            # Update progress based on tasks that were *supposed* to run
            if total_ai_tasks > 0:
                progress_bar.progress(min(1.0, completed_ai_tasks / total_ai_tasks))
            else:
                progress_bar.progress(1.0)  # Should not happen if total_ai_tasks is at least 1

        with st.spinner("Performing AI Analyses... This may take a moment."):
            run_ai_task_and_update_progress(ai_check_infringing_content, "Content Guidelines (AI)",
                                            tasks_that_will_run.get("Content Guidelines (AI) - Infringing", False),
                                            s.sb_book_title_meta, s.sb_subtitle_meta, s.sb_description_text)
            run_ai_task_and_update_progress(ai_check_misleading_description, "Content Guidelines (AI)",
                                            tasks_that_will_run.get("Content Guidelines (AI) - MisleadingDesc", False),
                                            s.sb_description_text, man_text)
            run_ai_task_and_update_progress(ai_check_freely_available_content, "Content Guidelines (AI)",
                                            tasks_that_will_run.get("Content Guidelines (AI) - FreelyAvail", False),
                                            man_text)
            run_ai_task_and_update_progress(ai_check_disappointing_content_issues, "Disappointing Content (AI)",
                                            tasks_that_will_run.get("Disappointing Content (AI)", False), man_text,
                                            s.sb_description_text, s.sb_is_translation)
            run_ai_task_and_update_progress(ai_check_manuscript_typos_placeholders_accessibility,
                                            "Manuscript Typos, Placeholders & Accessibility (AI)",
                                            tasks_that_will_run.get(
                                                "Manuscript Typos, Placeholders & Accessibility (AI)", False), man_text)
            run_ai_task_and_update_progress(ai_check_manuscript_general_quality_issues,
                                            "Manuscript General Quality (AI)",
                                            tasks_that_will_run.get("Manuscript General Quality (AI)", False), man_text)

            if tasks_that_will_run.get("Manuscript Links & Duplicated Text (AI)", False):
                links_dupes_feedback_list = []
                links_dupes_feedback_list.extend(ai_check_links_in_manuscript(man_text))
                links_dupes_feedback_list.extend(ai_check_duplicated_text_in_manuscript(man_text))
                if links_dupes_feedback_list and any(
                        msg.strip() and not msg.startswith("ℹ️") for msg in links_dupes_feedback_list):
                    s.ai_analysis_feedbacks["Manuscript Links & Duplicated Text (AI)"].extend(links_dupes_feedback_list)
                elif not links_dupes_feedback_list and bool(man_text):
                    s.ai_analysis_feedbacks["Manuscript Links & Duplicated Text (AI)"].append(
                        "ℹ️ No specific issues flagged for links or duplicated text by AI.")
                elif not bool(man_text):
                    s.ai_analysis_feedbacks["Manuscript Links & Duplicated Text (AI)"].append(
                        "ℹ️ No manuscript text provided for link/duplication analysis.")
                completed_ai_tasks += 1;
                progress_bar.progress(min(1.0, completed_ai_tasks / total_ai_tasks))

            if tasks_that_will_run.get("Public Domain Differentiation (AI)", False):
                run_ai_task_and_update_progress(ai_check_public_domain_differentiation,
                                                "Public Domain Differentiation (AI)", True, s.sb_is_public_domain,
                                                s.get("sb_public_domain_differentiation_statement", ""))

            if tasks_that_will_run.get("Description (AI)", False):
                prompt_desc = f"""Analyze KDP book description for:
                1. Spelling/grammar errors (bullet list, max 5, with specific suggestions for correction if possible).
                2. Clarity/professionalism (target ~150 words prose, concise feedback, suggest specific improvements if vague or not compelling).
                3. KDP HTML: List ALL tags used, state if KDP-supported (<br>,<p>,<b>,<em>,<i>,<u>,<h4>-<h6>,<ol><li>,<ul><li>), note unsupported (NO h1-h3). Suggest valid KDP-supported alternatives for any unsupported tags identified.
                4. Formatting issues: e.g., double spaces between words, misuse of angle brackets (suggest specific fixes).
                5. Character count including HTML (state the count clearly).
                Return feedback as a well-structured response with clear headings and bullet points for each identified issue. If no issues for a point, state that.
                Desc: --- {s.sb_description_text} ---"""
                s.ai_analysis_feedbacks["Description (AI)"].append(
                    invoke_claude_model(prompt_desc) or "Could not get feedback for description.")
            else:
                s.ai_analysis_feedbacks["Description (AI)"].append("ℹ️ No description provided for AI analysis.")
            if tasks_that_will_run.get("Description (AI)", False) or not s.ai_analysis_feedbacks[
                "Description (AI)"]: completed_ai_tasks += 1; progress_bar.progress(
                min(1.0, completed_ai_tasks / total_ai_tasks))

            if tasks_that_will_run.get("Keywords (AI)", False):
                keyword_str = "; ".join(k for k in s.sb_keywords_input_list if k.strip())
                prompt_kw = f"""Analyze KDP keywords: "{keyword_str}" for book "{s.sb_book_title_meta}", desc: "{s.sb_description_text[:100]}...".
                Check for (bullet points per issue, suggest specific actionable alternatives if a keyword is problematic but intent is clear): Redundancy with title/desc, Subjective Claims (e.g., "best"), Time-sensitive terms (e.g., "new"), Generic terms if used alone (e.g., "book"), Misleading info.
                If all keywords seem appropriate, state that clearly.
                """
                s.ai_analysis_feedbacks["Keywords (AI)"].append(
                    invoke_claude_model(prompt_kw) or "Could not get feedback for keywords.")
            else:
                s.ai_analysis_feedbacks["Keywords (AI)"].append("ℹ️ No keywords provided for AI analysis.")
            if tasks_that_will_run.get("Keywords (AI)", False) or not s.ai_analysis_feedbacks[
                "Keywords (AI)"]: completed_ai_tasks += 1; progress_bar.progress(
                min(1.0, completed_ai_tasks / total_ai_tasks))

            if tasks_that_will_run.get("Categories (AI)", False):
                cat_str = "; ".join(c for c in s.sb_categories_input_list if c.strip())
                prompt_cat = f"""Analyze KDP categories: "{cat_str}" for book "{s.sb_book_title_meta}", desc: "{s.sb_description_text[:100]}...".
                Check for (bullet points): Relevance to title/description, Obvious mismatches with genre/content, Categories too broad or too niche.
                If categories seem mismatched, suggest 1-2 more appropriate KDP-style category examples based on the provided info. If categories seem appropriate, state that.
                """
                s.ai_analysis_feedbacks["Categories (AI)"].append(
                    invoke_claude_model(prompt_cat) or "Could not get feedback for categories.")
            else:
                s.ai_analysis_feedbacks["Categories (AI)"].append("ℹ️ No categories provided for AI analysis.")
            if tasks_that_will_run.get("Categories (AI)", False) or not s.ai_analysis_feedbacks[
                "Categories (AI)"]: completed_ai_tasks += 1; progress_bar.progress(
                min(1.0, completed_ai_tasks / total_ai_tasks))

            if tasks_that_will_run.get("Manuscript Language (AI)", False):
                prompt_lang = f"Primary language of text (respond only with language name): \"\"\"{man_text[:1000]}\"\"\""
                detected_lang = invoke_claude_model(prompt_lang, max_tokens=50)
                if detected_lang and not detected_lang.startswith("Error:") and not detected_lang.startswith(
                        "Informational:"):
                    detected_lang = detected_lang.strip().rstrip('.')
                    if s.sb_selected_language_val.lower() not in detected_lang.lower() and detected_lang.lower() not in s.sb_selected_language_val.lower():
                        s.ai_analysis_feedbacks["Manuscript Language (AI)"].append(
                            f"⚠️ **AI Mismatch:** Metadata: '{s.sb_selected_language_val}', AI detected: '{detected_lang}'.")
                    else:
                        s.ai_analysis_feedbacks["Manuscript Language (AI)"].append(
                            f"✅ **AI Check:** Detected '{detected_lang}' consistent with metadata '{s.sb_selected_language_val}'.")
                elif detected_lang:
                    s.ai_analysis_feedbacks["Manuscript Language (AI)"].append(detected_lang)
                else:
                    s.ai_analysis_feedbacks["Manuscript Language (AI)"].append(
                        "⚠️ Could not detect manuscript language via AI.")
            elif man_text:
                s.ai_analysis_feedbacks["Manuscript Language (AI)"].append(
                    "ℹ️ Manuscript text too short for reliable AI language detection.")
            else:
                s.ai_analysis_feedbacks["Manuscript Language (AI)"].append(
                    "ℹ️ No manuscript uploaded for AI language detection.")
            if tasks_that_will_run.get("Manuscript Language (AI)", False) or not s.ai_analysis_feedbacks[
                "Manuscript Language (AI)"]: completed_ai_tasks += 1; progress_bar.progress(
                min(1.0, completed_ai_tasks / total_ai_tasks))

            if tasks_that_will_run.get("Manuscript Offensive Content (AI)", False):
                prompt_off = f"""Analyze text (up to 1st 2000 chars) for KDP offensive content (hate speech, child exploitation, pornography, glorifies rape/pedophilia, terrorism).
                If issues: provide specific text snippet, suspected violation category, and brief explanation as bullet points. If none, state clearly "No offensive content identified in this snippet." """
                s.ai_analysis_feedbacks["Manuscript Offensive Content (AI)"].append(
                    invoke_claude_model(prompt_off) or "Could not perform scan.")
            else:
                s.ai_analysis_feedbacks["Manuscript Offensive Content (AI)"].append(
                    "ℹ️ No manuscript uploaded for AI offensive content scan.")
            if tasks_that_will_run.get("Manuscript Offensive Content (AI)", False) or not s.ai_analysis_feedbacks[
                "Manuscript Offensive Content (AI)"]: completed_ai_tasks += 1; progress_bar.progress(
                min(1.0, completed_ai_tasks / total_ai_tasks))

            # Ensure progress bar completes visually if all tasks accounted for
            if completed_ai_tasks >= total_ai_tasks: progress_bar.progress(1.0)
            progress_bar_placeholder.empty()

    # --- Display Results ---
    # (Same display logic as before)
    if 'validation_results_grouped' in st.session_state and st.session_state.validation_results_grouped:
        st.header("📊 Validation Report")
        s = st.session_state

        s.error_count = 0;
        s.warning_count = 0
        for section_messages in s.validation_results_grouped.values():
            for msg in section_messages:
                if isinstance(msg, str):
                    if "❌" in msg:
                        s.error_count += 1
                    elif "⚠️" in msg:
                        s.warning_count += 1

        # Submission Readiness Indicator
        if s.error_count > 2 or s.warning_count > 5:
            st.error("🔴 **High Risk of Rejection:** Significant errors or multiple warnings. Address all ❌ & ⚠️ items.")
        elif s.error_count > 0:
            st.warning("🟠 **Moderate Risk:** Errors ❌ found. Must be addressed. Review warnings ⚠️.")
        elif s.warning_count > 0:
            st.warning("🟡 **Low Risk:** Some warnings ⚠️ found. Please review carefully.")
        else:
            st.success("🟢 **Looking Good (Rule-Based Checks):** No immediate errors or warnings from automated rules.")
        st.markdown(
            "This is a heuristic indicator. *Always review all feedback sections below, especially AI-powered analyses, before submitting to KDP.*")

        st.markdown("---")
        if st.button("🗓️ Need More Help? Book an Appointment with a Publishing Expert (Internal Only)",
                     key="appt_button"):
            st.info(
                "✨ **Feature Coming Soon!** For now, please consult the KDP guidelines or reach out to internal support channels for complex queries.")
        st.markdown("---")
        st.markdown(
            "💡 **Amazon Q Business Integration Idea:** Sentinel AI's findings and the underlying KDP guidelines could power an internal Amazon Q Business application. This would allow support teams to quickly query specific KDP policies, understand common publisher issues flagged by Sentinel AI, and get AI-assisted guidance on resolving complex cases, boosting operational efficiency.")
        st.markdown("---")

        for section, messages in s.validation_results_grouped.items():
            if messages:
                expanded_rules = ("❌" in "".join(str(m) for m in messages if isinstance(m, str)) or "⚠️" in "".join(
                    str(m) for m in messages if isinstance(m, str)))
                with st.expander(f"📋 Rule-Based: {section} ({len(messages)} item(s))", expanded=expanded_rules):
                    for msg_content in messages:
                        if isinstance(msg_content, str):
                            if "❌" in msg_content:
                                st.error(msg_content)
                            elif "⚠️" in msg_content:
                                st.warning(msg_content)
                            elif "✅" in msg_content:
                                st.success(msg_content)
                            else:
                                st.info(msg_content)
                        else:
                            st.write(msg_content)

        if 'ai_analysis_feedbacks' in s and s.ai_analysis_feedbacks:
            has_substantive_ai_feedback = any(
                any(isinstance(m, str) and m.strip() and not m.startswith("ℹ️") for m in msg_list)
                for msg_list in s.ai_analysis_feedbacks.values() if msg_list
            )
            with st.expander("🤖 AI-Powered Deep Analysis",
                             expanded=has_substantive_ai_feedback or s.error_count > 0 or s.warning_count > 0):
                for ai_section_title, ai_messages_list in s.ai_analysis_feedbacks.items():
                    if ai_messages_list:
                        substantive_messages_in_section = [m for m in ai_messages_list if
                                                           isinstance(m, str) and m.strip() and not m.startswith("ℹ️")]
                        info_messages_in_section = [m for m in ai_messages_list if
                                                    isinstance(m, str) and m.startswith("ℹ️")]
                        if substantive_messages_in_section:
                            st.subheader(f"{ai_section_title.replace(' (AI)', '').replace('(AI)', '').strip()}")
                            for ai_msg_idx, ai_msg_content in enumerate(substantive_messages_in_section):
                                if isinstance(ai_msg_content, str) and ai_msg_content.strip():
                                    st.text_area(f"AI Feedback {ai_msg_idx + 1}", value=ai_msg_content.strip(),
                                                 height=200 if len(ai_msg_content) < 400 else 300, disabled=True,
                                                 key=f"ai_{ai_section_title.replace(' ', '_').replace('(', '').replace(')', '')}_{ai_msg_idx}")
                            if info_messages_in_section:
                                for info_msg in info_messages_in_section: st.info(info_msg)
                            st.markdown("---")
                        elif info_messages_in_section:
                            with st.expander(
                                    f"{ai_section_title.replace(' (AI)', '').replace('(AI)', '').strip()} - Notes",
                                    expanded=False):
                                for info_msg in info_messages_in_section: st.info(info_msg)

        if s.error_count == 0 and s.warning_count == 0 and not has_substantive_ai_feedback:
            st.balloons()
            st.success(
                "🎉 Excellent! All checks look good based on current input and AI analysis did not flag major concerns. Please give a final manual review before submitting.")
        elif s.error_count == 0 and s.warning_count == 0 and has_substantive_ai_feedback:
            st.success(
                "✅ Rule-based checks passed! Please carefully review the detailed AI analysis sections for further insights and potential improvements.")


if __name__ == "__main__":
    main()