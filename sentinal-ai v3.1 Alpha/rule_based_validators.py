# rule_based_validators.py
import re
from kdp_data import (
    PROHIBITED_TITLE_KEYWORDS, TITLE_PLACEHOLDERS, SUPPORTED_HTML_TAGS_DESCRIPTION,
    PROHIBITED_KEYWORD_TERMS, EBOOK_ONLY_LANGS, PRINT_ONLY_LANGS_GENERAL,
    JAPANESE_FORMAT_RESTRICTIONS, HEBREW_RESTRICTIONS, YIDDISH_RESTRICTIONS,
    PDF_SUPPORTED_LANGS_FOR_UPLOAD, MARGIN_MINIMUMS, AI_TEXT_OPTIONS, AI_TRANSLATION_OPTIONS, AI_IMAGE_OPTIONS
)  # Import necessary data from kdp_data.py

# --- Helper for Regex based keyword checks ---
def check_for_prohibited_terms(text_to_check, prohibited_list, field_name_for_msg, guideline_ref, allow_partial_phrase_match=False):
    results = []
    text_lower = text_to_check.lower()
    for term in prohibited_list:
        # Use word boundaries for most terms to avoid partial matches like "free" in "freedom"
        # unless allow_partial_phrase_match is True (e.g. for "summary of")
        pattern = r'\b' + re.escape(term) + r'\b'
        if allow_partial_phrase_match and " " in term: # For phrases, don't require word boundary at start/end of phrase itself
            pattern = re.escape(term)

        if re.search(pattern, text_lower):
            # Special handling for generic keywords like "notebook" in titles if it's part of a longer, legitimate title
            if field_name_for_msg.startswith("Title") and term in ["notebook", "journal", "gifts", "books"]:
                if text_lower.count(term) == 1 and len(text_lower.split()) > 3: # Arbitrary: allow if title has more than 3 words
                    continue # Skip flagging as prohibited if it's a single occurrence in a longer title
            results.append(f"⚠️ **{field_name_for_msg}:** Contains potentially problematic term '{term}'. Review {guideline_ref} for appropriate usage.")
    return results

# --- Core Details & Cover ---
def validate_title_and_subtitle(title, subtitle, guideline_ref="Guideline 2, 7"):
    results = []
    if not title:
        results.append(f"❌ **Title:** Title is missing. Mandatory. {guideline_ref}")
    else:
        if len(title) + len(subtitle) > 200:
            results.append(f"❌ **Title/Subtitle Length:** Combined length ({len(title) + len(subtitle)}) exceeds 200 chars. {guideline_ref}")

        combined_title_text = title + (" " + subtitle if subtitle else "")
        results.extend(check_for_prohibited_terms(combined_title_text, PROHIBITED_TITLE_KEYWORDS, "Title/Subtitle", guideline_ref, allow_partial_phrase_match=True))

        if re.search(r'<[^>]+>', combined_title_text):
            results.append(f"❌ **Title/Subtitle Content:** Contains HTML tags. Not allowed. {guideline_ref}")
        if re.fullmatch(r'[^\w\s]+', title) or (subtitle and re.fullmatch(r'[^\w\s]+', subtitle)): # Checks if ONLY punctuation
            results.append(f"❌ **Title/Subtitle Content:** Consists only of punctuation. {guideline_ref}")
        if title.lower() in TITLE_PLACEHOLDERS or (subtitle and subtitle.lower() in TITLE_PLACEHOLDERS):
            results.append(f"❌ **Title/Subtitle Content:** Uses placeholder text (e.g., 'unknown', 'untitled'). {guideline_ref}")
    if not results and title:
        results.append("✅ **Title/Subtitle:** Basic checks passed.")
    return results

def validate_author_name(author_name, guideline_ref="Guideline 7"):
    results = []
    if not author_name:
        results.append(f"❌ **Author Name:** Primary author name is missing. Mandatory and cannot be changed after publishing. {guideline_ref}")
    else:
        if re.search(r'<[^>]+>', author_name):
            results.append(f"❌ **Author Name:** Contains HTML tags. Not allowed. {guideline_ref}")
        # This regex is permissive; KDP might be stricter. It allows letters (incl. accented), numbers, space, dot, hyphen, apostrophe.
        if not re.fullmatch(r"^[a-zA-Z0-9À-ÖØ-öø-ÿĀ-žḀ-ỿ\s.'-]+$", author_name):
            results.append(f"⚠️ **Author Name:** Contains characters beyond typical letters, numbers, spaces, periods, hyphens, or apostrophes. Please review carefully. {guideline_ref}")
    if not results and author_name:
        results.append("✅ **Author Name:** Basic checks passed.")
    return results

