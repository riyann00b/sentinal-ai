# kdp_data.py

KDP_PAGE_COUNT_SPECS_PAPERBACK = {
    "5\" x 8\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600), "prem_color_white": (24, 828)},
    "5.06\" x 7.81\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600), "prem_color_white": (24, 828)},
    "5.25\" x 8\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600), "prem_color_white": (24, 828)},
    "5.5\" x 8.5\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600), "prem_color_white": (24, 828)},
    "6\" x 9\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600), "prem_color_white": (24, 828)},
    "6.14\" x 9.21\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600), "prem_color_white": (24, 828)},
    "6.69\" x 9.61\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600), "prem_color_white": (24, 828)},
    "7\" x 10\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600), "prem_color_white": (24, 828)},
    "7.44\" x 9.69\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600), "prem_color_white": (24, 828)},
    "7.5\" x 9.25\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600), "prem_color_white": (24, 828)},
    "8\" x 10\"": {"bw_white": (24, 828), "bw_cream": (24, 776), "std_color_white": (72, 600), "prem_color_white": (24, 828)},
    "8.25\" x 6\"": {"bw_white": (24, 800), "bw_cream": (24, 750), "std_color_white": (72, 600), "prem_color_white": (24, 800)},
    "8.25\" x 8.25\"": {"bw_white": (24, 800), "bw_cream": (24, 750), "std_color_white": (72, 600), "prem_color_white": (24, 800)},
    "8.5\" x 8.5\"": {"bw_white": (24, 590), "bw_cream": (24, 550), "std_color_white": (72, 600), "prem_color_white": (24, 590)},
    "8.5\" x 11\"": {"bw_white": (24, 590), "bw_cream": (24, 550), "std_color_white": (72, 600), "prem_color_white": (24, 590)},
    "8.27\" x 11.69\" (A4)": {"bw_white": (24, 780), "bw_cream": (24, 730), "std_color_white": "Not available", "prem_color_white": (24, 590)}, # Adjusted std_color for A4 Paperback
}

KDP_PAGE_COUNT_SPECS_HARDCOVER = {
    "5.5\" x 8.5\"": {"bw_white": (75, 550), "bw_cream": (75, 550), "std_color_white": "Not available", "prem_color_white": (75, 550)},
    "6\" x 9\"": {"bw_white": (75, 550), "bw_cream": (75, 550), "std_color_white": "Not available", "prem_color_white": (75, 550)},
    "6.14\" x 9.21\"": {"bw_white": (75, 550), "bw_cream": (75, 550), "std_color_white": "Not available", "prem_color_white": (75, 550)},
    "7\" x 10\"": {"bw_white": (75, 550), "bw_cream": (75, 550), "std_color_white": "Not available", "prem_color_white": (75, 550)},
    "8.25\" x 11\"": {"bw_white": (75, 550), "bw_cream": (75, 550), "std_color_white": "Not available", "prem_color_white": (75, 550)},
}


INK_PAPER_TO_KEY_MAP = {
    "Black & white interior with cream paper": "bw_cream",
    "Black & white interior with white paper": "bw_white",
    "Standard color interior with white paper": "std_color_white",
    "Premium color interior with white paper": "prem_color_white"
}

SUPPORTED_LANGUAGES = sorted(list(
    {"Afrikaans", "Alsatian", "Arabic", "Basque", "Bokmål Norwegian", "Breton", "Catalan", "Chinese (Traditional)",
     "Cornish", "Corsican", "Danish", "Dutch/Flemish", "Eastern Frisian", "English", "Finnish", "French", "Frisian",
     "Galician", "German", "Gujarati", "Hebrew", "Hindi", "Icelandic", "Irish", "Italian", "Japanese", "Latin",
     "Luxembourgish", "Malayalam", "Manx", "Marathi", "Northern Frisian", "Norwegian", "Nynorsk Norwegian", "Polish",
     "Portuguese", "Provençal", "Romansh", "Scots", "Scottish Gaelic", "Spanish", "Swedish", "Tamil", "Ukrainian",
     "Welsh", "Yiddish"}))

EBOOK_ONLY_LANGS = ["Arabic", "Chinese (Traditional)", "Gujarati", "Hindi", "Malayalam", "Marathi", "Tamil"]
# Based on Guideline 11 table, "paperback and hardcover only" or similar
PRINT_ONLY_LANGS_GENERAL = ["Polish", "Latin", "Ukrainian"] # Generalizing for simplicity here
HEBREW_RESTRICTIONS = {"formats": ["Paperback"], "color_options": ["Black & white interior with cream paper", "Black & white interior with white paper", "Premium color interior with white paper"]} # No standard color
YIDDISH_RESTRICTIONS = {"formats": ["Paperback", "Hardcover"], "hardcover_reading_direction": "LTR"} # LTR for HC, Standard color might be an issue too

JAPANESE_FORMAT_RESTRICTIONS = ["eBook", "Paperback"] # No Hardcover explicitly mentioned for Japanese in G11 table

PDF_SUPPORTED_LANGS_FOR_UPLOAD = ["English", "French", "German", "Italian", "Portuguese", "Spanish", "Catalan", "Galician", "Basque"]

