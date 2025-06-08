# ai_analyzers.py
import boto3
import json
import re
import random

# --- Bedrock Client Configuration ---
BEDROCK_REGION = "us-east-1"
BEDROCK_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
bedrock_runtime_client = None


def init_bedrock_client():
    """Initializes the Bedrock runtime client if not already initialized."""
    global bedrock_runtime_client
    if bedrock_runtime_client is None:
        try:
            bedrock_runtime_client = boto3.client(
                service_name="bedrock-runtime",
                region_name=BEDROCK_REGION
            )
            return True, "Bedrock client initialized successfully."
        except Exception as e:
            bedrock_runtime_client = None
            return False, f"CRITICAL ERROR: Could not initialize Bedrock client in region '{BEDROCK_REGION}': {e}. Ensure AWS credentials and Bedrock model access are correctly configured."
    return True, "Bedrock client was already initialized."


def invoke_claude_model(prompt_text, model_id=BEDROCK_MODEL_ID, max_tokens=2000, temperature=0.3, top_p=0.9):
    """
    Invokes the Claude model via Bedrock.
    Returns the model's text response or an error/info string.
    """
    global bedrock_runtime_client
    if bedrock_runtime_client is None:
        # This path indicates a logic error in the calling app, as init should be confirmed first.
        print(
            "CRITICAL RUNTIME WARNING: invoke_claude_model called while bedrock_runtime_client is None. AI functionality will fail.")
        return "Error: Bedrock client is not available (was None when AI call attempted). AI analysis aborted."

    if not isinstance(prompt_text, str) or not prompt_text.strip():
        return "Error: Invalid or empty prompt provided to AI model."

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt_text}]}]
    })

    try:
        # The linter might still warn here due to static analysis of the global variable.
        # However, the check above should prevent this line from executing if client is None.
        response = bedrock_runtime_client.invoke_model(
            body=body, modelId=model_id, accept="application/json", contentType="application/json"
        )
        response_body = json.loads(response.get("body").read())

        if response_body.get("type") == "error":
            return f"Error: AI model returned an error: {response_body.get('error', {}).get('message', 'Unknown error')}"

        content_list = response_body.get("content", [])
        if isinstance(content_list, list) and content_list:
            for content_block in content_list:
                if content_block.get("type") == "text":
                    return content_block.get("text", "").strip()

        return "Informational: AI model returned no specific text feedback or an unexpected response structure."

    except AttributeError as ae:  # Specifically catch if invoke_model is called on None (should be rare now)
        if "NoneType" in str(ae) and "invoke_model" in str(ae):
            print(
                f"FATAL RUNTIME ERROR: Attempted to call invoke_model on None bedrock_runtime_client. App logic error. {ae}")
            return "Error: Bedrock client was unexpectedly None during AI call. Analysis aborted."
        raise  # Re-raise if it's a different AttributeError
    except Exception as e:
        error_type = type(e).__name__
        return f"Error: Could not get response from AI model '{model_id}'. Type: {error_type}, Details: {str(e)[:150]}..."


# --- AI Analysis Functions (Using YOUR list of functions) ---