def validate_cover_text_match(title_on_cover, author_on_cover, metadata_title, metadata_author, guideline_ref="Guideline 2, 4, 12"):
    results = []
    # Only run checks if metadata is provided, otherwise too many false positives
    if metadata_title and title_on_cover and title_on_cover.strip().lower() != metadata_title.strip().lower():
        results.append(f"⚠️ **Cover Text Mismatch (Title):** Cover ('{title_on_cover}') does not exactly match metadata ('{metadata_title}'). Must match. {guideline_ref}")
    if metadata_author and author_on_cover and author_on_cover.strip().lower() != metadata_author.strip().lower():
        results.append(f"⚠️ **Cover Text Mismatch (Author):** Cover ('{author_on_cover}') does not exactly match metadata ('{metadata_author}'). Must match. {guideline_ref}")

    if not title_on_cover and metadata_title:
        results.append(f"ℹ️ **Cover Text (Title):** Metadata title '{metadata_title}' provided, but no title text from cover was entered for comparison.")
    if not author_on_cover and metadata_author:
        results.append(f"ℹ️ **Cover Text (Author):** Metadata author '{metadata_author}' provided, but no author text from cover was entered for comparison.")

    if not results and (title_on_cover or author_on_cover) and (metadata_title or metadata_author) : # Only give success if something was actually checked
         results.append("✅ **Cover Text Match:** Provided cover text appears consistent with metadata (if both were entered).")
    elif not title_on_cover and not author_on_cover:
        results.append("ℹ️ **Cover Text Match:** No cover text entered for comparison.")
    return results


# --- Content & Marketing ---
def validate_description_html(description, guideline_ref="Guideline 10"):
    results = []
    if not description:
        return ["ℹ️ **Description HTML:** No description provided for HTML check."]

    # Find all tags
    found_tags = re.findall(r"<(/?)(\w+)[^>]*>", description) # Extracts tag name from <tag> or </tag>
    used_tag_names = {tag_info[1].lower() for tag_info in found_tags}

    unsupported_found = []
    for tag_name in used_tag_names:
        if tag_name not in SUPPORTED_HTML_TAGS_DESCRIPTION:
            unsupported_found.append(tag_name)

    if unsupported_found:
        results.append(f"❌ **Description HTML:** Found unsupported HTML tags: {', '.join(sorted(list(set(unsupported_found))))}. Supported tags are: {', '.join(SUPPORTED_HTML_TAGS_DESCRIPTION)}. {guideline_ref}")

    # Check for common h1-h3 misuse
    if any(h_tag in used_tag_names for h_tag in ["h1", "h2", "h3"]):
        results.append(f"❌ **Description HTML:** Found h1, h2, or h3 tags. These are NOT supported. Use h4, h5, or h6. {guideline_ref}")

    # Basic check for unclosed common tags (simplified)
    common_formatting_tags = ['b', 'i', 'em', 'u', 'p', 'h4', 'h5', 'h6']
    for tag in common_formatting_tags:
        open_tags = len(re.findall(f"<{tag}[^>]*>", description.lower()))
        close_tags = len(re.findall(f"</{tag}>", description.lower()))
        if open_tags > close_tags:
            results.append(f"⚠️ **Description HTML:** Potential unclosed '<{tag}>' tag(s). Ensure all tags are properly closed. {guideline_ref}")
        elif close_tags > open_tags:
            results.append(f"⚠️ **Description HTML:** Potential extra closing '</{tag}>' tag(s) without an opening tag. {guideline_ref}")

    # Angle bracket misuse checks from Guideline 10
    if re.search(r"< \w+", description): # < text
        results.append(f"❌ **Description HTML:** Found pattern '< text' (space after opening bracket). Not allowed. {guideline_ref}")
    if re.search(r"<<|>>", description): # << OR >>
        results.append(f"❌ **Description HTML:** Found '<<' or '>>'. Not allowed. {guideline_ref}")
    if re.search(r"<>", description): # <>
        results.append(f"❌ **Description HTML:** Found pattern '<>'. Not allowed. {guideline_ref}")

    char_count = len(description)
    results.append(f"ℹ️ **Description Character Count (incl. HTML):** {char_count} characters.")
    if char_count > 4000: # KDP limit is typically 4000 chars
         results.append(f"❌ **Description Length:** {char_count} characters. Exceeds KDP's typical limit of 4000 characters (including HTML). {guideline_ref}")

    if not results:
        results.append("✅ **Description HTML:** Basic HTML checks passed.")
    return results