AI_TEXT_OPTIONS = [
    "None (AI was only used for assistance like brainstorming or editing my own writing)",
    "Some sections created by AI, with minimal or no editing by you",
    "Some sections created by AI, with extensive editing by you",
    "Entire work created by AI, with minimal or no editing by you",
    "Entire work created by AI, with extensive editing by you"
]
AI_IMAGE_OPTIONS = [
    "None (AI was only used for assistance like brainstorming or editing my own images)",
    "One or a few AI-generated images, with minimal or no editing by you",
    "One or a few AI-generated images, with extensive editing by you",
    "Many AI-generated images, with minimal or no editing by you",
    "Many AI-generated images, with extensive editing by you"
]
AI_TRANSLATION_OPTIONS = [
    "None (AI was only used for assistance like brainstorming or editing my own translations)",
    "Some sections translated by AI, with minimal or no editing by you",
    "Some sections translated by AI, with extensive editing by you",
    "Entire work translated by AI, with minimal or no editing by you",
    "Entire work translated by AI, with extensive editing by you"
]

TRIM_SIZE_OPTIONS_PAPERBACK = [
    "Select Trim Size", "5\" x 8\"", "5.06\" x 7.81\"", "5.25\" x 8\"", "5.5\" x 8.5\"", "6\" x 9\"",
    "6.14\" x 9.21\"", "6.69\" x 9.61\"", "7\" x 10\"", "7.44\" x 9.69\"", "7.5\" x 9.25\"",
    "8\" x 10\"", "8.25\" x 6\"", "8.25\" x 8.25\"", "8.5\" x 8.5\"", "8.5\" x 11\"",
    "8.27\" x 11.69\" (A4)"
]
TRIM_SIZE_OPTIONS_HARDCOVER = [
    "Select Trim Size", "5.5\" x 8.5\"", "6\" x 9\"", "6.14\" x 9.21\"", "7\" x 10\"", "8.25\" x 11\""
]

INK_PAPER_OPTIONS_PAPERBACK = [
    "Select Ink/Paper",
    "Black & white interior with cream paper",
    "Black & white interior with white paper",
    "Standard color interior with white paper",
    "Premium color interior with white paper"
]
INK_PAPER_OPTIONS_HARDCOVER = [ # Standard Color often not available for HC
    "Select Ink/Paper",
    "Black & white interior with cream paper",
    "Black & white interior with white paper",
    "Premium color interior with white paper"
]

BOOK_FORMAT_OPTIONS = ["eBook", "Paperback", "Hardcover"]
YES_NO_OPTIONS = ["No", "Yes"]
MANUSCRIPT_UPLOAD_FORMAT_OPTIONS = ["Other", "PDF", "DOCX", "EPUB", "HTML", "TXT"]

PROHIBITED_TITLE_KEYWORDS = ["free", "bestselling", "best seller", "best book", "sale", "discount", "notebook", "journal", "gifts", "books", "summary of", "study guide for", "analysis of"] # Added a few more common ones
TITLE_PLACEHOLDERS = ["unknown", "n/a", "na", "blank", "none", "null", "not applicable", "untitled"]
PROHIBITED_KEYWORD_TERMS = ["free", "bestselling", "on sale", "new", "available now", "kindle unlimited", "kdp select", "book", "ebook"] # "book", "ebook" if used alone
SUPPORTED_HTML_TAGS_DESCRIPTION = ['br', 'p', 'b', 'em', 'i', 'u', 'h4', 'h5', 'h6', 'ol', 'ul', 'li']

# Guideline 13 Margin Minimums
MARGIN_MINIMUMS = {
    "no_bleed_outside": 0.25, # inches
    "bleed_outside": 0.375, # inches
    "page_counts_inside": [
        (24, 150, 0.375),
        (151, 300, 0.5),
        (301, 500, 0.625),
        (501, 700, 0.75),
        (701, 828, 0.875) # For paperback
    ],
    "hardcover_default_inside": 0.625 # A general figure, KDP docs are more nuanced by trim for HC
}

DEFAULT_SESSION_STATE = {
    'book_title_metadata': "",
    'subtitle_metadata': "",
    'author_name_metadata': "",
    'is_public_domain': False,
    'public_domain_differentiation_statement': "",
    'title_on_cover': "",
    'author_on_cover': "",
    'is_translation': False,
    'original_author_translation': "",
    'translator_name_translation': "",
    'description_text': "",
    'categories_input_list': ["", "", ""],
    'keywords_input_list': [""] * 7,
    'is_series': False,
    'series_name': "",
    'series_number': "",
    'sexually_explicit': "No",
    'min_reading_age': 0,
    'max_reading_age': 0,
    'ai_used_any': "No",
    'ai_text_detail': AI_TEXT_OPTIONS[0],
    'ai_images_detail': AI_IMAGE_OPTIONS[0],
    'ai_translation_detail': AI_TRANSLATION_OPTIONS[0],
    'is_low_content': False,
    'isbn': "",
    'selected_language': "English",
    'manuscript_upload_format_for_kdp': "Other", # User's intended format for KDP
    'book_format': BOOK_FORMAT_OPTIONS[0],
    'trim_size': TRIM_SIZE_OPTIONS_PAPERBACK[0], # Default to paperback options
    'ink_paper_type': INK_PAPER_OPTIONS_PAPERBACK[0],
    'page_count': "",
    'interior_bleed': "No",

    # Internal app state
    'validation_results_grouped': {},
    'ai_analysis_feedbacks': {},
    'error_count': 0,
    'warning_count': 0,
    'extracted_manuscript_text': "",
    'last_uploaded_filename': None, # To track if file changed
    'json_inputs_to_share': "",     # For save/load feature
    'json_load_area_text': ""       # For save/load feature
}