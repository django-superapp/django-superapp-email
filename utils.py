import re
from html import unescape
from bs4 import BeautifulSoup


def html_to_text(html_content):
    """
    Convert HTML content to plain text
    
    Args:
        html_content: HTML content to convert
        
    Returns:
        Plain text version of the HTML content
    """
    if not html_content:
        return ""
    
    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Replace <br> and <p> tags with newlines
    for tag in soup.find_all(['br', 'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        tag.append('\n')
    
    # Replace <li> tags with "* " prefix and newline
    for li in soup.find_all('li'):
        li.insert_before('* ')
        li.append('\n')
    
    # Get the text
    text = soup.get_text()
    
    # Clean up the text
    text = re.sub(r'\n{3,}', '\n\n', text)  # Replace multiple newlines with double newlines
    text = re.sub(r' {2,}', ' ', text)      # Replace multiple spaces with single space
    text = unescape(text)                   # Unescape HTML entities
    
    return text.strip()