def validate_categories(categories_list, guideline_ref="Guideline 2, 11"):
    results = []
    filled_categories = [c.strip() for c in categories_list if c.strip()]
    if len(filled_categories) > 3:
        results.append(f"❌ **Categories Count:** {len(filled_categories)} selected. KDP allows up to 3. {guideline_ref}")
    if not filled_categories:
        results.append(f"ℹ️ **Categories:** No categories provided. Crucial for discoverability. {guideline_ref}")
    else:
        results.append(f"✅ **Categories Count:** {len(filled_categories)} categories provided (max 3 allowed).")
    return results

def validate_keywords(keywords_list, title="", subtitle="", categories_list=None, guideline_ref="Guideline 9, 10"):
    if categories_list is None: categories_list = []
    results = []
    if not any(kw.strip() for kw in keywords_list):
        results.append(f"ℹ️ **Keywords:** No keywords provided. Crucial for discoverability. {guideline_ref}")
        return results

    filled_keywords = [k.strip() for k in keywords_list if k.strip()]
    if len(filled_keywords) > 7:
        results.append(f"❌ **Keywords Count:** {len(filled_keywords)} entered. KDP allows up to 7. {guideline_ref}")

    title.lower() + " " + subtitle.lower() + " " + " ".join(c.lower() for c in categories_list if c)

    for i, kw in enumerate(filled_keywords):
        kw_lower = kw.lower()
        if len(kw) > 50 : # KDP has a character limit per keyword field, usually around 50
            results.append(f"⚠️ **Keyword {i+1} ('{kw[:20]}...'):** Length ({len(kw)}) may exceed KDP's per-keyword field limit (typically ~50 chars). Please verify. {guideline_ref}")

        results.extend(check_for_prohibited_terms(kw, PROHIBITED_KEYWORD_TERMS, f"Keyword {i+1} ('{kw[:20]}...')", guideline_ref))

        if re.search(r'<[^>]+>', kw):
            results.append(f"❌ **Keyword {i+1} ('{kw[:20]}...'):** Contains HTML tags. {guideline_ref}")
        if '"' in kw:
            results.append(f"⚠️ **Keyword {i+1} ('{kw[:20]}...'):** Contains quotation marks. Generally not recommended. {guideline_ref}")

        # Check for redundancy with title/subtitle/categories
        if title and kw_lower in title.lower(): # Simple check
            results.append(f"ℹ️ **Keyword {i+1} ('{kw[:20]}...'):** Appears in title. Avoid redundancy if not adding significant new context. {guideline_ref}")
        if subtitle and kw_lower in subtitle.lower():
             results.append(f"ℹ️ **Keyword {i+1} ('{kw[:20]}...'):** Appears in subtitle. Avoid redundancy. {guideline_ref}")
        for cat in categories_list:
            if cat and kw_lower in cat.lower():
                 results.append(f"ℹ️ **Keyword {i+1} ('{kw[:20]}...'):** Appears in category '{cat}'. Avoid redundancy. {guideline_ref}")
    if not results:
        results.append("✅ **Keywords:** Basic checks passed.")
    return results

def validate_series_info(is_series, series_name, series_number_str, is_low_content, is_public_domain, guideline_ref="Guideline 2, 6, 7, 11"):
    results = []
    if is_series:
        results.append("ℹ️ **Series Information:** Declared as part of a series.")
        if is_low_content:
            results.append(f"❌ **Series & Low Content:** Low-content books are not eligible for series. {guideline_ref}")
        if is_public_domain:
            results.append(f"❌ **Series & Public Domain:** Public domain books are not eligible for series. {guideline_ref}")

        if not series_name:
            results.append(f"❌ **Series Name:** Required if book is part of a series. {guideline_ref}")
        else:
            # Validate series_name using title validation rules (it must adhere to them)
            series_title_issues = validate_title_and_subtitle(series_name, "", guideline_ref="Guideline 2 (for Series Title)")
            if any("❌" in issue or "⚠️" in issue for issue in series_title_issues):
                results.append(f"--- Issues found in Series Name '{series_name}' (must follow Book Title guidelines): ---")
                results.extend(series_title_issues)
                results.append("--- End of Series Name Issues ---")
            else:
                results.append("✅ **Series Name:** Basic checks passed.")


        if series_number_str:
            if not series_number_str.isdigit():
                results.append(f"❌ **Series Number ('{series_number_str}'):** Must be digits only (e.g., '1', '2'). {guideline_ref}")
            elif series_name and re.search(r'\b' + re.escape(series_number_str) + r'\b', series_name, re.IGNORECASE):
                results.append(f"⚠️ **Series Name & Number:** Series name ('{series_name}') appears to contain the series number ('{series_number_str}'). The series name field should generally *only* contain the name of the series itself. {guideline_ref}")
            else:
                 results.append(f"✅ **Series Number:** '{series_number_str}' format looks okay (digits).")
        else:
            results.append("ℹ️ **Series Number:** Not provided. Usually required for numbered series parts.")
    return results

