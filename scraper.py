"""
Job Description Scraper Module

Uses requests and BeautifulSoup to extract job description text from URLs.
Includes fallback text cleaning functionality.
"""

import re
from typing import Optional

import requests
from bs4 import BeautifulSoup


class ScrapingError(Exception):
    """Raised when scraping fails (bot detection, access denied, etc.)"""
    pass


def clean_text(text: str) -> str:
    """
    Clean extracted text by removing excessive whitespace, 
    script/style remnants, and normalizing spacing.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text with normalized whitespace
    """
    if not text:
        return ""
    
    # Remove any remaining script/style content markers
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove HTML tags that might have slipped through
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Remove HTML entities
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'&#\d+;', ' ', text)
    
    # Normalize whitespace: replace multiple spaces/tabs with single space
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Normalize newlines: replace multiple newlines with double newline
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Remove leading/trailing whitespace from entire text
    text = text.strip()
    
    return text


def scrape_job_description(url: str, timeout: int = 15) -> str:
    """
    Scrape job description text from a given URL.
    
    Args:
        url: The URL of the job posting
        timeout: Request timeout in seconds
        
    Returns:
        Extracted and cleaned job description text
        
    Raises:
        ScrapingError: If scraping fails due to bot detection, 
                       access denied, or other issues
    """
    # Common headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise ScrapingError(
            f"Request timed out after {timeout} seconds. "
            "The website may be slow or blocking automated requests."
        )
    except requests.exceptions.ConnectionError:
        raise ScrapingError(
            f"Failed to connect to {url}. "
            "Please check the URL and your internet connection."
        )
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else "Unknown"
        if status_code == 403:
            raise ScrapingError(
                "Access denied (403 Forbidden). "
                "This site likely has bot protection (LinkedIn, Naukri, etc.). "
                "Please paste the job description manually."
            )
        elif status_code == 404:
            raise ScrapingError(
                "Page not found (404). Please check if the URL is correct."
            )
        else:
            raise ScrapingError(
                f"HTTP Error {status_code}. Unable to fetch the page."
            )
    except requests.exceptions.RequestException as e:
        raise ScrapingError(f"Request failed: {str(e)}")
    
    # Check for common bot detection indicators in response
    content_lower = response.text.lower()
    bot_indicators = [
        'captcha', 'robot', 'blocked', 'access denied',
        'please verify', 'human verification', 'security check'
    ]
    
    if any(indicator in content_lower for indicator in bot_indicators):
        # Could be a false positive, but warn the user
        if len(response.text) < 5000:  # Short response likely means blocked
            raise ScrapingError(
                "Bot detection triggered. The website requires human verification. "
                "Please paste the job description manually."
            )
    
    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Remove script and style elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        element.decompose()
    
    # Try to find the main content area (common job posting containers)
    job_selectors = [
        {'class_': re.compile(r'job[-_]?description', re.I)},
        {'class_': re.compile(r'job[-_]?details', re.I)},
        {'class_': re.compile(r'description', re.I)},
        {'id': re.compile(r'job[-_]?description', re.I)},
        {'role': 'main'},
        {'class_': 'content'},
    ]
    
    main_content = None
    for selector in job_selectors:
        main_content = soup.find(['div', 'section', 'article', 'main'], **selector)
        if main_content:
            break
    
    # If no specific container found, use body
    if not main_content:
        main_content = soup.find('body') or soup
    
    # Extract text
    text = main_content.get_text(separator='\n')
    
    # Clean the extracted text
    cleaned_text = clean_text(text)
    
    # Validate we got meaningful content
    if len(cleaned_text) < 100:
        raise ScrapingError(
            "Extracted content is too short. "
            "The page may require JavaScript or login. "
            "Please paste the job description manually."
        )
    
    return cleaned_text


def extract_company_name(text: str) -> Optional[str]:
    """
    Attempt to extract company name from job description text.
    Returns None if extraction fails.
    
    Args:
        text: Job description text
        
    Returns:
        Extracted company name or None
    """
    # Common patterns for company names in job postings
    patterns = [
        r'(?:company|organization|employer)[\s:]+([A-Z][A-Za-z0-9\s&.,]+?)(?:\n|$)',
        r'(?:about|join)\s+([A-Z][A-Za-z0-9\s&]+?)(?:\n|$)',
        r'^([A-Z][A-Za-z0-9\s&]+?)\s+(?:is hiring|is looking|seeks)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            # Clean up and validate
            if 3 <= len(company) <= 50:
                return company
    
    return None