def ai_extract_details_for_autofill(manuscript_text):
    # ... (Your existing prompt and logic) ...
    # Make sure the regex for JSON extraction is corrected:
    # json_match = re.search(r"\{.*}", ai_feedback_str, re.DOTALL) # Corrected Regex
    # ...
    suggestions = {
        "title": "", "author": "", "language": "", "description_draft": "",
        "keywords": [], "categories": [], "series_title": "", "series_number": "",
        "is_translation_hint": False, "original_author_hint": "", "translator_hint": ""
    }
    if not manuscript_text or len(manuscript_text) < 200:
        return suggestions, "ℹ️ Manuscript text too short for comprehensive auto-fill."

    text_chunk = manuscript_text[:8000]
    prompt = f"""You are an expert librarian and KDP assistant. Analyze the following manuscript text snippet (approximately first {len(text_chunk)} characters) and extract or infer the specified information.
Provide your response strictly in JSON format with the exact keys listed. If a piece of information cannot be confidently determined, use an empty string "" or an empty list [].

Keys to extract:
- "title_suggestion": The most likely book title. Look for prominent, centered text near the beginning, or lines like "Title: ...".
- "author_suggestion": The most likely primary author's name. Look for "By ..." or names near the title.
- "language_suggestion": The primary language of the text (e.g., "English", "Spanish", "French", "German").
- "description_draft_suggestion": A short, compelling draft book description (2-4 sentences, ~75-100 words) based on the initial content's plot, theme, or main idea.
- "keyword_suggestions": A list of 3-5 relevant KDP-style keywords or short phrases (2-3 words each) describing setting, character types, plot themes, or story tone.
- "category_suggestions": A list of 1-2 broad KDP genre categories that seem appropriate (e.g., "Science Fiction > Adventure", "Romance > Contemporary", "Self-Help > Personal Development"). Be specific if possible.
- "series_title_suggestion": If the text strongly indicates it's part of a series (e.g., "Book Two of The Great Chronicles", "The Dragon's Legacy: Part 1"), suggest the series title.
- "series_number_suggestion": If a series number is clearly indicated with a series title (e.g., "Book 2", "Part II"), suggest the number (digits only).
- "is_translation_hint": true if there are strong textual cues like "translated by", "original title:", "originally published in [language] as...", otherwise false.
- "original_author_hint": If is_translation_hint is true and an original author is mentioned, suggest their name.
- "translator_hint": If is_translation_hint is true and a translator is mentioned, suggest their name.

Prioritize information found early in the text (e.g., potential title page, copyright page elements, first few paragraphs).
For description and keywords, capture the essence of the beginning of the story/content.

Manuscript Snippet:
---
{text_chunk}
---

JSON Response:
"""
    ai_feedback_str = invoke_claude_model(prompt, max_tokens=1800, temperature=0.2)

    if ai_feedback_str and not ai_feedback_str.startswith("Error:") and not ai_feedback_str.startswith(
            "Informational:"):
        try:
            json_match = re.search(r"\{.*}", ai_feedback_str, re.DOTALL)  # Corrected Regex
            if json_match:
                ai_extracted_data = json.loads(json_match.group(0))
                suggestions["title"] = ai_extracted_data.get("title_suggestion", "").strip()
                suggestions["author"] = ai_extracted_data.get("author_suggestion", "").strip()
                suggestions["language"] = ai_extracted_data.get("language_suggestion", "").strip()
                suggestions["description_draft"] = ai_extracted_data.get("description_draft_suggestion", "").strip()
                suggestions["keywords"] = [kw.strip() for kw in ai_extracted_data.get("keyword_suggestions", []) if
                                           isinstance(kw, str) and kw.strip()]
                suggestions["categories"] = [cat.strip() for cat in ai_extracted_data.get("category_suggestions", []) if
                                             isinstance(cat, str) and cat.strip()]
                suggestions["series_title"] = ai_extracted_data.get("series_title_suggestion", "").strip()
                suggestions["series_number"] = ai_extracted_data.get("series_number_suggestion", "").strip()
                suggestions["is_translation_hint"] = ai_extracted_data.get("is_translation_hint", False)
                suggestions["original_author_hint"] = ai_extracted_data.get("original_author_hint", "").strip()
                suggestions["translator_hint"] = ai_extracted_data.get("translator_hint", "").strip()
                return suggestions, "✅ AI extracted details! Please review."
            else:
                return suggestions, f"⚠️ AI response for auto-fill was not in expected JSON format. Response: {ai_feedback_str[:200]}..."
        except json.JSONDecodeError:
            return suggestions, f"⚠️ Error decoding AI JSON response for auto-fill. Response: {ai_feedback_str[:200]}..."
        except Exception as e:
            return suggestions, f"⚠️ Error processing AI auto-fill: {str(e)[:100]}"
    elif ai_feedback_str:
        return suggestions, ai_feedback_str
    else:
        return suggestions, "⚠️ AI did not provide suggestions for auto-fill (empty response)."


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
    Specifically look for claims in the description NOT clearly supported or contradicted by the manuscript snippet.
    List significant discrepancies as actionable bullet points. Explain the mismatch and suggest ways to make the description more accurate.
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
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=[.?!])\s', manuscript_text.strip())  # Corrected Regex
    candidate_sentences = sorted(list(set(s.strip() for s in sentences if 15 < len(s.split()) < 60 and len(s) > 80)),
                                 key=len, reverse=True)
    if not candidate_sentences: return [
        "ℹ️ Could not find enough distinct, long sentences for 'freely available content' check."]
    sentences_to_check = random.sample(candidate_sentences, min(len(candidate_sentences), 3))
    prompt_sentences_block = "Sentences to assess:\n" + "".join(
        f"{i + 1}. \"{sent}\"\n" for i, sent in enumerate(sentences_to_check))
    prompt = f"""{prompt_sentences_block}
    For each numbered sentence above: Assess likelihood (Low, Medium, High) of being commonly found verbatim on public web. Brief justification. Format: "* Sentence X: [Likelihood] - [Justification]"
    Conclude with reminder: "Ensure you hold all publishing rights. KDP prohibits copyrighted content freely available on web unless you are owner/have permission." (Ref G1)
    Present as structured list. """
    ai_feedback = invoke_claude_model(prompt, max_tokens=700)
    if ai_feedback:
        results.append(ai_feedback)
    else:
        results.append("⚠️ AI check for freely available content failed or returned no response.")
    return results