# --- Print Details ---
def validate_print_specs(
    trim_size_str, page_count_str, interior_bleed_str, ink_paper_type_str, book_format_str,
    KDP_PAGE_COUNT_SPECS_PAPERBACK, KDP_PAGE_COUNT_SPECS_HARDCOVER, INK_PAPER_TO_KEY_MAP,
    guideline_ref="Guideline 12, 13"
    ):
    results = []
    if book_format_str not in ["Paperback", "Hardcover"]:
        return ["ℹ️ Print specific checks not applicable for eBook format."]

    if trim_size_str == "Select Trim Size": results.append(f"❌ **Print Specs - Trim Size:** Please select a trim size. {guideline_ref}")
    if ink_paper_type_str == "Select Ink/Paper": results.append(f"❌ **Print Specs - Ink & Paper:** Please select an ink and paper type. {guideline_ref}")
    if not page_count_str: results.append(f"❌ **Print Specs - Page Count:** Page count is required. {guideline_ref}")

    if not all([trim_size_str != "Select Trim Size", ink_paper_type_str != "Select Ink/Paper", page_count_str]):
        return results # Stop if essential info is missing

    try:
        page_count = int(page_count_str)
        if page_count < 24: # Absolute minimum for any print book
            raise ValueError("Page count must be at least 24.")
    except ValueError:
        results.append(f"❌ **Print Specs - Page Count ('{page_count_str}'):** Must be a whole number, at least 24. {guideline_ref}")
        return results # Stop if page count is invalid

    has_bleed = interior_bleed_str == "Yes"
    results.append(f"ℹ️ **Print Input Summary:** Format: {book_format_str}, Trim: {trim_size_str}, Ink/Paper: {ink_paper_type_str}, Bleed: {interior_bleed_str}, Pages: {page_count}.")

    KDP_SPECS_TO_USE = KDP_PAGE_COUNT_SPECS_PAPERBACK if book_format_str == "Paperback" else KDP_PAGE_COUNT_SPECS_HARDCOVER
    ink_key_segment = INK_PAPER_TO_KEY_MAP.get(ink_paper_type_str)

    # Hardcover specific check for Standard Color (Guideline 13 states "Not available" for HC)
    if book_format_str == "Hardcover" and ink_paper_type_str == "Standard color interior with white paper":
        results.append(f"❌ **Print Specs - Ink/Paper for Hardcover:** 'Standard color interior with white paper' is generally NOT available for Hardcovers. Choose Premium Color or Black Ink. {guideline_ref}")
        ink_key_segment = None # Invalidate it for page count check

    page_count_limits_msg = f"⚠️ **Print Specs - Page Count Limits:** Could not automatically verify page count limits for '{trim_size_str}' with '{ink_paper_type_str}' ({book_format_str}). Please manually verify against KDP Guideline 13 tables."
    if trim_size_str in KDP_SPECS_TO_USE and ink_key_segment:
        limits = KDP_SPECS_TO_USE[trim_size_str].get(ink_key_segment)
        if isinstance(limits, tuple) and len(limits) == 2:
            min_pages, max_pages = limits
            if not (min_pages <= page_count <= max_pages):
                page_count_limits_msg = f"❌ **Print Specs - Page Count Error:** For {trim_size_str} ({ink_paper_type_str}, {book_format_str}), pages must be {min_pages}-{max_pages}. Your input: {page_count}. {guideline_ref}"
            else:
                page_count_limits_msg = f"✅ **Print Specs - Page Count OK:** {page_count} pages is within {min_pages}-{max_pages} for {trim_size_str} ({ink_paper_type_str}, {book_format_str})."
        elif limits == "Not available":
             page_count_limits_msg = f"❌ **Print Specs - Ink/Paper Incompatible:** The combination of {trim_size_str} and {ink_paper_type_str} for {book_format_str} is listed as 'Not available' by KDP. Please choose a different combination. {guideline_ref}"
    results.append(page_count_limits_msg)

    # Document Page Setup Size Calculation (Guideline 12, 13)
    try:
        # Simplified parsing - assumes format "W\" x H\"" or "W.XX\" x H.YY\""
        trim_parts_match = re.match(r'([0-9.]+)"?\s*x\s*([0-9.]+)"?', trim_size_str.replace(" ", ""))
        if trim_parts_match:
            width_in, height_in = float(trim_parts_match.group(1)), float(trim_parts_match.group(2))
            doc_width, doc_height = width_in, height_in
            if has_bleed:
                doc_width += 0.125  # Bleed added to one side (outside edge) for width
                doc_height += 0.250 # Bleed added to top and bottom for height
            results.append(f"✅ **Document Page Setup Size (Manuscript File):** For '{trim_size_str}' {'with bleed' if has_bleed else 'no bleed'}, set your document page size to approximately **{doc_width:.3f}\" W x {doc_height:.3f}\" H**. {guideline_ref}")
            if has_bleed:
                results.append("   Ensure all bleed elements in your manuscript extend fully to these larger page dimensions.")
        else:
            results.append(f"⚠️ **Print Specs - Page Setup Size:** Could not parse trim size '{trim_size_str}' to calculate document page dimensions. Please calculate manually per Guideline 13.")
    except Exception:
        results.append(f"⚠️ **Print Specs - Page Setup Size Calc Error:** Error calculating document page dimensions for '{trim_size_str}'. Please calculate manually per Guideline 13.")


    # Margin calculation
    inside_margin_val = 0.0
    margin_tier_found = False
    for min_p, max_p, margin in MARGIN_MINIMUMS["page_counts_inside"]:
        if min_p <= page_count <= max_p:
            inside_margin_val = margin
            margin_tier_found = True
            break

    # Override for Hardcover general case if page count fits typical HC range (75-550) and not already found
    # KDP Hardcover margins are more complex and can depend on specific trim size for inside margin, this is a simplification
    if book_format_str == "Hardcover":
        if 75 <= page_count <= 550:
            inside_margin_val = MARGIN_MINIMUMS["hardcover_default_inside"] # Use default HC inside margin
            margin_tier_found = True # Consider it found for HC within this common range
        elif page_count > 550:
             results.append(f"⚠️ **Print Specs - Margins:** Hardcover page count ({page_count}) exceeds 550. KDP typically limits HC to 550 pages. Please verify. {guideline_ref}")


    outside_margin_min_val = MARGIN_MINIMUMS["bleed_outside"] if has_bleed else MARGIN_MINIMUMS["no_bleed_outside"]

    if margin_tier_found and inside_margin_val > 0:
        results.append(f"✅ **Minimum Margin Requirements (Manuscript File):** Inside (Gutter): at least **{inside_margin_val:.3f}\"**. Outside (Top, Bottom, Outer Edge): at least **{outside_margin_min_val:.3f}\"**. {guideline_ref}")
    else:
        results.append(f"⚠️ **Print Specs - Margins:** Could not determine specific inside margin for {page_count} pages. Minimum Outside (Top, Bottom, Outer Edge): **{outside_margin_min_val:.3f}\"**. Please consult KDP Guideline 13 tables for precise inside margin. {guideline_ref}")

    results.append("   *Reminder: Set 'Mirror Margins' in your document setup (e.g., MS Word) for print books.*")
    if book_format_str == "Hardcover":
         results.append("   *Hardcover margin requirements can be very specific to trim size and page count. Always double-check KDP's official documentation.*")

    return results


