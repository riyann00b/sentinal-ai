# Sentinel AI - KDP Pre-submission Validation Assistant

**Amazon Internal Hackathon Project**
*Theme: AI Productivity*

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Deployed-brightgreen.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-Amazon%20Confidential-red.svg)](#)

## 🚀 Project Overview

Sentinel AI is an intelligent validation tool designed to assist KDP (Kindle Direct Publishing) authors and publishers by checking their book details, metadata, and manuscript content against common KDP guidelines *before* official submission. The primary goal is to improve publisher productivity, reduce rejection rates and delays, and enhance the overall quality of books published through KDP.

This tool leverages Amazon Bedrock (with the Claude 3 Sonnet model) for AI-powered analysis and Streamlit for the user interface. It aims to simplify and automate a significant portion of daily KDP-related content validation tasks.

**Problem Addressed:**
KDP publishers often face challenges in getting their books approved efficiently due to:
*   High rejection rates stemming from metadata or content errors.
*   Time-consuming delays caused by iterative correction cycles.
*   Difficulty in interpreting KDP's extensive and evolving guidelines.
*   The need for format-specific validation for eBooks, paperbacks, and hardcovers.
*   A significant KDP support burden resulting from preventable, common issues.

**Our Solution: Sentinel AI**
Sentinel AI offers a proactive approach to KDP compliance by providing:
*   **Comprehensive Metadata Validation:** Checks numerous KDP fields against established guidelines.
*   **AI-Powered Content Analysis (Snippets):** Utilizes Claude Sonnet via Bedrock to identify potential issues in manuscript excerpts, such as offensive content, placeholder text, or text that might be freely available online.
*   **Actionable Recommendations:** Delivers specific, AI-generated feedback and actionable suggestions rather than just error flags.
*   **KDP Guideline Awareness:** Educates users on key KDP requirements contextually throughout the data input and validation process.
*   **Productivity Focus:** Aims to catch issues early in the publishing workflow, saving valuable time for both KDP authors/publishers and internal Amazon review teams.

## ✨ Core Features

*   **Interactive KDP Guideline Interface:** Guides users through essential KDP requirements for various aspects of their book setup.
*   **Manuscript Upload & Text Extraction:** Supports common file formats (`.txt`, `.docx`, `.pdf`, `.epub`, `.html`) for content analysis and auto-fill capabilities.
*   **AI-Powered Auto-fill (from Manuscript):** Leverages Bedrock (Claude) to attempt extraction and pre-filling of metadata fields (title, author, language, description draft, etc.) from an uploaded manuscript, minimizing manual data entry.
*   **Extensive Rule-Based Validation Engine:** Systematically checks for common errors related to:
    *   Book Title, Subtitle, and Author Name (length, prohibited content, consistency).
    *   ISBN (format, applicability based on book type like low-content, eBook, print).
    *   Book Language & Format Compatibility (cross-referencing KDP's supported language/format matrix).
    *   AI Content Declaration (ensuring appropriate user input based on KDP's AI content policy).
    *   Low-Content Book Implications (highlighting specific KDP restrictions).
    *   Public Domain Differentiation (checking for statements of unique value).
    *   Series Information (eligibility, title/numbering rules).
    *   Book Description HTML (validating against KDP's supported HTML tags).
    *   Keywords & Categories (count, prohibited terms, redundancy).
    *   Print Specifications (page count vs. trim/ink, bleed/margin calculations based on KDP tables).
    *   Cover Text vs. Metadata Consistency.
*   **In-depth AI-Powered Analysis (via Amazon Bedrock - Claude 3 Sonnet):**
    *   Scan for potential offensive content in manuscript snippets (Guideline 1).
    *   Evaluate book description quality (Simple, Compelling, Professional - Guideline 8).
    *   Suggest and analyze KDP keywords and categories for discoverability (Guideline 9).
    *   Assess manuscript snippets for quality issues (typos, placeholders, links, duplicated text - Guideline 4).
    *   Estimate the likelihood of manuscript text being freely available online (Guideline 1, 3).
    *   Detect potential infringing companion content (Guideline 1, 3).
    *   Review public domain differentiation statements for KDP compliance (Guideline 1).
    *   Check manuscript language consistency against declared metadata language (Guideline 11).
*   **Save/Load Session State:** Allows users to save their entered data as JSON and load it later to resume their work.
*   **Dynamic Submission Readiness Indicator:** Provides a high-level heuristic assessment (e.g., "High Risk," "Review Needed," "Looking Good") based on validation results.
*   **Alignment with Amazon Approved AI Tools:** Exclusively utilizes Amazon Bedrock, adhering to hackathon tool guidelines.

## 🛠️ Technology Stack

*   **Frontend UI:** Streamlit
*   **Backend & Core Logic:** Python
*   **AI Model Invocation:** Amazon Bedrock (Anthropic Claude 3 Sonnet model)
*   **AWS Interaction:** Boto3 (AWS SDK for Python)
*   **File Processing Libraries:** `python-docx`, `PyPDF2`, `EbookLib`, `BeautifulSoup4`
*   **Environment & Package Management:** `uv` (from Astral)

## ⚙️ Setup & Running the Application (with `uv`)

**Prerequisites:**
1.  **uv:** Ensure `uv` is installed. If not, refer to the [official uv documentation](https://github.com/astral-sh/uv) for installation instructions (e.g., `pipx install uv` or `pip install uv`).
2.  **Python:** `uv` will utilize your system's available Python interpreters. This project recommends Python 3.9 or newer.
3.  **AWS Account & Credentials:**
    *   An AWS account with access to Amazon Bedrock.
    *   AWS credentials must be configured in your environment (e.g., via AWS CLI `aws configure`, setting environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_DEFAULT_REGION`, or using an IAM role if deploying to an AWS service).
    *   The credentials/role must have permissions for `bedrock:InvokeModel` action on the `anthropic.claude-3-sonnet-20240229-v1:0` model, specifically in the `us-east-1` region.

**Installation & Environment Setup (using `uv`):**
1.  Clone this repository (or download and extract the project files).
2.  Navigate to the project's root directory (e.g., `sentinel_ai_project/`, where `pyproject.toml` is located) in your terminal.
3.  **Create and activate a virtual environment using `uv`:**
    ```bash
    uv venv sai  # This creates a virtual environment named 'sai_env'
    source sai/bin/activate  # On Linux/macOS
    # .\sai\Scripts\activate  # On Windows PowerShell
    # sai\Scripts\activate.bat # On Windows Command Prompt
    ```
4.  **Install dependencies using `uv` (which reads `pyproject.toml`):**
    Ensure you are in the activated environment (`sai_env`) and in the project's root directory.
    ```bash
    uv pip install .
    ```
    This command installs the project itself and all dependencies listed in the `[project.dependencies]` section of your `pyproject.toml` file.

**Running Sentinel AI:**
1.  Ensure your `uv`-managed virtual environment (`sai_env`) is activated.
2.  Verify that your AWS credentials and default region (expected to be `us-east-1` for Bedrock access) are correctly configured.
3.  From the project's root directory, execute:

    ```bash
    streamlit run sentinel_ai_app.py
    ```
4.  The Sentinel AI application should automatically open in your default web browser.

## 📖 How to Use Sentinel AI

1.  **Launch the App:** Follow the "Running Sentinel AI" instructions above.
2.  **Upload Manuscript (Optional but Highly Recommended):**
    *   In the sidebar, use the "Upload Manuscript" button to select your book's content file.
    *   This enables deeper AI-driven content analysis and the "Auto-fill from Manuscript" feature.
3.  **Auto-fill Details (Optional):**
    *   After a manuscript is successfully uploaded and text is extracted, click the "🤖 Auto-fill from Manuscript" button in the sidebar.
    *   AI will attempt to pre-populate fields such as Title, Author, Language, and draft a Description. **Always review and verify auto-filled information.**
4.  **Enter/Edit Book Details:**
    *   Navigate through the main content tabs: "📘 Core Book & Author," "📝 Description & Discoverability," "🎯 Audience & Special Types," "🤖 AI Content Declaration," and "🖨️ Print Book Setup."
    *   Carefully fill in all relevant details for your book. Tooltips and help text often reference specific KDP guidelines.
5.  **Initiate Validation:**
    *   Once all information is entered to your satisfaction, click the "✨ Validate with Sentinel AI" button in the sidebar.
6.  **Review the Validation Report:**
    *   Sentinel AI will perform comprehensive rule-based checks and AI-powered analyses. This may take a few moments, especially the AI parts.
    *   The results will be displayed in the "📊 Validation Report" section on the main page.
    *   Look for:
        *   ❌ **Errors:** Critical issues that will likely lead to KDP rejection. These must be addressed.
        *   ⚠️ **Warnings:** Potential issues or areas that require careful review against KDP guidelines.
        *   ✅ / ℹ️ **Success/Informational Notes:** Confirmations or helpful tips.
    *   Expand the "Rule-Based Validation Checks" and "AI-Powered Deep Analysis" sections for detailed feedback.
7.  **Iterate and Refine:**
    *   Based on the report, go back to the input tabs to correct any errors or update information.
    *   Modify your manuscript or cover files externally if needed.
    *   Re-upload the manuscript if changes were made to its content.
    *   Re-validate as many times as necessary.
8.  **Save/Load Session (Optional):**
    *   Use "🔗 Generate Sharable Input Data" in the sidebar to get a JSON string of your current inputs. Copy this.
    *   Later, you can paste this JSON into the "Paste saved input data here" box and click "📥 Load Inputs from Data" to restore your session (manuscript files will need to be re-uploaded).

## 🎯 Hackathon Objectives Met

*   **Improve Productivity with AI:** Sentinel AI automates significant portions of KDP guideline cross-referencing and error checking, aiming to simplify critical pre-submission validation tasks for publishers. It provides AI assistance for refining descriptions and keywords.
*   **Upskill Team:** Serves as a practical demonstration of applying Amazon Bedrock (Claude Sonnet) to solve real-world problems in the publishing domain, enhancing AI literacy.
*   **Drive Innovation:** Represents a novel, AI-powered tool conceptualized and developed to directly optimize KDP operational practices.
*   **Accelerate Solutions:** Leverages approved internal AI tools (Bedrock) for rapid prototyping, with a clear path towards delivering production-ready value.
*   **Engineer Experience:** Designed to reduce manual effort, minimize common submission errors, and provide a more streamlined and informed pre-publication process for KDP authors.

## 🔮 Future Enhancements & Vision

*   **Deeper Manuscript Analysis:** Full document parsing for comprehensive formatting checks (e.g., print layout rules beyond basic margins, image placement), image DPI checks.
*   **Cover Image Analysis:** Basic OCR for text matching, resolution checks, and flagging common cover design issues.
*   **Amazon Q Business Integration:** Develop an internal Amazon Q Business application powered by Sentinel AI's knowledge base of KDP guidelines and common publisher pitfalls. This would enable KDP support teams to:
    *   Quickly query specific KDP policies.
    *   Understand the context of issues flagged by Sentinel AI for publishers.
    *   Receive AI-assisted guidance for resolving complex publisher queries, thereby improving support efficiency and consistency.
*   **Enhanced AI Suggestions:** More nuanced AI feedback on plot coherence, character development (from snippets), and advanced marketing copy optimization.
*   **Automated Ticket Triage (Concept):** Explore using AI to categorize common publisher issues flagged by Sentinel AI to suggest routing to appropriate internal support queues.
*   **User Authentication & Profile Management:** For personalized settings and history (post-hackathon).
*   **Direct KDP API Integration (Long-term, if feasible & approved):** To pre-fill KDP setup forms or perform live checks.

## 🤝 Project Team & Contact

*   **[Your Name / Team Member Names]**
*   Primary Contact: `[your_amazon_email@amazon.com]`

---
*Amazon Confidential - For Internal Hackathon Use Only. This tool provides guidance and is not a substitute for carefully reading and adhering to all official KDP Terms and Conditions and Content Guidelines.*