def ai_check_manuscript_typos_placeholders_accessibility(manuscript_text):  # Removed unused guideline_ref
    results = []
    if not manuscript_text or len(manuscript_text) < 100:
        return ["ℹ️ Manuscript text too short/not provided for detailed quality/placeholder/accessibility checks."]
    text_chunk_for_analysis = manuscript_text[:4000]
    prompt = f"""You are a KDP manuscript quality assistant. Review snippet (first ~{len(text_chunk_for_analysis)} chars) for:
    1. Typos/Grammar: List up to 5-7 noticeable errors (original -> suggested).
    2. Placeholder Text: Identify common placeholders ("Lorem Ipsum", "Insert Chapter Title Here", etc.).
    3. Accessibility Hints: Identify elements needing accessibility considerations (undescribed images, poor lists). Actionable suggestions.
    If no issues for a category, state "No specific issues noted in this snippet."
    Manuscript Snippet: --- {text_chunk_for_analysis} --- """
    ai_feedback = invoke_claude_model(prompt, max_tokens=1800)
    if ai_feedback:
        results.append(ai_feedback)
    else:
        results.append("⚠️ AI check for typos/placeholders/accessibility failed.")
    return results


def ai_check_manuscript_general_quality_issues(manuscript_text):  # Removed unused guideline_ref
    results = []
    if not manuscript_text or len(manuscript_text) < 200:
        return ["ℹ️ Manuscript text too short/not provided for general quality check."]
    text_chunk = manuscript_text[:3000]
    prompt = f"""You are a KDP content quality reviewer. Analyze snippet (first ~{len(text_chunk)} chars) for general quality issues per Kindle Content Quality Guides. Actionable bullet points per category if issues found. If none, state "No specific issues noted in this snippet."
    1. Incomplete Content/Abrupt Endings: Signs content ends abruptly, missing chapters, refers to content not present? (e.g., "Conclusion:" then little text). Specific examples, suggest checking completeness.
    2. Distracting Formatting (from text patterns): Overuse of ALL CAPS, excessive/inconsistent **bolding**/*italics* hindering readability? Specific examples, advise review.
    3. Inappropriate Solicitation in Narrative: Direct requests for reviews, ratings, social follows *within main narrative* (not end matter)? Quote phrase, advise remove/relocate.
    4. Basic Structure Issues (from text patterns): Obvious issues with list formatting (items run together)? Confusing dialogue presentation (lack of speaker attribution, missing quotes)? Advise review.
    Manuscript Snippet: --- {text_chunk} ---
    Be specific with examples, suggest fixes. """
    ai_feedback = invoke_claude_model(prompt, max_tokens=1200)
    if ai_feedback:
        results.append(ai_feedback)
    else:
        results.append("⚠️ AI check for general manuscript quality failed.")
    return results