# --- AI Declaration, Audience, Type ---
def validate_primary_audience(sexually_explicit, min_age, max_age, categories_list, guideline_ref="Guideline 2, 11"):
    results = []
    children_category_keywords = ["children", "kids", "juvenile", "baby", "toddler", "picture book", "early reader", "middle grade"]
    teen_category_keywords = ["teen", "young adult", "ya"]

    if sexually_explicit == "Yes":
        results.append(f"⚠️ **Sexually Explicit Content:** Declared. Book will be ineligible for Children’s categories. {guideline_ref}")
        if min_age is not None and min_age < 18:
            results.append(f"⚠️ **Sexually Explicit & Reading Age:** Explicit content declared, but minimum reading age is {min_age}. This may be contradictory. {guideline_ref}")
        for cat_str in categories_list:
            if cat_str and any(child_kw in cat_str.lower() for child_kw in children_category_keywords):
                results.append(f"❌ **Sexually Explicit & Category:** Explicit content declared, but category '{cat_str}' appears to be for children. This is not allowed. {guideline_ref}")

    if min_age is not None and max_age is not None:
        if min_age < 0 or max_age < 0: # Should be caught by number_input min_value
            results.append(f"❌ **Reading Age:** Ages cannot be negative. {guideline_ref}")
        elif min_age > max_age != 0: # Allow max_age=0 if min_age is set
            results.append(f"❌ **Reading Age:** Minimum age ({min_age}) cannot be greater than maximum age ({max_age}), unless max age is 0 (not set). {guideline_ref}")
        else:
            results.append(f"✅ **Reading Age Range:** Min: {min_age if min_age !=0 else 'Not Set'}, Max: {max_age if max_age !=0 else 'Not Set'}.")
    elif (min_age is not None and min_age != 0) and (max_age is None or max_age == 0):
        results.append(f"ℹ️ **Reading Age:** Minimum age ({min_age}) set, but maximum is not. Consider setting a maximum. {guideline_ref}")
    elif (max_age is not None and max_age != 0) and (min_age is None or min_age == 0):
        results.append(f"ℹ️ **Reading Age:** Maximum age ({max_age}) set, but minimum is not. Consider setting a minimum. {guideline_ref}")


    is_children_or_ya_category_selected = any(
        cat_str and (any(child_kw in cat_str.lower() for child_kw in children_category_keywords) or
                     any(teen_kw in cat_str.lower() for teen_kw in teen_category_keywords))
        for cat_str in categories_list
    )

    if is_children_or_ya_category_selected and (min_age is None or min_age == 0):
        results.append(f"⚠️ **Reading Age & Category:** A Children's or Teen/YA category is selected. Setting an appropriate Minimum and Maximum reading age is highly recommended for discoverability. {guideline_ref}")
    elif min_age is not None and min_age > 17 and is_children_or_ya_category_selected:
         results.append(f"⚠️ **Reading Age & Category:** Minimum reading age ({min_age}) seems for adults, but a Children's/YA category is selected. Please verify this is intentional. {guideline_ref}")

    if not results: # If no specific errors/warnings related to audience were added
        results.append("✅ **Primary Audience:** Basic checks passed.")
    return results

