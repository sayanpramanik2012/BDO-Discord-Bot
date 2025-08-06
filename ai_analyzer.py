"""AI Deep Analyzer for BDO patches using Gemini"""
import google.generativeai as genai
import logging
import os
import aiofiles
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class BDOAIAnalyzer:
    """Deep AI analysis of BDO patches using direct URL access"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.reports_folder = "patch_reports"
        os.makedirs(self.reports_folder, exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def generate_deep_report(self, patch_data: Dict[str, Any]) -> Optional[str]:
        """Generate comprehensive analysis report for patch"""
        try:
            # Get full content from URL
            full_content = await self._extract_full_content(patch_data['link'])
            if not full_content:
                logger.error(f"Failed to extract content from {patch_data['link']}")
                return None
            
            # Create comprehensive analysis prompt
            analysis_prompt = self._create_analysis_prompt(patch_data, full_content)
            
            # Safe logging for Korean titles
            from utils.helpers import safe_log_message
            safe_title = safe_log_message(patch_data['title'][:50])
            logger.info(f"Generating deep analysis for {patch_data['source']} patch: {safe_title}...")
            
            response = self.model.generate_content(analysis_prompt)
            
            if response and response.text:
                # Create formatted report
                report = self._format_final_report(patch_data, response.text)
                
                # Save to file
                filename = await self._save_report_to_file(patch_data, report)
                
                logger.info(f"Generated and saved deep analysis report: {filename}")
                return filename
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating deep report: {e}")
            return None

    async def _extract_full_content(self, url: str) -> Optional[str]:
        """Extract full content from patch URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Remove unwanted elements
                        for unwanted in soup.select('script, style, nav, header, footer, .header_wrap'):
                            unwanted.decompose()
                        
                        # Extract content from specific areas
                        content_selectors = [
                            '.contents_area.editor_area .mceTmpl',
                            '.contents_area.editor_area',
                            '.view-content',
                            '.article-content',
                            '.board-view-content'
                        ]
                        
                        for selector in content_selectors:
                            content_div = soup.select_one(selector)
                            if content_div:
                                text = content_div.get_text(separator=' ', strip=True)
                                if len(text) > 200:  # Ensure substantial content
                                    return text
                        
                        # Fallback
                        body = soup.find('body')
                        if body:
                            return body.get_text(separator=' ', strip=True)[:10000]
                        
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
        
        return None
    
    def _create_analysis_prompt(self, patch_data: Dict[str, Any], content: str) -> str:
        """Create comprehensive analysis prompt for Gemini"""
        
        prompt = f"""
You are a professional Black Desert Online intelligence analyst. Create a comprehensive, detailed analysis report of this patch/update.

PATCH INFORMATION:
- Title: {patch_data['title']}
- Date: {patch_data['date']}
- Source: {patch_data['source']}
- Language: {patch_data['language']}

ANALYSIS REQUIREMENTS:
1. **Executive Summary** (2-3 paragraphs)
   - Overall significance of this update
   - Key strategic implications for players
   - Meta impact assessment

2. **Detailed Content Analysis**
   - New content additions (if any)
   - Class balance changes with specific impact analysis
   - System improvements and QoL updates
   - Bug fixes and technical changes

3. **Strategic Impact Assessment**
   - PvP meta implications
   - PvE progression changes
   - Economic/market effects
   - Guild and large-scale PvP impacts

4. **Player Action Items**
   - Immediate priorities for different player types
   - Gear/build adjustments needed
   - New strategies to adopt
   - Things to avoid or discontinue

5. **Competitive Intelligence**
   - Advantages for prepared players
   - Market opportunities
   - Resource allocation recommendations
   - Timing considerations

6. **Technical Details**
   - Specific numerical changes (if mentioned)
   - Skill modifications with before/after comparison
   - New mechanics explanations

CONTENT TO ANALYZE:
{content[:8000]}

Generate a professional, comprehensive report suitable for competitive players. Use clear headings, bullet points, and strategic insights. If content is in Korean, provide analysis in English but mention original Korean terms where relevant.
"""
        
        return prompt
    
    def _format_final_report(self, patch_data: Dict[str, Any], ai_analysis: str) -> str:
        """Format the final report with metadata"""
        
        header = f"""BLACK DESERT ONLINE - INTELLIGENCE REPORT
{'='*60}

PATCH INFORMATION:
- Title: {patch_data['title']}
- Date: {patch_data['date']}
- Source: {patch_data['source']}
- Original URL: {patch_data['link']}
- Analysis Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
- Report ID: {patch_data['id']}

{'='*60}

"""
        
        footer = f"""

{'='*60}
Report Generated by BDO Intelligence Division
AI Analysis Model: Gemini-1.5-Flash
Classification: Comprehensive Analysis
Distribution: Community & Competitive Players
{'='*60}
"""
        
        return header + ai_analysis + footer
    
    async def _save_report_to_file(self, patch_data: Dict[str, Any], report: str) -> str:
        """Save report to .txt file"""
        try:
            # Generate filename
            source_clean = patch_data['source'].lower().replace(' ', '_').replace('labs', 'lab')
            date_str = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"{source_clean}_{patch_data['id']}_{date_str}.txt"
            filepath = os.path.join(self.reports_folder, filename)
            
            # Save file
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(report)
            
            return filename
            
        except Exception as e:
            logger.error(f"Error saving report to file: {e}")
            return None
    
    def get_latest_report_file(self, source: str) -> Optional[str]:
        """Get the latest report file for a source"""
        try:
            source_clean = source.lower().replace(' ', '_').replace('labs', 'lab')
            
            # Find files matching the source
            matching_files = []
            for filename in os.listdir(self.reports_folder):
                if filename.startswith(source_clean) and filename.endswith('.txt'):
                    filepath = os.path.join(self.reports_folder, filename)
                    matching_files.append((filepath, os.path.getctime(filepath)))
            
            if matching_files:
                # Sort by creation time, return most recent
                latest_file = max(matching_files, key=lambda x: x[1])
                return latest_file[0]
                
        except Exception as e:
            logger.error(f"Error getting latest report file: {e}")
        
        return None
