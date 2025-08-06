"""Link extractor for BDO patch pages - gets links only, not content"""
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import logging
import re
import hashlib
import time

logger = logging.getLogger(__name__)

class BDOLinkExtractor:
    """Extract patch links for AI processing"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    
    async def extract_global_lab_links(self, base_url: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Extract Global Labs patch links"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        patches = []
                        selectors = [
                            'li:has(a[href*="Detail"])',
                            'tr:has(a[href*="Detail"])',
                            'a[href*="Detail"]'
                        ]
                        
                        for selector in selectors:
                            elements = soup.select(selector)[:limit * 2]
                            if elements:
                                logger.info(f"Found {len(elements)} Global Labs links")
                                
                                for element in elements:
                                    patch_data = self._extract_global_lab_link_data(element, base_url)
                                    if patch_data:
                                        patches.append(patch_data)
                                    if len(patches) >= limit:
                                        break
                                break
                        
                        return patches[:limit]
                        
        except Exception as e:
            logger.error(f"Error extracting Global Labs links: {e}")
        
        return []
    
    async def extract_korean_links(self, base_url: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Extract Korean patch links"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        patches = []
                        selectors = [
                            'li:has(a[href*="Detail"])',
                            'tr:has(a[href*="Detail"])',
                            'a[href*="Detail"]'
                        ]
                        
                        for selector in selectors:
                            elements = soup.select(selector)[:limit * 2]
                            if elements:
                                logger.info(f"Found {len(elements)} Korean links")
                                
                                for element in elements:
                                    patch_data = self._extract_korean_link_data(element, base_url)
                                    if patch_data:
                                        patches.append(patch_data)
                                    if len(patches) >= limit:
                                        break
                                break
                        
                        return patches[:limit]
                        
        except Exception as e:
            logger.error(f"Error extracting Korean links: {e}")
        
        return []
    
    def _extract_global_lab_link_data(self, element, base_url: str) -> Optional[Dict[str, Any]]:
        """Extract Global Labs link data"""
        try:
            # Find link
            link_elem = element.find('a')
            if not link_elem:
                return None
                
            href = link_elem.get('href')
            if not href:
                return None
            
            # Build full URL
            if href.startswith('http'):
                full_url = href
            elif href.startswith('/'):
                full_url = f"https://blackdesert.pearlabyss.com{href}"
            else:
                full_url = f"https://blackdesert.pearlabyss.com/GlobalLab/{href}"
            
            # Extract title
            title = link_elem.get_text(strip=True)
            if not title or len(title) < 5:
                return None
            
            # Extract date from context
            date = self._extract_date_from_element(element) or "Date not found"
            
            # Generate stable ID
            patch_id = self._generate_stable_id(full_url, "globallab")
            
            return {
                'id': patch_id,
                'title': title,
                'date': date,
                'link': full_url,
                'source': 'Global Labs',
                'language': 'english'
            }
            
        except Exception as e:
            logger.error(f"Error extracting Global Labs link data: {e}")
            return None
    
    def _extract_korean_link_data(self, element, base_url: str) -> Optional[Dict[str, Any]]:
        """Extract Korean link data"""
        try:
            # Find link
            link_elem = element.find('a')
            if not link_elem:
                return None
                
            href = link_elem.get('href')
            if not href:
                return None
            
            # Build full URL
            if href.startswith('http'):
                full_url = href
            elif href.startswith('/'):
                full_url = f"https://www.kr.playblackdesert.com{href}"
            else:
                full_url = f"https://www.kr.playblackdesert.com/ko-KR/News/{href}"
            
            # Extract title
            title = link_elem.get_text(strip=True)
            if not title or len(title) < 5:
                return None
            
            # Extract date from context
            date = self._extract_date_from_element(element) or "Date not found"
            
            # Generate stable ID
            patch_id = self._generate_stable_id(full_url, "korean")
            
            return {
                'id': patch_id,
                'title': title,
                'date': date,
                'link': full_url,
                'source': 'Korean Notice',
                'language': 'korean'
            }
            
        except Exception as e:
            logger.error(f"Error extracting Korean link data: {e}")
            return None
    
    def _generate_stable_id(self, url: str, source: str) -> str:
        """Generate stable ID from URL"""
        try:
            # Extract board number from URL
            board_match = re.search(r'[?&]_?boardNo=(\d+)', url, re.IGNORECASE)
            if board_match:
                return f"{source}_{board_match.group(1)}"
            
            # Extract group content number
            group_match = re.search(r'[?&]groupContentNo=(\d+)', url, re.IGNORECASE)
            if group_match:
                return f"{source}_{group_match.group(1)}"
            
            # Fallback to URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            return f"{source}_url_{url_hash}"
            
        except Exception as e:
            logger.error(f"Error generating stable ID: {e}")
            return f"{source}_error_{int(time.time())}"
    
    def _extract_date_from_element(self, element) -> Optional[str]:
        """Extract date from element context"""
        try:
            text = element.get_text()
            
            # Date patterns
            patterns = [
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{4}\.\d{2}\.\d{2})',
                r'(\d{2}/\d{2}/\d{4})',
                r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1)
                    
        except Exception as e:
            logger.error(f"Error extracting date: {e}")
        
        return None