def validate_isbn(isbn_str, is_low_content, book_format, guideline_ref="Guideline 6, 7, 11, 12"):
    results = []
    is_print_format = book_format in ["Paperback", "Hardcover"]

    if not isbn_str:
        if is_print_format and not is_low_content:
            results.append(f"ℹ️ **ISBN:** No ISBN provided. For non-low-content {book_format.lower()} books, an ISBN is required. KDP can provide one for free (except for low-content). {guideline_ref}")
        elif is_print_format and is_low_content:
            results.append(f"ℹ️ **ISBN:** No ISBN provided for low-content {book_format.lower()}. This is acceptable. Note: KDP does not provide free ISBNs for low-content books. {guideline_ref}")
        elif book_format == "eBook":
            results.append(f"ℹ️ **ISBN:** No ISBN provided for eBook. This is acceptable (ISBN is optional for eBooks). {guideline_ref}")
        return results # Return early if no ISBN provided, further checks not needed

    # ISBN provided, proceed with validation
    cleaned_isbn = isbn_str.replace("-", "").replace(" ", "")
    if not cleaned_isbn.isdigit():
        results.append(f"❌ **ISBN ('{isbn_str}'):** Should consist of digits only (hyphens are for display). Found non-digit characters. {guideline_ref}")
        # Don't return yet, length check might still be useful
    length = len(cleaned_isbn)
    if length not in [10, 13]:
        results.append(f"❌ **ISBN ('{isbn_str}'):** Must be 10 or 13 digits long (when hyphens/spaces removed). Found {length} digits. {guideline_ref}")
    else:
        results.append(f"✅ **ISBN Format:** Length ({length} digits) is correct for ISBN-10 or ISBN-13.")

    if is_low_content and is_print_format:
        results.append(f"⚠️ **ISBN & Low Content:** You've provided an ISBN ('{isbn_str}') for a low-content {book_format.lower()}. Ensure this is your own purchased ISBN, as KDP does not offer free ISBNs for low-content books. {guideline_ref}")
    elif is_print_format and not is_low_content:
         results.append(f"ℹ️ **ISBN Provided:** '{isbn_str}'. Ensure this ISBN and its associated imprint, title, and author match exactly what's registered with your ISBN agency (e.g., Bowker) if it's your own. If using a free KDP ISBN, KDP handles registration. {guideline_ref}")

    return results

