"""AI translation and summarization using Gemini"""
import logging
from typing import Optional, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class BDOTranslator:
    """Handles AI translation and summarization of patch notes"""
    
    def __init__(self):
        self.model = Config.initialize_gemini()
    
    async def translate_and_summarize(self, korean_patch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Translate Korean patch notes and create summary using Gemini"""
        try:
            # Step 1: Translate Korean to English
            translated_content = await self._translate_content(korean_patch)
            if not translated_content:
                return None
            
            # Step 2: Create AI summary
            ai_summary = await self._create_summary(translated_content)
            if not ai_summary:
                return None
            
            return {
                'original': korean_patch,
                'translated': translated_content,
                'summary': ai_summary
            }
            
        except Exception as e:
            logger.error(f"Translation/Summary error: {e}")
            return None
    
    async def translate_and_summarize_with_language(self, patch: Dict[str, Any], target_language: str) -> Optional[Dict[str, Any]]:
        """Enhanced translation and summarization for manual commands"""
        try:
            # If already in target language, just add summary
            if (patch.get('language') == 'english' and target_language == 'en') or \
            (patch.get('language') == 'korean' and target_language == 'ko'):
                
                # Generate summary for existing content
                summary = await self._create_summary_in_language(patch['content'], target_language)
                
                enhanced_patch = patch.copy()
                enhanced_patch['summary'] = summary
                return enhanced_patch
            
            # Need translation
            translated_content = await self._translate_to_language(patch, target_language)
            if not translated_content:
                return None
            
            # Create summary in target language
            summary = await self._create_summary_in_language(translated_content, target_language)
            
            return {
                'original': patch,
                'translated': translated_content,
                'summary': summary,
                'title': patch['title'],
                'date': patch['date'],
                'content': translated_content,
                'link': patch.get('link'),
                'source': patch['source'],
                'language': target_language
            }
            
        except Exception as e:
            logger.error(f"Enhanced translation error: {e}")
            return None

    async def _translate_content(self, korean_patch: Dict[str, Any]) -> Optional[str]:
        """Translate Korean content to English"""
        try:
            content_to_translate = korean_patch['content'][:Config.MAX_TRANSLATION_LENGTH]
            
            translation_prompt = f"""
            You are a professional translator specializing in Korean to English translation for video game content.
            
            Translate the following Korean Black Desert Online patch notes to English:
            - Maintain original formatting and structure
            - Keep technical terms and game-specific terminology accurate
            - Preserve any numerical values, percentages, and statistics
            - Maintain bullet points and lists if present
            
            Title: {korean_patch['title']}
            Content: {content_to_translate}
            
            Provide only the translation without additional commentary.
            """
            
            response = self.model.generate_content(translation_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return None
    
    async def _translate_to_language(self, patch: Dict[str, Any], target_language: str) -> Optional[str]:
        """Translate patch content to specific target language"""
        try:
            content = patch['content'][:Config.MAX_TRANSLATION_LENGTH]
            language_names = {
                'en': 'English',
                'ko': 'Korean',
                'es': 'Spanish', 
                'fr': 'French',
                'de': 'German',
                'ja': 'Japanese'
            }
            
            target_lang_name = language_names.get(target_language, 'English')
            
            translation_prompt = f"""
            You are a professional translator specializing in video game content translation.
            
            Translate the following Black Desert Online patch notes to {target_lang_name}:
            - Maintain original formatting and structure
            - Keep technical terms and game-specific terminology accurate
            - Preserve any numerical values, percentages, and statistics
            
            Title: {patch['title']}
            Content: {content}
            
            Provide only the translation without additional commentary.
            """
            
            response = self.model.generate_content(translation_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Language translation error: {e}")
            return None
    
    async def _create_summary(self, translated_content: str) -> Optional[str]:
        """Create AI summary of translated patch notes"""
        try:
            content_to_summarize = translated_content[:Config.MAX_SUMMARY_LENGTH]
            
            summary_prompt = f"""
            Create a concise and informative summary of these Black Desert Online patch notes.
            Focus on the most important changes that affect players.
            
            Format your response as follows:
            **🔥 Key Changes:**
            • [Most important changes as bullet points]
            
            **⚔️ Class Updates:**
            • [Class-specific changes, or "None" if no class updates]
            
            **🆕 New Content:**
            • [New features, content, or systems, or "None" if no new content]
            
            **🔧 Bug Fixes:**
            • [Major bug fixes only, or "None" if no significant fixes]
            
            Content to summarize:
            {content_to_summarize}
            
            Keep the summary under 800 characters total.
            """
            
            response = self.model.generate_content(summary_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Summary error: {e}")
            return None
    
    async def _create_summary_in_language(self, content: str, language: str) -> Optional[str]:
        """Enhanced summary creation with maintenance detection"""
        try:
            # Check if this is a maintenance notice
            is_maintenance = any(keyword in content.lower() 
                            for keyword in ['maintenance', 'scheduled', 'server', 'unavailable'])
            
            if is_maintenance:
                # Special prompt for maintenance notices
                summary_prompt = f"""
                Create a brief summary of this Black Desert maintenance notice.
                Focus on key information players need to know.
                
                Format:
                **🔧 Maintenance Details:**
                • [Key points about the maintenance]
                
                **⏰ Timing:**
                • [When and how long]
                
                **📋 Impact:**
                • [What services affected]
                
                Content: {content[:1000]}
                """
            else:
                # Regular patch content prompt
                summary_prompt = f"""
                Create a structured summary of these Black Desert patch notes:
                
                **🔥 Key Changes:**
                • [Most important updates]
                
                **⚔️ Class Updates:**
                • [Class changes or "None"]
                
                **🆕 New Content:**
                • [New features or "None"]
                
                **🔧 Bug Fixes:**
                • [Major fixes or "None"]
                
                Content: {content[:2000]}
                """
            
            response = self.model.generate_content(summary_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return None

    async def translate_simple_text(self, korean_text: str) -> Optional[str]:
        """Simple translation for shorter texts"""
        try:
            prompt = f"""
            Translate this Korean text to English, maintaining any formatting:
            {korean_text[:1000]}
            
            Provide only the translation.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Simple translation error: {e}")
            return None
