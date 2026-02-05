"""
HTML to Markdown and Markdown to HTML converters for rich text editing.
"""
import re
from html import escape, unescape


def html_to_markdown(html):
    """
    Convert HTML to Markdown-like syntax for easy editing.
    Preserves formatting like bold, italic, links, headings, lists, etc.
    """
    if not html:
        return ""
    
    text = html
    
    # Convert headings
    for i in range(1, 7):
        text = re.sub(f'<h{i}[^>]*>(.*?)</h{i}>', lambda m: '#' * i + ' ' + m.group(1) + '\n', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert bold+italic combination (nested tags)
    text = re.sub(r'<strong[^>]*>\s*<em[^>]*>(.*?)</em>\s*</strong>', r'***\1***', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<em[^>]*>\s*<strong[^>]*>(.*?)</strong>\s*</em>', r'***\1***', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<b[^>]*>\s*<i[^>]*>(.*?)</i>\s*</b>', r'***\1***', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<i[^>]*>\s*<b[^>]*>(.*?)</b>\s*</i>', r'***\1***', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert bold/strong
    text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert italic/em
    text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert underline
    text = re.sub(r'<u[^>]*>(.*?)</u>', r'__\1__', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert strikethrough
    text = re.sub(r'<s[^>]*>(.*?)</s>', r'~~\1~~', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert links
    text = re.sub(r'<a[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert list items (simplified)
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'• \1\n', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert paragraphs to double newlines
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert line breaks
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    
    # Remove remaining HTML tags but preserve content
    text = re.sub(r'<[^>]+>', '', text)
    
    # Unescape HTML entities
    text = unescape(text)
    
    # Clean up excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def markdown_to_html(markdown):
    """
    Convert Markdown-like syntax to HTML for email sending.
    Supports bold, italic, underline, links, headings, lists, etc.
    """
    if not markdown:
        return ""
    
    html = markdown
    
    # Convert headings (must be at start of line)
    for i in range(6, 0, -1):  # Process from h6 to h1
        pattern = r'^' + '#' * i + r'\s+(.+?)$'
        html = re.sub(pattern, f'<h{i}>\\1</h{i}>', html, flags=re.MULTILINE)
    
    # Convert bold+italic: ***text*** (must be processed BEFORE ** and *)
    html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html)
    
    # Convert bold: **text**
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # Convert italic: *text*
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # Convert underline: __text__
    html = re.sub(r'__(.+?)__', r'<u>\1</u>', html)
    
    # Convert strikethrough: ~~text~~
    html = re.sub(r'~~(.+?)~~', r'<s>\1</s>', html)
    
    # Convert links: [text](url)
    html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Convert bullet points
    lines = html.split('\n')
    in_list = False
    processed_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('•') or stripped.startswith('*') or stripped.startswith('-'):
            if not in_list:
                processed_lines.append('<ul>')
                in_list = True
            # Remove bullet and wrap in <li>
            item_text = re.sub(r'^[•\*\-]\s*', '', stripped)
            processed_lines.append(f'  <li>{item_text}</li>')
        else:
            if in_list:
                processed_lines.append('</ul>')
                in_list = False
            processed_lines.append(line)
    
    if in_list:
        processed_lines.append('</ul>')
    
    html = '\n'.join(processed_lines)
    
    # Convert paragraphs: double newlines become paragraph breaks
    paragraphs = html.split('\n\n')
    html_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if para:
            # Don't wrap if it's already a block element
            if not re.match(r'^\s*<(h[1-6]|ul|ol|li|div|blockquote)', para, re.IGNORECASE):
                # Replace single newlines with <br> within paragraphs
                para = para.replace('\n', '<br>')
                html_paragraphs.append(f'<p>{para}</p>')
            else:
                html_paragraphs.append(para)
    
    html = '\n'.join(html_paragraphs)
    
    return html


def strip_html_to_text(html):
    """
    Strip all HTML tags and return plain text.
    Useful for the subject line.
    """
    if not html:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html)
    
    # Unescape HTML entities
    text = unescape(text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()