def validate_ai_content_declaration(ai_used_any_str, ai_text_detail, ai_images_detail, ai_translation_detail, guideline_ref="Guideline 1"):
    results = []
    ai_used = ai_used_any_str == "Yes"

    if not ai_used:
        results.append(f"✅ **AI Content Declaration:** User states no AI-based tools were used to *create* text, images, or translations. (AI-assistance for editing/refining user-created content is different and generally doesn't require disclosure). {guideline_ref}")
        return results

    results.append(f"📝 **AI Content Declaration: User indicated use of AI tools.** Review KDP's definitions of 'AI-Generated' vs. 'AI-Assisted'. You are responsible for all content adhering to guidelines, including IP rights. {guideline_ref}")

    if ai_text_detail != AI_TEXT_OPTIONS[0]: # Not "None"
        results.append(f"  - **AI-Generated Text declared:** '{ai_text_detail}'. This requires disclosure to KDP. KDP considers text *created* by AI tools as 'AI-Generated', even with substantial user edits afterward.")
    if ai_images_detail != AI_IMAGE_OPTIONS[0]:
        results.append(f"  - **AI-Generated Images declared:** '{ai_images_detail}'. This requires disclosure to KDP. KDP considers images *created* by AI tools as 'AI-Generated', regardless of subsequent edits.")
    if ai_translation_detail != AI_TRANSLATION_OPTIONS[0]:
        results.append(f"  - **AI-Generated Translations declared:** '{ai_translation_detail}'. This requires disclosure to KDP. KDP considers translations *created* by AI tools as 'AI-Generated', even with substantial user edits afterward.")

    if ai_text_detail == AI_TEXT_OPTIONS[0] and ai_images_detail == AI_IMAGE_OPTIONS[0] and ai_translation_detail == AI_TRANSLATION_OPTIONS[0] and ai_used:
        results.append(f"⚠️ **AI Declaration Inconsistency:** You indicated AI tools were used, but then selected 'None' for text, images, and translations. If AI tools only *assisted* with your own created content (e.g., editing, brainstorming, refining), select 'No' for the initial AI use question. If AI *created* any actual content, please specify in the details. {guideline_ref}")

    return results

def validate_low_content_implications(is_low_content, guideline_ref="Guideline 6, 11"):
    results = []
    if is_low_content:
        results.append(f"ℹ️ **Low-Content Book Specifics:** This book is marked as low-content. Be aware of the following KDP policies: {guideline_ref}")
        results.append("  - Not eligible for a free KDP ISBN.")
        results.append("  - Not eligible to be part of a KDP Series.")
        results.append("  - 'Look Inside' feature might not be supported if you publish without your own ISBN (consider A+ Content for interior images).")
        results.append("  - Transparency codes are not available if published without your own ISBN.")
        results.append("  - The 'Set Release Date' option for pre-orders is not currently offered.")
        results.append("  - If KDP places a barcode (when publishing without your own ISBN/barcode), ensure the bottom-right of your back cover is clear.")
        results.append("  - The 'low-content' checkbox in KDP cannot be changed after publishing.")
    return results

# --- Language & Manuscript ---
def validate_language_and_format(
    selected_language_metadata, book_format, manuscript_upload_format_for_kdp,
    guideline_ref="Guideline 11"
    ):
    results = []
    if not selected_language_metadata:
        results.append(f"❌ **Book Language:** Language not selected. This is mandatory. {guideline_ref}")
        return results # Stop if language is missing

    # Check format compatibility with language
    if book_format == "eBook":
        if selected_language_metadata in PRINT_ONLY_LANGS_GENERAL:
            results.append(f"❌ **Language/Format Conflict:** '{selected_language_metadata}' is generally supported for print formats (Paperback/Hardcover) only, not eBooks, according to KDP Guideline 11. Please verify.")
        elif selected_language_metadata == "Hebrew": # Special case from table for Hebrew
             results.append(f"❌ **Language/Format Conflict:** '{selected_language_metadata}' is listed as Paperback only in Guideline 11. Not for eBooks.")
        elif selected_language_metadata == "Japanese" and selected_language_metadata not in JAPANESE_FORMAT_RESTRICTIONS:
            results.append(f"⚠️ **Language/Format:** '{selected_language_metadata}' for eBook. Japanese has specific reading direction settings in KDP. Ensure these are correctly configured. {guideline_ref}")

    elif book_format in ["Paperback", "Hardcover"]:
        if selected_language_metadata in EBOOK_ONLY_LANGS:
            results.append(f"❌ **Language/Format Conflict:** '{selected_language_metadata}' is supported for eBooks *only*, not for {book_format}. {guideline_ref}")
        if selected_language_metadata == "Japanese" and book_format == "Hardcover": # Japanese is eBook and Paperback only per G11
            results.append(f"❌ **Language/Format Conflict:** Japanese is listed for eBook and Paperback only in KDP Guideline 11, not Hardcover. Please verify.")

        if selected_language_metadata == "Hebrew":
            if book_format != "Paperback":
                 results.append(f"❌ **Language/Format Conflict:** Hebrew is listed as Paperback only in Guideline 11. Not for {book_format}.")
            if HEBREW_RESTRICTIONS: # Check color option if it's passed later
                pass # Placeholder for color option check in main app based on ink_paper_type
        if selected_language_metadata == "Yiddish":
            if YIDDISH_RESTRICTIONS and book_format == "Hardcover":
                 results.append(f"ℹ️ **Language Note (Yiddish Hardcover):** Ensure LTR (Left-to-Right) reading direction is set up. {guideline_ref}")


    # Check PDF upload compatibility with language
    if manuscript_upload_format_for_kdp == "PDF" and selected_language_metadata not in PDF_SUPPORTED_LANGS_FOR_UPLOAD:
        results.append(f"⚠️ **Manuscript Upload Format/Language:** You intend to upload a PDF for '{selected_language_metadata}'. KDP only supports PDF uploads for a limited set of languages ({', '.join(PDF_SUPPORTED_LANGS_FOR_UPLOAD)}). For other languages, use formats like HTML, MOBI, Word, EPUB. {guideline_ref}")

    if not results:
        results.append("✅ **Language & Format:** Basic compatibility checks passed.")
    return results