def ai_check_links_in_manuscript(manuscript_text):  # Removed unused guideline_ref
    results = []
    if not manuscript_text or len(manuscript_text) < 50:
        return ["ℹ️ Manuscript text too short/not provided for link analysis."]
    url_pattern = r'(?:(?:https?|ftp):\/\/|www\.)[\w\/\-?=%.~+#&;]+[\w\/\-?=%.~+#&;]'
    found_urls = re.findall(url_pattern, manuscript_text)
    if not found_urls: return ["ℹ️ No URLs automatically detected in the manuscript text for AI review."]
    urls_to_check_str = "\n".join(list(set(found_urls))[:5])
    prompt = f"""You are a KDP content policy assistant. URLs found in manuscript:
    Detected URLs (up to 5 unique): {urls_to_check_str}
    Provide feedback based on KDP's Link Guidelines (actionable bullet points):
    1. Functionality & Relevance: Stress links MUST be functional/relevant.
    2. Prohibited Link Types: Warn against links to porn, other eBook stores (not Amazon), web forms collecting extensive personal data, illegal/harmful/infringing/offensive, malicious.
    3. Descriptive Link Text: Advise descriptive text (e.g., "View author page") not "click here" or raw URL.
    4. Bonus Content Placement: Remind bonus content (previews) not frontloaded or disruptive.
    5. Mandatory Action: State user MUST manually test every link in Kindle Previewer before publishing. """
    ai_feedback = invoke_claude_model(prompt, max_tokens=800)
    if ai_feedback:
        results.append(
            f"Detected URLs for review: {', '.join(list(set(found_urls))[:5])}{' (and potentially more)' if len(set(found_urls)) > 5 else ''}")
        results.append(ai_feedback)
    else:
        results.append("⚠️ Could not get AI feedback on detected links.")
    return results


def ai_check_duplicated_text_in_manuscript(manuscript_text):  # Removed unused guideline_ref
    results = []
    if not manuscript_text or len(manuscript_text) < 500:
        return ["ℹ️ Manuscript text too short/not provided for duplicated text analysis."]
    text_chunk = manuscript_text[:5000]
    prompt = f"""You are a KDP content quality assistant. Analyze snippet (first ~{len(text_chunk)} chars) for potentially unintentional duplicated text blocks.
    Focus on substantial verbatim/near-verbatim repetitions (sentences/paragraphs) seeming like copy-paste errors, not intentional literary device.
    For each suspected unintentional duplication (list up to 3 examples): Provide short snippet (10-15 words) of duplicated text. Explain why it seems unintentional. Suggest author review.
    If no obvious unintentional duplications, state: "No significant unintentional text duplications identified in this snippet."
    Present as bulleted list. Manuscript Snippet: --- {text_chunk} --- """
    ai_feedback = invoke_claude_model(prompt, max_tokens=800)
    if ai_feedback:
        results.append(ai_feedback)
    else:
        results.append("⚠️ Could not perform AI check for duplicated text.")
    return results


