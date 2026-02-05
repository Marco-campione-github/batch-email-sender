import re
from auth import get_docs_service


def extract_document_id(doc_input):
    """
    Extract document ID from either a Google Docs URL or direct ID.
    
    Supports formats:
    - https://docs.google.com/document/d/DOCUMENT_ID/edit
    - DOCUMENT_ID
    """
    # Pattern to match Google Docs URL
    url_pattern = r'docs\.google\.com/document/d/([a-zA-Z0-9-_]+)'
    match = re.search(url_pattern, doc_input)
    
    if match:
        return match.group(1)
    
    # Assume it's already a document ID
    return doc_input.strip()


def read_google_doc(doc_input):
    """
    Fetch and parse a Google Doc to extract Subject and Body.
    
    Expected format:
    ===SUBJECT===
    Your subject here
    
    ===BODY===
    Your email body here...
    
    Returns a dict with 'subject' (plain text), 'body' (plain text),
    and 'body_html' (formatted HTML) keys.
    """
    doc_id = extract_document_id(doc_input)
    
    try:
        docs_service = get_docs_service()
        document = docs_service.documents().get(documentId=doc_id).execute()
        
        content = document.get('body', {}).get('content', [])
        lists = document.get('lists', {})
        
        # Extract both plain text and HTML
        full_text = extract_text_from_content(content)
        full_html = extract_html_from_content(content, lists)
        
        # Parse plain text for display in UI
        subject_plain, body_plain = parse_doc_content_text(full_text)
        
        # Parse HTML for email sending
        subject_html, body_html = parse_doc_content_html(full_html)
        
        return {
            'subject': subject_plain,
            'body': body_plain,
            'body_html': body_html
        }
    except Exception as e:
        raise Exception(f"Failed to read Google Doc: {str(e)}")


def extract_text_from_content(content):
    """
    Extract plain text from Google Docs content structure.
    """
    text_parts = []
    
    for element in content:
        if 'paragraph' in element:
            paragraph = element['paragraph']
            if 'elements' in paragraph:
                for elem in paragraph['elements']:
                    if 'textRun' in elem:
                        text_content = elem['textRun'].get('content', '')
                        text_parts.append(text_content)
    
    return ''.join(text_parts)


def extract_html_from_content(content, lists):
    """
    Extract HTML from Google Docs content structure, preserving formatting.
    
    Supports:
    - Bold, Italic, Underline, Strikethrough
    - Links
    - Headings (H1-H6)
    - Font sizes and colors
    - Bullet and numbered lists
    - Paragraphs and line breaks
    """
    html_parts = []
    
    for element in content:
        if 'paragraph' in element:
            paragraph = element['paragraph']
            paragraph_html = convert_paragraph_to_html(paragraph, lists)
            if paragraph_html:
                html_parts.append(paragraph_html)
    
    return ''.join(html_parts)


def convert_paragraph_to_html(paragraph, lists):
    """
    Convert a Google Docs paragraph to HTML.
    """
    if 'elements' not in paragraph:
        return ''
    
    # Check if this is a list item
    bullet = paragraph.get('bullet')
    list_id = bullet.get('listId') if bullet else None
    nesting_level = bullet.get('nestingLevel', 0) if bullet else None
    
    # Get paragraph style (for headings)
    para_style = paragraph.get('paragraphStyle', {})
    named_style = para_style.get('namedStyleType', 'NORMAL_TEXT')
    
    # Build the text content with inline formatting
    text_html = ''
    for elem in paragraph['elements']:
        if 'textRun' in elem:
            text_run = elem['textRun']
            content = text_run.get('content', '')
            text_style = text_run.get('textStyle', {})
            
            # Apply formatting to this text run
            formatted_text = apply_text_formatting(content, text_style)
            text_html += formatted_text
    
    # Skip empty paragraphs (except if they're just newlines)
    if not text_html.strip():
        return '<br>'
    
    # Wrap in appropriate HTML tag based on style
    if named_style.startswith('HEADING_'):
        level = named_style.split('_')[1]
        return f'<h{level}>{text_html}</h{level}>'
    elif list_id:
        # List items - we'll wrap with <li>
        # Note: This is a simplified approach. Full list handling would require
        # tracking list start/end across multiple paragraphs
        return f'<li>{text_html}</li>'
    else:
        return f'<p>{text_html}</p>'