# --- Translation & Public Domain ---
def validate_translation_info(is_translation, original_author, translator_name, guideline_ref="Guideline 1"):
    results = []
    if is_translation:
        results.append("ℹ️ **Translation Information:** Book declared as a translation.")
        if not original_author:
            results.append(f"❌ **Original Author (Translation):** If this is a translation, the original author's name must be provided. {guideline_ref}")
        else:
            results.append(f"✅ Original Author (Translation): '{original_author}' provided.")

        if not translator_name:
            results.append(f"⚠️ **Translator Name (Translation):** If this is a translation, the translator's name must be provided. Use 'Anonymous' if the translator is unknown for a non-new translation. {guideline_ref}")
        elif translator_name.lower() == "anonymous":
            results.append(f"✅ Translator Name (Translation): 'Anonymous' provided. This is acceptable if translator is unknown for an older work. {guideline_ref}")
        else:
            results.append(f"✅ Translator Name (Translation): '{translator_name}' provided.")
    return results

def validate_public_domain_differentiation(is_public_domain, differentiation_statement, book_description, guideline_ref="Guideline 1"):
    results = []
    if is_public_domain:
        results.append("ℹ️ **Public Domain Book:** Noted. Differentiation is key for KDP acceptance if a free version exists.")
        results.append(f"  - **KDP Policy Reminder:** Undifferentiated versions of public domain titles are not allowed if a free version is already available in the Kindle store. Your version must be *substantially* differentiated (e.g., through unique translation, original annotations, scholarly analysis, or unique illustrative content). Minor formatting changes are not sufficient. {guideline_ref}")

        differentiation_keywords = [
            "annotated", "annotations by", "illustrated by", "original illustrations", "new translation by",
            "critical edition", "introduction by", "foreword by", "commentary by",
            "scholarly analysis", "edited by", "with new research", "unique collection of"
        ]
        # Combine statement and description for keyword checking
        text_to_check_for_keywords = (differentiation_statement.lower() if differentiation_statement else "") + " " + (book_description.lower() if book_description else "")

        found_keywords = [kw for kw in differentiation_keywords if kw in text_to_check_for_keywords]

        if not differentiation_statement.strip() and not found_keywords:
            results.append(f"❌ **Differentiation Not Stated Clearly:** Please provide a clear statement in the dedicated field describing how your public domain version is *substantially differentiated*, OR ensure this is very obvious in your book description using terms like 'annotated by', 'new translation', 'original illustrations', 'scholarly introduction'. This is crucial for KDP. {guideline_ref}")
        elif differentiation_statement.strip() and not found_keywords: # Statement provided, but no strong keywords hit
             results.append(f"⚠️ **Differentiation Statement May Lack Clarity:** Your statement ('{differentiation_statement[:70]}...') does not seem to use common terms indicating substantial differentiation (e.g., 'annotated', 'new translation', 'original illustrations'). Ensure your statement clearly conveys unique, KDP-acceptable value beyond simple reformatting. {guideline_ref}")
        elif found_keywords:
            results.append(f"✅ **Potential Differentiation Mentioned:** Your statement and/or description appears to mention terms like '{', '.join(found_keywords)}' which could indicate differentiation. Ensure this reflects *substantial and unique* KDP-acceptable value.")
        else: # Should be caught by the first 'if' but as a fallback
             results.append(f"⚠️ **Differentiation Not Obvious:** Could not identify clear terms of substantial differentiation in your statement or description. Please explicitly describe the unique value added. {guideline_ref}")
    return results