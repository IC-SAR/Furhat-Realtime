import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time
from collections import deque
import re

class SVVSDScraper:
    def __init__(self, base_url, max_pages=100, delay=1):
        """
        Initialize the scraper
        
        Args:
            base_url: Starting URL for scraping
            max_pages: Maximum number of pages to scrape
            delay: Delay between requests in seconds (be respectful!)
        """
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.max_pages = max_pages
        self.delay = delay
        self.visited = set()
        self.to_visit = deque([base_url])
        self.data = []
        
    def is_valid_url(self, url):
        """Check if URL is valid and belongs to the same domain"""
        parsed = urlparse(url)
        
        # Must be same domain
        if parsed.netloc != self.domain:
            return False
        
        # Skip common non-content files
        skip_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', 
                          '.css', '.js', '.ico', '.xml', '.zip', '.doc', '.docx']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
            
        return True
    
    def is_relevant_content(self, soup, url):
        """Determine if page contains relevant SVVSD information"""
        # Keywords that indicate relevance
        relevant_keywords = [
            'school', 'student', 'education', 'district', 'teacher',
            'learning', 'curriculum', 'program', 'calendar', 'board',
            'enrollment', 'staff', 'parent', 'community', 'about',
            'mission', 'vision', 'policy', 'department', 'administration'
        ]
        
        text = soup.get_text().lower()
        url_lower = url.lower()
        
        # Check if URL or content contains relevant keywords
        relevance_score = sum(1 for keyword in relevant_keywords 
                             if keyword in text or keyword in url_lower)
        
        return relevance_score >= 2  # At least 2 keyword matches
    
    def extract_page_data(self, url, soup):
        """Extract structured data from a page"""
        data = {
            'url': url,
            'title': '',
            'main_content': '',
            'headings': [],
            'links': [],
            'metadata': {}
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            data['title'] = title_tag.get_text().strip()
        
        # Extract meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            data['metadata']['description'] = meta_desc.get('content', '')
        
        # Extract headings (h1-h3)
        for i in range(1, 4):
            headings = soup.find_all(f'h{i}')
            for heading in headings:
                text = heading.get_text().strip()
                if text:
                    data['headings'].append({
                        'level': i,
                        'text': text
                    })
        
        # Extract main content
        # Try to find main content areas
        main_content = []
        content_tags = soup.find_all(['p', 'article', 'section', 'div'], 
                                     class_=re.compile(r'content|main|body', re.I))
        
        if not content_tags:
            content_tags = soup.find_all('p')
        
        for tag in content_tags:
            text = tag.get_text().strip()
            if len(text) > 50:  # Only substantial paragraphs
                main_content.append(text)
        
        data['main_content'] = '\n\n'.join(main_content[:20])  # Limit to 20 paragraphs
        
        # Extract all links on the page
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            link_text = link.get_text().strip()
            if link_text:
                data['links'].append({
                    'text': link_text,
                    'href': href
                })
        
        return data
    
    def scrape_page(self, url):
        """Scrape a single page and extract data"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Innovation Center)'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if content is relevant
            if not self.is_relevant_content(soup, url):
                print(f"Skipping irrelevant page: {url}")
                return []
            
            # Extract data
            page_data = self.extract_page_data(url, soup)
            
            # Find new URLs to visit
            new_urls = []
            for link in soup.find_all('a', href=True):
                absolute_url = urljoin(url, link['href'])
                # Remove fragments
                absolute_url = absolute_url.split('#')[0]
                
                if (absolute_url not in self.visited and 
                    absolute_url not in self.to_visit and
                    self.is_valid_url(absolute_url)):
                    new_urls.append(absolute_url)
            
            print(f"✓ Scraped: {url} (found {len(new_urls)} new links)")
            return page_data, new_urls
            
        except Exception as e:
            print(f"✗ Error scraping {url}: {str(e)}")
            return None, []
    
    def scrape(self):
        """Main scraping loop"""
        print(f"Starting scrape of {self.base_url}")
        print(f"Max pages: {self.max_pages}, Delay: {self.delay}s\n")
        
        while self.to_visit and len(self.visited) < self.max_pages:
            url = self.to_visit.popleft()
            
            if url in self.visited:
                continue
            
            self.visited.add(url)
            
            result = self.scrape_page(url)
            if result:
                page_data, new_urls = result
                if page_data:
                    self.data.append(page_data)
                
                # Add new URLs to queue
                self.to_visit.extend(new_urls)
            
            # Be respectful - delay between requests
            time.sleep(self.delay)
        
        print(f"\n✓ Scraping complete! Visited {len(self.visited)} pages")
        return self.data
    
    def save_json(self, filename='svvsd_data.json'):
        """Save data as JSON (good for structured LLM training)"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved JSON to {filename}")
    
    def save_jsonl(self, filename='svvsd_data.jsonl'):
        """Save data as JSONL (preferred for many LLM training pipelines)"""
        with open(filename, 'w', encoding='utf-8') as f:
            for item in self.data:
                # Create a training-friendly format
                training_item = {
                    'text': f"Title: {item['title']}\n\nURL: {item['url']}\n\n{item['main_content']}",
                    'metadata': {
                        'url': item['url'],
                        'title': item['title'],
                        'headings': item['headings']
                    }
                }
                f.write(json.dumps(training_item, ensure_ascii=False) + '\n')
        print(f"✓ Saved JSONL to {filename}")
    
    def save_markdown(self, filename='svvsd_data.md'):
        """Save data as Markdown (human-readable and LLM-friendly)"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# SVVSD Website Data\n\n")
            f.write(f"Scraped from: {self.base_url}\n")
            f.write(f"Total pages: {len(self.data)}\n\n")
            f.write("---\n\n")
            
            for item in self.data:
                f.write(f"## {item['title']}\n\n")
                f.write(f"**URL:** {item['url']}\n\n")
                
                if item['headings']:
                    f.write("**Key Topics:**\n")
                    for heading in item['headings'][:5]:  # Top 5 headings
                        f.write(f"- {heading['text']}\n")
                    f.write("\n")
                
                if item['main_content']:
                    f.write("**Content:**\n\n")
                    f.write(item['main_content'])
                    f.write("\n\n")
                
                f.write("---\n\n")
        
        print(f"✓ Saved Markdown to {filename}")
    
    def save_individual_files(self, output_dir='svvsd_pages'):
        """Save each scraped page as a separate file"""
        import os
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        for idx, item in enumerate(self.data):
            # Create a safe filename from the URL
            url_path = urlparse(item['url']).path
            # Remove leading/trailing slashes and replace slashes with underscores
            safe_name = url_path.strip('/').replace('/', '_')
            
            # If empty (home page), use 'index'
            if not safe_name:
                safe_name = 'index'
            
            # Add index to prevent duplicates and limit length
            filename = f"{idx:03d}_{safe_name[:100]}.txt"
            filepath = os.path.join(output_dir, filename)
            
            # Write the content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"URL: {item['url']}\n")
                f.write(f"Title: {item['title']}\n")
                f.write("=" * 80 + "\n\n")
                
                if item['headings']:
                    f.write("KEY TOPICS:\n")
                    for heading in item['headings']:
                        indent = "  " * (heading['level'] - 1)
                        f.write(f"{indent}- {heading['text']}\n")
                    f.write("\n" + "=" * 80 + "\n\n")
                
                f.write("CONTENT:\n\n")
                f.write(item['main_content'])
                
                if item['metadata'].get('description'):
                    f.write("\n\n" + "=" * 80 + "\n")
                    f.write(f"DESCRIPTION: {item['metadata']['description']}\n")
        
        print(f"✓ Saved {len(self.data)} individual files to '{output_dir}/' directory")
        print(self.data)
        
        # Also create an index file
        index_path = os.path.join(output_dir, '000_INDEX.txt')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("SVVSD SCRAPED PAGES INDEX\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total pages scraped: {len(self.data)}\n")
            f.write(f"Base URL: {self.base_url}\n\n")
            f.write("=" * 80 + "\n\n")
            
            for idx, item in enumerate(self.data):
                url_path = urlparse(item['url']).path.strip('/').replace('/', '_')
                if not url_path:
                    url_path = 'index'
                filename = f"{idx:03d}_{url_path[:100]}.txt"
                f.write(f"{filename}\n")
                f.write(f"  Title: {item['title']}\n")
                f.write(f"  URL: {item['url']}\n\n")
        
        print(f"✓ Created index file: {index_path}")


# Example usage
if __name__ == "__main__":
    scraper = SVVSDScraper(
        base_url="https://innovation.svvsd.org/",
        #base_url="https://www.svvsd.org/",
        max_pages=999_999_999,  # Adjust based on needs
        delay=0.1 # 2 second delay between requests
    )
    
    # Scrape the website
    data = scraper.scrape()
    
    # Save in multiple formats
    #scraper.save_json()      # Structured JSON
    scraper.save_jsonl()     # JSONL for LLM training
    #scraper.save_markdown()  # Human-readable format
    
    print(f"\n✓ All done! Collected data from {len(data)} relevant pages")