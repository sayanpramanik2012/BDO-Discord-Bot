"""Enhanced configuration for dual-source BDO bot"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

class Config:
    """Enhanced configuration class"""
    
    # Discord Configuration
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    
    # AI Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = 'gemini-2.0-flash'
    
    # BDO URLs - Updated with your requested URLs
    KOREAN_NOTICE_URL = "https://www.kr.playblackdesert.com/ko-KR/News/Notice?boardType=2"
    GLOBAL_LAB_URL = "https://blackdesert.pearlabyss.com/GlobalLab/en-US/News/Notice?_categoryNo=2"
    
    # Bot Settings
    CHECK_INTERVAL_MINUTES = 15  # More frequent for dual monitoring
    COMMAND_PREFIX = '!'
    
    # Language Support
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'ko': '한국어 (Korean)',
        'es': 'Español (Spanish)',
        'fr': 'Français (French)',
        'de': 'Deutsch (German)',
        'ja': '日本語 (Japanese)'
    }
    
    # Content Limits
    MAX_TRANSLATION_LENGTH = 4000
    MAX_SUMMARY_LENGTH = 3000
    MAX_DISCORD_FIELD_LENGTH = 1024
    MAX_DISCORD_MESSAGE_LENGTH = 2000
    
    @classmethod
    def validate_config(cls):
        """Validate configuration"""
        errors = []
        if not cls.DISCORD_TOKEN:
            errors.append("DISCORD_TOKEN not found in .env file")
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY not found in .env file")
        if errors:
            raise ValueError("\n".join(errors))
    
    @classmethod
    def initialize_gemini(cls):
        """Initialize Gemini AI"""
        genai.configure(api_key=cls.GEMINI_API_KEY)
        return genai.GenerativeModel(cls.GEMINI_MODEL)

Config.validate_config()
