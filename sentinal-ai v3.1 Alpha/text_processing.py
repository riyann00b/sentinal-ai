# text_processing.py
from io import StringIO, BytesIO
import docx  # pip install python-docx

# Attempt to import optional libraries and set them to None if not found
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from ebooklib import epub
    import ebooklib  # For ebooklib.ITEM_DOCUMENT
except ImportError:
    epub = None
    ebooklib = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


def get_library_warnings():
    warnings = []
    if PyPDF2 is None:
        warnings.append(
            "PyPDF2 library not found. PDF processing will be unavailable. Install with: pip install PyPDF2")
    if epub is None or ebooklib is None:
        warnings.append(
            "EbookLib library not found. EPUB processing will be unavailable. Install with: pip install EbookLib")
    if BeautifulSoup is None:
        warnings.append(
            "BeautifulSoup4 library not found. EPUB/HTML processing will be impacted. Install with: pip install beautifulsoup4")
    return warnings


def extract_text_from_file(uploaded_file):
    if uploaded_file is None:
        return "", "No file uploaded."

    file_name = uploaded_file.name.lower()
    text_content = ""
    error_message = None
    warning_message = None

    try:
        if file_name.endswith(".txt"):
            file_bytes = uploaded_file.getvalue()
            try:
                text_content = StringIO(file_bytes.decode("utf-8")).read()
            except UnicodeDecodeError:
                try:
                    text_content = StringIO(file_bytes.decode("latin-1")).read()
                    warning_message = f"File '{uploaded_file.name}' decoded as latin-1 after utf-8 failed."
                except Exception as e_latin1:
                    error_message = f"Could not decode .txt file '{uploaded_file.name}' with utf-8 or latin-1: {str(e_latin1)[:100]}..."

        elif file_name.endswith(".docx"):
            if docx:
                doc = docx.Document(BytesIO(uploaded_file.getvalue()))
                text_content = '\n'.join([para.text for para in doc.paragraphs])
            else:
                error_message = "python-docx library not available. Cannot process .docx files."

        elif file_name.endswith(".pdf"):
            if PyPDF2:
                try:
                    pdf_reader = PyPDF2.PdfReader(BytesIO(uploaded_file.getvalue()))
                    if not pdf_reader.pages:
                        warning_message = f"Warning: PDF file '{uploaded_file.name}' appears to be empty or unreadable (no pages found)."
                    else:
                        for page_num, page in enumerate(pdf_reader.pages):
                            page_text = page.extract_text()
                            if page_text:
                                text_content += page_text + "\n"
                        if not text_content.strip() and pdf_reader.pages:
                            warning_message = f"Warning: PDF file '{uploaded_file.name}' was processed, but no text could be extracted. It might be an image-based PDF or have extraction issues."
                except Exception as e_pdf:
                    error_message = f"Error processing PDF '{uploaded_file.name}': {str(e_pdf)[:150]}... Ensure it's not password-protected or corrupted."
            else:
                error_message = "PyPDF2 library not available. Cannot process .pdf files."

        elif file_name.endswith(".epub"):
            if epub and BeautifulSoup and ebooklib:
                try:
                    book_bytes = BytesIO(uploaded_file.getvalue())
                    book = epub.read_epub(book_bytes)
                    processed_items = 0
                    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                        content_bytes = item.get_content()
                        content_html_str = ""
                        if isinstance(content_bytes, bytes):
                            try:
                                content_html_str = content_bytes.decode('utf-8',
                                                                        errors='replace')  # Use replace for robustness
                            except Exception as e_decode:
                                # Log this or add to warning if necessary
                                print(
                                    f"DEBUG: EPUB item decoding error {e_decode}, trying latin-1 for item {item.get_name()}")
                                try:
                                    content_html_str = content_bytes.decode('latin-1', errors='replace')
                                except:
                                    pass  # Give up on this item if both fail
                        elif isinstance(content_bytes, str):
                            content_html_str = content_bytes

                        if content_html_str:
                            soup = BeautifulSoup(content_html_str, 'html.parser')
                            for script_or_style in soup(["script", "style"]):
                                script_or_style.decompose()
                            extracted_item_text = soup.get_text(separator='\n', strip=True)
                            if extracted_item_text:
                                text_content += extracted_item_text + "\n\n"
                                processed_items += 1
                    if processed_items == 0 and not text_content:  # If no items of type document or no text from them
                        warning_message = f"Warning: EPUB '{uploaded_file.name}' processed, but no text content found in document items. Structure might be unusual or empty."

                except Exception as e_epub:
                    error_message = f"Error processing EPUB '{uploaded_file.name}': {str(e_epub)[:150]}..."
            else:
                error_message = "EbookLib or BeautifulSoup4 not available. Cannot process .epub files."

        elif file_name.endswith((".html", ".htm", ".xhtml")):
            if BeautifulSoup:
                html_bytes = uploaded_file.getvalue()
                html_content_str = ""
                if isinstance(html_bytes, bytes):
                    try:
                        html_content_str = html_bytes.decode('utf-8', errors='replace')
                    except UnicodeDecodeError:
                        try:
                            html_content_str = html_bytes.decode('latin-1', errors='replace')
                            warning_message = f"File '{uploaded_file.name}' (HTML) decoded as latin-1 after utf-8 failed."
                        except Exception as e_decode_html:
                            error_message = f"Could not decode HTML file '{uploaded_file.name}' with utf-8 or latin-1: {e_decode_html}"
                elif isinstance(html_bytes, str):
                    html_content_str = html_bytes

                if html_content_str and not error_message:
                    soup = BeautifulSoup(html_content_str, 'html.parser')
                    for script_or_style in soup(["script", "style"]):
                        script_or_style.decompose()
                    text_content = soup.get_text(separator='\n', strip=True)
                elif not error_message:  # If html_content_str is empty but no decode error
                    warning_message = f"HTML file '{uploaded_file.name}' appears to be empty."

            else:
                error_message = "BeautifulSoup4 not available. Cannot process HTML files."
        else:
            warning_message = f"Unsupported file type for text extraction: '{uploaded_file.name}'. Please upload .txt, .docx, .pdf, .epub, or .html."
            # No return here, let it fall through to general error/warning handling

    except Exception as e:
        # Catch-all for unexpected errors during processing a specific file type
        error_message = f"General error processing file '{uploaded_file.name}' (type: {file_name.split('.')[-1]}): {str(e)[:150]}..."

    final_text = text_content.strip()
    if error_message:
        return "", error_message  # Prioritize error message

    # If no specific error/warning yet, but no text extracted for a supported type
    if not final_text and not warning_message and uploaded_file and not file_name.endswith(
            (".txt", ".docx", ".pdf", ".epub", ".html", ".htm",
             ".xhtml")):  # This condition is likely redundant if the top 'else' for unsupported type handles it
        pass  # Already handled by unsupported type message
    elif not final_text and not warning_message and uploaded_file:
        warning_message = f"File '{uploaded_file.name}' processed, but resulted in empty text content. Please check the file."

    return final_text, warning_message