def ai_check_disappointing_content_issues(manuscript_text, description_text,
                                          is_translation):  # Removed unused guideline_ref
    results = []
    if not manuscript_text and not description_text:
        return ["ℹ️ Manuscript and description needed for disappointing content checks."]
    text_chunk = manuscript_text[:2000] if manuscript_text else ""
    prompt = f"""You are a KDP content quality assistant. Review for "Disappointing Content" issues. Actionable bullet points.
    Book Desc: "{description_text[:500]}..." Snippet (first ~{len(text_chunk)} chars): "{text_chunk}..." Is Translation: {is_translation}
    Check for:
    1. Content Too Short (Impression): Based ONLY on snippet/desc, does content seem unusually brief for what desc implies? (Rough impression). If so, suggest user verify full length meets expectations.
    2. Poorly Translated (if applicable): If translation, does snippet contain awkward phrasing, unnatural grammar suggesting poor translation? Specific example, suggest professional review. If not translation/quality fine, state that.
    3. Primary Purpose - Solicitation/Advertisement: Does desc/snippet seem *overwhelmingly* focused on soliciting/advertising not substantive content? Suggest toning down.
    4. Bonus Content Placement (Advisory): Remind bonus content (previews) must not appear before primary content, not disruptive.
    If no specific issues for a point, state "No immediate concerns noted for [point name] based on provided text." """
    ai_feedback = invoke_claude_model(prompt, max_tokens=1000)
    if ai_feedback:
        results.append(ai_feedback)
    else:
        results.append("⚠️ AI check for disappointing content issues failed.")
    return results


# Functions from your original prototype list that were using guideline_ref:
def ai_check_offensive_content(text_snippet, guideline_ref="Guideline 1"):  # From your list, uses guideline_ref
    if not text_snippet or len(text_snippet) < 50: return ["ℹ️ Text snippet too short for offensive content scan."]
    prompt = f"""You are a KDP content policy specialist. Analyze text snippet (first ~2000 characters) for potential KDP offensive content (hate speech, child exploitation, pornography, glorifies rape/pedophilia, terrorism) as per {guideline_ref}.
    If issues: provide specific text snippet, suspected violation category, and brief explanation. If none, state "No offensive content identified in this snippet according to {guideline_ref}." Text: --- {text_snippet[:2000]} --- """
    return [invoke_claude_model(prompt, max_tokens=800, temperature=0.1)]


def ai_check_description_quality(description_text,
                                 guideline_ref="Guideline 8, 10"):  # From your list, uses guideline_ref
    if not description_text: return ["ℹ️ No description for AI quality analysis."]
    prompt = f"""KDP book marketing/HTML expert. Analyze description per KDP best practices ({guideline_ref}).
    Simple (plot/theme, concise, ~150w prose), Compelling (grab opening, clear genre), Professional (no errors).
    Supported HTML: <br>,<p>,<b>,<em>,<i>,<u>,<h4>-<h6>,<ol><li>,<ul><li>. NOT <h1>-<h3>. Max 4000 chars.
    Desc: --- {description_text} ---
    Feedback: Overall Impression, Opening, Genre Cues, Professionalism (errors/corrections), HTML Usage (ALL tags, UNSUPPORTED, syntax), Suggestions, Char Count. Ref: {guideline_ref}. """
    return [invoke_claude_model(prompt, max_tokens=1500, temperature=0.4)]


def ai_suggest_keywords(title, description_snippet, current_keywords_str,
                        guideline_ref="Guideline 9, 10"):  # From your list, uses guideline_ref
    if not title and not description_snippet: return ["ℹ️ Title/desc needed for AI keyword suggestions."]
    prompt = f"""KDP keyword expert. Title: "{title}", Desc: "{description_snippet[:500]}...", Current KWs: "{current_keywords_str}"
    Suggest 5-7 KDP keywords/phrases (2-3 words): Portray content (setting, char, plot, tone). Customer search terms. Avoid redundancy (title, current KWs). Adhere KDP 'Keywords to Avoid' ({guideline_ref}).
    Bulleted list. Explain relevance. If current strong, say so. """
    return [invoke_claude_model(prompt, max_tokens=800, temperature=0.5)]


