"""AI Deep Analyzer for BDO patches using Gemini with Direct URL Analysis"""
import logging
import os
import aiofiles
from datetime import datetime
from typing import Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)

class BDOAIAnalyzer:
    """Deep AI analysis of BDO patches using direct URL access"""
    
    def __init__(self, api_key: str):
        self.model = Config.initialize_gemini()
        self.reports_folder = "patch_reports"
        os.makedirs(self.reports_folder, exist_ok=True)
        
        # Use config limits
        self.max_content_length = Config.MAX_TRANSLATION_LENGTH
        self.max_analysis_length = Config.MAX_SUMMARY_LENGTH
    
    async def generate_deep_report(self, patch_data: Dict[str, Any]) -> Optional[str]:
        """Generate comprehensive analysis report by passing URL directly to AI"""
        try:
            # Create comprehensive analysis prompt with URL
            analysis_prompt = self._create_url_analysis_prompt(patch_data)
            
            # Safe logging for Korean titles
            from utils.helpers import safe_log_message
            safe_title = safe_log_message(patch_data['title'][:50])
            logger.info(f"Generating deep analysis via direct URL for {patch_data['source']}: {safe_title}...")
            
            # Pass URL directly to Gemini for analysis
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
    
    def _create_url_analysis_prompt(self, patch_data: Dict[str, Any]) -> str:
        """Create comprehensive analysis prompt that includes the URL for direct access"""
        
        # Check if this is a maintenance update
        maintenance_keywords = ['maintenance', 'server maintenance', 'scheduled maintenance', 
                              'hotfix', '정기점검', '임시점검', '서버점검']
        is_maintenance = any(keyword in patch_data['title'].lower() for keyword in maintenance_keywords)
        
        if is_maintenance:
            prompt = f"""
Please access and analyze the content from this URL: {patch_data['link']}

PATCH INFORMATION:
- Title: {patch_data['title']}
- Date: {patch_data['date']}
- Source: {patch_data['source']}

This appears to be a maintenance update. Please access the URL and provide a brief summary focusing on:
- Server downtime details
- Any critical fixes mentioned
- Impact on players

Keep the analysis concise for maintenance updates.
"""
        else:
            prompt = f"""
Please access and analyze the Black Desert Online patch content from this URL: {patch_data['link']}

PATCH INFORMATION:
- Title: {patch_data['title']}
- Date: {patch_data['date']}
- Source: {patch_data['source']}

You are a senior Black Desert Online intelligence analyst. After accessing the URL, create an extremely detailed, comprehensive analysis report.

REQUIRED DETAILED ANALYSIS SECTIONS (Target: {Config.MAX_SUMMARY_LENGTH} characters total):

1. **EXECUTIVE SUMMARY** (4-5 paragraphs)
   - Overall significance and strategic implications
   - Key meta changes and their impact
   - Priority actions for competitive players

2. **EVENTS ANALYSIS** (Comprehensive Detail)
   - New events starting (rewards, duration, requirements, strategies)
   - Ongoing events changes or extensions with specific details
   - Event optimization tips and economic impact analysis
   - Time-sensitive recommendations for players

3. **CLASS & CHARACTER CHANGES** (Extremely Detailed)
   - List each class with specific skill changes
   - Exact damage numbers, cooldown modifications, range adjustments
   - PvP impact analysis with before/after scenarios
   - PvE efficiency changes with grinding speed implications
   - Awakening vs Succession detailed comparisons
   - Recommended skill rotations and build adjustments

4. **ITEMS & EQUIPMENT** (Comprehensive Analysis)
   - New items added (exact stats, acquisition methods, drop rates)
   - Item balance changes and enhancement system modifications
   - Cash shop additions with cost-benefit analysis
   - Market economy predictions and trading opportunities
   - Gear progression path updates and investment recommendations

5. **MONSTER ZONES & CONTENT** (Detailed Breakdown)
   - New hunting zones with exact location and requirements
   - Monster spawn rate, behavior, and difficulty changes
   - Loot table modifications with drop rate analysis
   - Grinding efficiency calculations and silver/hour projections
   - Zone-specific strategies and optimal grinding routes

6. **FIXES & TECHNICAL CHANGES** (Complete Analysis)
   - Bug fixes with detailed explanation of what was broken
   - System performance improvements and their practical benefits
   - UI/UX modifications and accessibility improvements
   - Server stability enhancements and connection improvements

7. **NEW CONTENT & FEATURES** (Full Exploration)
   - Completely new systems with detailed mechanics explanation
   - New dungeons, raids, or PvP modes with strategies
   - Story content, quest additions, and reward analysis
   - Housing, lifeskill, or social feature detailed guides
   - Integration impact with existing game systems

8. **STRATEGIC INTELLIGENCE** (Advanced Analysis)
   - Competitive advantages for prepared players
   - Market manipulation opportunities and economic predictions
   - Guild warfare tactical implications and siege strategies
   - Resource allocation optimization and investment priorities
   - Timing strategies for maximum benefit from changes

9. **PLAYER ACTION ITEMS** (Specific Recommendations)
   - Immediate priorities categorized by player type
   - Exact gear pieces to acquire, enhance, or sell
   - Skill point allocation and succession/awakening choices
   - Daily/weekly routine adjustments for maximum efficiency
   - Long-term planning recommendations and goal setting

For each section, provide specific details, exact numbers where available, and strategic insights. Use bullet points and clear formatting. If any section does not exist in the patch, state that clearly.

Access the URL directly and analyze ALL content thoroughly. Generate a comprehensive intelligence report with maximum detail suitable for competitive players and guilds.
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
- AI Model: {Config.GEMINI_MODEL}
- Analysis Method: Direct URL Access
- Analysis Length: {len(ai_analysis)} characters

{'='*60}

"""
        
        footer = f"""

{'='*60}
Report Generated by BDO Intelligence Division
AI Analysis Model: {Config.GEMINI_MODEL}
Classification: Comprehensive Analysis
Max Content Length: {Config.MAX_TRANSLATION_LENGTH}
Max Analysis Length: {Config.MAX_SUMMARY_LENGTH}
Analysis Method: Direct URL Processing
Distribution: Community & Competitive Players
{'='*60}
"""
        
        return header + ai_analysis + footer
    
    async def _save_report_to_file(self, patch_data: Dict[str, Any], report: str) -> str:
        """Save report to .txt file with enhanced metadata"""
        try:
            # Generate filename with more descriptive naming
            source_clean = patch_data['source'].lower().replace(' ', '_').replace('labs', 'lab')
            date_str = datetime.now().strftime('%Y%m%d_%H%M')
            
            # Include model name in filename for tracking
            model_clean = Config.GEMINI_MODEL.replace('-', '_').replace('.', '_')
            filename = f"{source_clean}_{patch_data['id']}_{model_clean}_url_{date_str}.txt"
            filepath = os.path.join(self.reports_folder, filename)
            
            # Save file with UTF-8 encoding
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(report)
            
            # Log file creation with size info
            file_size = len(report.encode('utf-8'))
            logger.info(f"Saved report: {filename} ({file_size:,} bytes)")
            
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
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get current model configuration info"""
        return {
            'model_name': Config.GEMINI_MODEL,
            'max_content_length': Config.MAX_TRANSLATION_LENGTH,
            'max_analysis_length': Config.MAX_SUMMARY_LENGTH,
            'supported_languages': list(Config.SUPPORTED_LANGUAGES.keys()),
            'analysis_method': 'Direct URL Access'
        }