def apply_text_formatting(text, text_style):
    """
    Apply text formatting (bold, italic, color, etc.) to text.
    Returns HTML string.
    """
    if not text:
        return ''
    
    # Build inline styles
    styles = []
    
    # Font size
    if 'fontSize' in text_style:
        size = text_style['fontSize'].get('magnitude', 11)
        styles.append(f'font-size: {size}pt')
    
    # Text color
    if 'foregroundColor' in text_style:
        color = text_style['foregroundColor'].get('color', {})
        rgb_color = color.get('rgbColor', {})
        if rgb_color:
            r = int(rgb_color.get('red', 0) * 255)
            g = int(rgb_color.get('green', 0) * 255)
            b = int(rgb_color.get('blue', 0) * 255)
            styles.append(f'color: rgb({r}, {g}, {b})')
    
    # Background color
    if 'backgroundColor' in text_style:
        color = text_style['backgroundColor'].get('color', {})
        rgb_color = color.get('rgbColor', {})
        if rgb_color:
            r = int(rgb_color.get('red', 0) * 255)
            g = int(rgb_color.get('green', 0) * 255)
            b = int(rgb_color.get('blue', 0) * 255)
            styles.append(f'background-color: rgb({r}, {g}, {b})')
    
    # Font family
    if 'fontFamily' in text_style:
        font = text_style['fontFamily']
        styles.append(f'font-family: {font}')
    
    # Build style attribute
    style_attr = f' style="{"; ".join(styles)}"' if styles else ''
    
    # Apply HTML tags for formatting
    html = text
    
    # Bold
    if text_style.get('bold'):
        html = f'<strong>{html}</strong>'
    
    # Italic
    if text_style.get('italic'):
        html = f'<em>{html}</em>'
    
    # Underline
    if text_style.get('underline'):
        html = f'<u>{html}</u>'
    
    # Strikethrough
    if text_style.get('strikethrough'):
        html = f'<s>{html}</s>'
    
    # Link
    if 'link' in text_style:
        url = text_style['link'].get('url', '')
        if url:
            html = f'<a href="{url}">{html}</a>'
    
    # Wrap in span with styles if we have any
    if style_attr:
        html = f'<span{style_attr}>{html}</span>'
    
    return html


def parse_doc_content_text(text):
    """
    Parse plain text to extract Subject and Body sections.
    
    Required format:
    ===SUBJECT===
    Your subject here
    
    ===BODY===
    Your body here...
    """
    subject = ""
    body = ""
    
    # Extract content after ===SUBJECT=== and before ===BODY===
    subject_match = re.search(r'===\s*SUBJECT\s*===\s*\n(.+?)(?=\n\s*===\s*BODY\s*===|\Z)', text, re.DOTALL | re.IGNORECASE)
    if subject_match:
        subject = subject_match.group(1).strip()
    
    # Extract content after ===BODY===
    body_match = re.search(r'===\s*BODY\s*===\s*\n(.+)', text, re.DOTALL | re.IGNORECASE)
    if body_match:
        body = body_match.group(1).strip()
    
    return subject, body


def parse_doc_content_html(html):
    """
    Parse the document HTML to extract Subject and Body sections.
    
    Required format:
    ===SUBJECT===
    Your subject here
    
    ===BODY===
    Your body here...
    """
    subject = ""
    body = ""
    
    # Extract content after ===SUBJECT=== and before ===BODY===
    subject_match = re.search(r'===\s*SUBJECT\s*===\s*</[^>]+>(.+?)(?=<[^>]+>===\s*BODY\s*===|\Z)', html, re.DOTALL | re.IGNORECASE)
    if subject_match:
        subject_html = subject_match.group(1).strip()
        # Remove HTML tags and normalize whitespace for subject
        subject = re.sub(r'<[^>]+>', ' ', subject_html).strip()
        subject = re.sub(r'\s+', ' ', subject)  # Normalize whitespace
    
    # Extract content after ===BODY===
    body_match = re.search(r'===\s*BODY\s*===\s*</[^>]+>(.+)', html, re.DOTALL | re.IGNORECASE)
    if body_match:
        body = body_match.group(1).strip()
    
    return subject, body