def ai_suggest_categories(title, description_snippet, current_categories_str,
                          guideline_ref="Guideline 2, 11"):  # From your list, uses guideline_ref
    if not title and not description_snippet: return ["ℹ️ Title/desc needed for AI category suggestions."]
    prompt = f"""KDP categorization expert. Title: "{title}", Desc: "{description_snippet[:500]}...", Current Cats: "{current_categories_str}"
    1. Suggest 1-3 KDP-style categories (e.g., "Fiction > Sci-Fi > Space Opera"). Specific per {guideline_ref}.
    2. Explain reasoning.
    3. If current cats ok, confirm. If mismatched, explain, offer alternatives. Structured response. """
    return [invoke_claude_model(prompt, max_tokens=700, temperature=0.4)]


def ai_check_manuscript_quality_snippets(manuscript_text,
                                         guideline_ref="Guideline 4"):  # From your list, uses guideline_ref
    if not manuscript_text or len(manuscript_text) < 200: return ["ℹ️ Manuscript too short for AI quality checks."]
    results = [];
    chunk1 = manuscript_text[:4000]
    prompt1 = f"""KDP manuscript quality assistant. Review snippet (first ~{len(chunk1)} chars) for ({guideline_ref}):
    1. Typos/Grammar: List up to 5-7 errors (original -> suggested).
    2. Placeholder Text: Identify common placeholders.
    3. Accessibility Hints: Identify elements needing accessibility (undescribed images, poor lists). Actionable suggestions.
    If no issues for category, state "No specific issues noted in this snippet." Snippet: --- {chunk1} --- """
    results.append(f"--- AI Feedback: Typos, Placeholders, Accessibility (First ~4k chars, {guideline_ref}) ---")
    results.append(invoke_claude_model(prompt1, max_tokens=1800, temperature=0.2))
    chunk2 = manuscript_text[:6000];
    url_pattern = r'(?:(?:https?|ftp):\/\/|www\.)[\w\/\-?=%.~+#&;]+[\w\/\-?=%.~+#&;]';
    found_urls = re.findall(url_pattern, chunk2)
    urls_to_check_str = "Detected URLs:\n" + "\n".join(list(set(found_urls))[:5]) if found_urls else ""
    prompt2 = f"""KDP policy/quality assistant. Analyze snippet (~{len(chunk2)} chars) ({guideline_ref}). {urls_to_check_str}
    1. Link Guidelines (if URLs detected): Stress links functional/relevant. Warn prohibited types. Advise descriptive text. Remind bonus content placement. User MUST test all links. If no URLs, state that.
    2. Unintentional Duplicated Text: Scan for substantial verbatim repetitions (copy-paste errors). List 2-3 examples. If none, state.
    Snippet: --- {chunk2} --- """
    results.append(f"\n--- AI Feedback: Links & Duplicated Text (First ~6k chars, {guideline_ref}) ---")
    results.append(invoke_claude_model(prompt2, max_tokens=1200, temperature=0.3))
    return results


def ai_check_freely_available_and_infringing_content(title, manuscript_text_snippet,
                                                     guideline_ref="Guideline 1, 3"):  # From your list, uses guideline_ref
    if not manuscript_text_snippet or len(manuscript_text_snippet) < 300: return ["ℹ️ Snippet too short for checks."]
    results = [];
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=[.?!])\s',
                         manuscript_text_snippet.strip())  # Corrected Regex
    candidate_sentences = sorted(list(set(s.strip() for s in sentences if 12 < len(s.split()) < 70 and len(s) > 70)),
                                 key=len, reverse=True)
    if not candidate_sentences:
        results.append("ℹ️ No distinct long sentences for 'freely available' check.")
    else:
        sentences_to_check_count = min(len(candidate_sentences), 3);
        sentences_for_prompt = random.sample(candidate_sentences, sentences_to_check_count)
        prompt_sentences_block = "Sentences to assess:\n" + "".join(
            f"{i + 1}. \"{sent}\"\n" for i, sent in enumerate(sentences_for_prompt))
        prompt_free = f"""{prompt_sentences_block}
        For each: Assess likelihood (Low, Med, High) of being on public web. Justification. Format: "* Sent X: [Likelihood] - [Justification]"
        Conclude: "Per {guideline_ref}, ensure rights. KDP prohibits copyrighted web content unless owner/permission/PD & differentiated. Review policies." Structured list. """
        results.append(f"--- AI Feedback: Snippet Sentences Web Likelihood ({guideline_ref}) ---")
        results.append(invoke_claude_model(prompt_free, max_tokens=800, temperature=0.2))
    prompt_infringing = f"""KDP policy assistant. Title: "{title}", Snippet: "{manuscript_text_snippet[:1000]}..."
    Does this suggest unauthorized summary, study guide, analysis, workbook, companion based on known copyrighted work? Look for: "summary of [Famous Work]", etc.
    If strong signs: State it *might* be perceived as such, explain why. Advise: "Ensure rights/licenses/permissions. Unauthorized companion content can violate copyright/KDP policies ({guideline_ref}). Written permission often required."
    If no strong signs: "Snippet doesn't immediately raise strong concerns as infringing companion. Ensure full work/marketing comply." """
    results.append(f"\n--- AI Feedback: Potential Infringing Companion ({guideline_ref}) ---")
    results.append(invoke_claude_model(prompt_infringing, max_tokens=700, temperature=0.1))
    return results


