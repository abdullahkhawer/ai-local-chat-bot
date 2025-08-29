#!/usr/bin/env python3
"""
Confluence PDF Downloader

This script downloads all pages from a specified Confluence space in PDF format.
It uses the Confluence REST API to fetch page content and convert it to PDF.

Requirements:
- requests
- pdfkit (optional, for HTML to PDF conversion)
- wkhtmltopdf (system dependency for pdfkit)

Usage:
    python confluence_pdf_downloader.py

Configuration:
    Set the following environment variables or modify the script:
    - CONFLUENCE_URL: Your Confluence instance URL
    - CONFLUENCE_USERNAME: Your username or email
    - CONFLUENCE_API_TOKEN: Your API token or password
    - CONFLUENCE_SPACE_KEY: The space key to download from
"""

import os
import sys
import json
import requests
import urllib.parse
from pathlib import Path
import time
import logging
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('confluence_downloader.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ConfluenceDownloader:
    def __init__(self, base_url: str, username: str, api_token: str, space_key: str):
        """
        Initialize the Confluence downloader.
        
        Args:
            base_url: Confluence instance URL (e.g., 'https://yourcompany.atlassian.net')
            username: Username or email for authentication
            api_token: API token or password
            space_key: Space key to download from
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.space_key = space_key
        self.session = requests.Session()
        self.session.auth = (username, api_token)
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Create output directory
        self.output_dir = Path(f"data")
        self.output_dir.mkdir(exist_ok=True)
        self.output_dir = Path(f"data/confluence_{space_key}")
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"Initialized downloader for space '{space_key}'")
        logger.info(f"Output directory: {self.output_dir.absolute()}")

    def get_space_pages(self, limit: int = 100) -> List[Dict]:
        """
        Get all pages from the specified space.
        
        Args:
            limit: Number of pages to fetch per request
            
        Returns:
            List of page dictionaries
        """
        pages = []
        start = 0
        
        while True:
            url = f"{self.base_url}/wiki/rest/api/content"
            params = {
                'spaceKey': self.space_key,
                'type': 'page',
                'status': 'current',
                'limit': limit,
                'start': start,
                'expand': 'space,version,ancestors'
            }
            
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                current_pages = data.get('results', [])
                pages.extend(current_pages)
                
                logger.info(f"Fetched {len(current_pages)} pages (total: {len(pages)})")
                
                # Check if there are more pages
                if len(current_pages) < limit:
                    break
                    
                start += limit
                time.sleep(0.5)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching pages: {e}")
                break
        
        logger.info(f"Total pages found: {len(pages)}")
        return pages

    def get_page_content_as_pdf(self, page_id: str) -> Optional[bytes]:
        """
        Get page content as PDF using Confluence's export functionality.
        
        Args:
            page_id: The page ID to export
            
        Returns:
            PDF content as bytes, or None if failed
        """
        # Try Confluence Cloud PDF export first
        export_url = f"{self.base_url}/wiki/spaces/{self.space_key}/pdfpageexport.action"
        params = {'pageId': page_id}
        
        try:
            response = self.session.get(export_url, params=params)
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('application/pdf'):
                return response.content
        except Exception as e:
            logger.debug(f"PDF export method 1 failed: {e}")
        
        # Try alternative PDF export URL
        export_url = f"{self.base_url}/wiki/exportword"
        params = {
            'pageId': page_id,
            'exportType': 'PDF'
        }
        
        try:
            response = self.session.get(export_url, params=params)
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('application/pdf'):
                return response.content
        except Exception as e:
            logger.debug(f"PDF export method 2 failed: {e}")
        
        return None

    def get_page_html_content(self, page_id: str) -> Optional[str]:
        """
        Get page content as HTML for manual PDF conversion.
        
        Args:
            page_id: The page ID to fetch
            
        Returns:
            HTML content as string, or None if failed
        """
        url = f"{self.base_url}/wiki/rest/api/content/{page_id}"
        params = {
            'expand': 'body.export_view,space,version,ancestors'
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            html_content = data.get('body', {}).get('export_view', {}).get('value', '')
            return html_content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching HTML content for page {page_id}: {e}")
            return None

    def html_to_pdf(self, html_content: str, output_path: Path) -> bool:
        """
        Convert HTML content to PDF using WeasyPrint (pure Python, no system deps).
        Args:
            html_content: HTML content to convert
            output_path: Path to save the PDF
        Returns:
            True if successful, False otherwise
        """
        try:
            from weasyprint import HTML
            # Add CSS for better formatting
            styled_html = f"""
            <html>
            <head>
                <meta charset=\"UTF-8\">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .page-title {{ font-size: 24px; font-weight: bold; margin-bottom: 20px; }}
                    .content {{ max-width: 100%; }}
                    img {{ max-width: 100%; height: auto; }}
                    /* Force table to fit page using scale if too wide */
                    .table-wrapper {{
                        width: 100%;
                        overflow-x: auto;
                        margin-bottom: 1em;
                        /* PDF hack: scale down wide tables */
                        display: block;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        font-size: 8px;
                        table-layout: fixed;
                        min-width: 600px;
                        max-width: 100vw;
                        overflow-x: auto;
                        display: block;
                        /* If table is too wide, scale it down */
                        transform: scale(0.7);
                        transform-origin: left top;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 2px 4px;
                        text-align: left;
                        word-break: break-all;
                        white-space: pre-line;
                        max-width: 100px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }}
                    th {{
                        background-color: #f2f2f2;
                        font-size: 8px;
                        /* Uncomment to rotate header text for extreme cases */
                        /* writing-mode: vertical-rl; transform: rotate(180deg); */
                    }}
                </style>
            </head>
            <body>
                <div class=\"content\">
                    <div class=\"table-wrapper\">{html_content}</div>
                </div>
            </body>
            </html>
            """
            # Use base_url to resolve relative URIs (e.g., images)
            base_url = self.base_url
            HTML(string=styled_html, base_url=base_url).write_pdf(str(output_path))
            return True
        except ImportError:
            logger.warning("WeasyPrint not installed. Install with: pip install weasyprint")
            return False
        except Exception as e:
            logger.error(f"Error converting HTML to PDF with WeasyPrint: {e}")
            return False

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe file system usage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length and strip whitespace
        filename = filename.strip()[:200]
        
        return filename

    def download_page(self, page: Dict) -> bool:
        """
        Download a single page as PDF.
        
        Args:
            page: Page dictionary from Confluence API
            
        Returns:
            True if successful, False otherwise
        """
        page_id = page['id']
        page_title = page['title']
        
        logger.info(f"Downloading page: {page_title} (ID: {page_id})")
        
        # Create filename
        safe_title = self.sanitize_filename(page_title)
        pdf_filename = f"{safe_title}_{page_id}.pdf"
        output_path = self.output_dir / pdf_filename
        
        # Skip if already exists
        if output_path.exists():
            logger.info(f"File already exists, skipping: {pdf_filename}")
            return True
        else:
            # Rate limiting
            time.sleep(1)
        
        # Try to get PDF directly from Confluence
        pdf_content = self.get_page_content_as_pdf(page_id)
        
        if pdf_content:
            try:
                with open(output_path, 'wb') as f:
                    f.write(pdf_content)
                logger.info(f"Successfully downloaded PDF: {pdf_filename}")
                return True
            except Exception as e:
                logger.error(f"Error saving PDF {pdf_filename}: {e}")
                return False
        
        # Fallback: Get HTML and convert to PDF
        logger.info(f"PDF export not available, trying HTML conversion for: {page_title}")
        html_content = self.get_page_html_content(page_id)
        
        if html_content:
            # Add page title to HTML
            html_with_title = f'<div class="page-title">{page_title}</div>{html_content}'
            
            if self.html_to_pdf(html_with_title, output_path):
                logger.info(f"Successfully converted HTML to PDF: {pdf_filename}")
                return True
            else:
                # Save as HTML if PDF conversion fails
                html_filename = f"{safe_title}_{page_id}.html"
                html_path = self.output_dir / html_filename
                try:
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(f'<h1>{page_title}</h1>{html_content}')
                    logger.info(f"Saved as HTML instead: {html_filename}")
                    return True
                except Exception as e:
                    logger.error(f"Error saving HTML {html_filename}: {e}")
                    return False
        
        logger.error(f"Failed to download page: {page_title}")
        return False

    def download_all_pages(self):
        """Download all pages from the space."""
        logger.info(f"Starting download of all pages from space: {self.space_key}")
        
        pages = self.get_space_pages()
        if not pages:
            logger.error("No pages found or error fetching pages")
            return
        
        successful_downloads = 0
        failed_downloads = 0
        
        for i, page in enumerate(pages, 1):
            logger.info(f"Processing page {i}/{len(pages)}")
            
            if self.download_page(page):
                successful_downloads += 1
            else:
                failed_downloads += 1

        logger.info(f"Download completed!")
        logger.info(f"Successful downloads: {successful_downloads}")
        logger.info(f"Failed downloads: {failed_downloads}")
        logger.info(f"Files saved to: {self.output_dir.absolute()}")

def main():
    """Main function to run the downloader."""
    print("Confluence PDF Downloader")
    print("=" * 40)
    
    # Get configuration from environment variables or user input
    confluence_url = os.getenv('CONFLUENCE_URL')
    if not confluence_url:
        confluence_url = input("Enter Confluence URL (e.g., https://yourcompany.atlassian.net): ").strip()
    
    username = os.getenv('CONFLUENCE_USERNAME')
    if not username:
        username = input("Enter username/email: ").strip()
    
    api_token = os.getenv('CONFLUENCE_API_TOKEN')
    if not api_token:
        api_token = input("Enter API token/password: ").strip()
    
    space_key = os.getenv('CONFLUENCE_SPACE_KEY')
    if not space_key:
        space_key = input("Enter space key: ").strip()
    
    if not all([confluence_url, username, api_token, space_key]):
        print("Error: All configuration values are required")
        sys.exit(1)
    
    try:
        downloader = ConfluenceDownloader(confluence_url, username, api_token, space_key)
        downloader.download_all_pages()
        
    except KeyboardInterrupt:
        print("\nDownload interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