def ai_check_public_domain_differentiation_statement(is_public_domain, differentiation_statement,
                                                     guideline_ref="Guideline 1"):  # From your list, uses guideline_ref
    if not is_public_domain: return []
    if not differentiation_statement or not differentiation_statement.strip(): return [
        "ℹ️ PD book, but no differentiation statement for AI assessment. Ensure clear in desc. KDP requires substantial differentiation if free version exists."]
    prompt = f"""User states book is PD. Statement: "{differentiation_statement}"
    Assess for KDP's *substantial* differentiation (unique original annotations/analysis, new original translation, unique original illustrations, curated unique collection with original intro/context). Minor formatting/cover changes NOT substantial.
    Assessment: Statement clearly describe substantial differentiation? Sound genuine value-add or minor repackaging? Brief overall assessment. Offer 1-2 actionable bullet points to strengthen if weak/unclear. If strong, say so. Ref {guideline_ref}. """
    return [invoke_claude_model(prompt, max_tokens=700, temperature=0.3)]


def ai_check_language_consistency(metadata_language, manuscript_snippet,
                                  guideline_ref="Guideline 11"):  # From your list, uses guideline_ref
    if not manuscript_snippet or len(manuscript_snippet) < 100: return [
        "ℹ️ Snippet too short for AI language detection."]
    if not metadata_language: return ["ℹ️ Metadata language not selected for AI consistency check."]
    prompt = f"""Analyze primary language of snippet. Respond ONLY with language name (e.g., "English"). If mixed, predominant.
    Snippet: --- {manuscript_snippet[:1500]} --- Detected Language: """
    detected_lang_by_ai = invoke_claude_model(prompt, max_tokens=50, temperature=0.1)
    if detected_lang_by_ai and not detected_lang_by_ai.startswith("Error:") and not detected_lang_by_ai.startswith(
            "Informational:"):
        detected_lang_clean = detected_lang_by_ai.strip().rstrip('.').splitlines()[0]
        meta_lang_norm = metadata_language.lower().split("(")[0].strip();
        ai_lang_norm = detected_lang_clean.lower().split("(")[0].strip()
        if meta_lang_norm == ai_lang_norm or meta_lang_norm in ai_lang_norm or ai_lang_norm in meta_lang_norm:
            return [
                f"✅ **AI Language Check:** AI detected '{detected_lang_clean}' consistent with metadata '{metadata_language}'. {guideline_ref}"]
        else:
            return [
                f"⚠️ **AI Language Mismatch:** Metadata: '{metadata_language}', AI detected: '{detected_lang_clean}'. Ensure match. {guideline_ref}"]
    elif detected_lang_by_ai:
        return [f"ℹ️ AI Language Detection Note: {detected_lang_by_ai}"]
    else:
        return ["⚠️ Could not perform AI language detection on manuscript snippet."]