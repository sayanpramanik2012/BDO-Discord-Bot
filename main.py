"""Enhanced BDO Patch Bot with AI Analysis System - Fixed Unicode Logging"""
import discord
from discord.ext import commands, tasks
import logging
import asyncio
import sys
import os

# Set UTF-8 encoding before any other imports
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Local imports
from config import Config
from link_extractor import BDOLinkExtractor
from ai_analyzer import BDOAIAnalyzer
from database import BotDatabase
from discord_handler import DiscordHandler
from utils.helpers import setup_logging, safe_log_message

# Setup logging with UTF-8 support
setup_logging()
logger = logging.getLogger(__name__)

class EnhancedBDOPatchBot(commands.Bot):
    """Enhanced bot with AI analysis workflow"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=Config.COMMAND_PREFIX, intents=intents, help_command=None)
        
        # Initialize components
        self.link_extractor = BDOLinkExtractor()
        self.ai_analyzer = BDOAIAnalyzer(Config.GEMINI_API_KEY)
        self.discord_handler = DiscordHandler(self)
        self.db = BotDatabase()
    
    async def setup_hook(self):
        """Setup hook for loading extensions"""
        try:
            # Load command modules
            await self.load_extension('commands.patch_commands')
            await self.load_extension('commands.config_commands')
            logger.info("All extensions loaded successfully")
            
            # Print loaded commands for debugging
            command_names = [cmd.name for cmd in self.commands]
            logger.info(f"Loaded commands: {command_names}")
            
        except Exception as e:
            logger.error(f"Failed to load extensions: {e}")
            # Manual fallback loading
            try:
                from commands.patch_commands import PatchCommands
                from commands.config_commands import ConfigCommands
                await self.add_cog(PatchCommands(self))
                await self.add_cog(ConfigCommands(self))
                logger.info("Manually loaded cogs as fallback")
            except Exception as fallback_error:
                logger.error(f"Fallback cog loading failed: {fallback_error}")
    
    async def on_ready(self):
        """Bot ready event"""
        logger.info(f'{self.user} has logged in!')
        logger.info(f'Bot is monitoring {len(self.guilds)} servers')
        
        # Print available commands for debugging
        command_names = [cmd.name for cmd in self.commands]
        logger.info(f"Available commands: {command_names}")
        
        # Start AI analysis monitoring
        if not self.ai_analysis_loop.is_running():
            self.ai_analysis_loop.start()
            logger.info("Started AI analysis monitoring loop")
        
        # Start notification loop
        if not self.notification_loop.is_running():
            self.notification_loop.start()
            logger.info("Started notification loop")
    
    @tasks.loop(minutes=Config.CHECK_INTERVAL_MINUTES)
    async def ai_analysis_loop(self):
        """Main AI analysis loop - generates reports for new patches"""
        try:
            logger.info("Running AI analysis cycle...")
            
            # Extract Global Labs links
            gl_patches = await self.link_extractor.extract_global_lab_links(
                Config.GLOBAL_LAB_URL, 5
            )
            
            # Process Global Labs patches
            for patch in gl_patches:
                if self.db.is_report_new('Global Labs', patch['id']):
                    # Safe logging for Korean titles
                    safe_title = safe_log_message(patch['title'][:50])
                    logger.info(f"Generating new AI report for Global Labs: {safe_title}...")
                    
                    report_filename = await self.ai_analyzer.generate_deep_report(patch)
                    if report_filename:
                        self.db.store_ai_report(patch, report_filename, 'Global Labs')
                        logger.info(f"New Global Labs AI report generated: {report_filename}")
            
            # Extract Korean links
            kr_patches = await self.link_extractor.extract_korean_links(
                Config.KOREAN_NOTICE_URL, 5
            )
            
            # Process Korean patches
            for patch in kr_patches:
                if self.db.is_report_new('Korean Notice', patch['id']):
                    # Safe logging for Korean titles
                    safe_title = safe_log_message(patch['title'][:50])
                    logger.info(f"Generating new AI report for Korean: {safe_title}...")
                    
                    report_filename = await self.ai_analyzer.generate_deep_report(patch)
                    if report_filename:
                        self.db.store_ai_report(patch, report_filename, 'Korean Notice')
                        logger.info(f"New Korean AI report generated: {report_filename}")
            
        except Exception as e:
            logger.error(f"Error in AI analysis loop: {e}")
    
    @tasks.loop(minutes=2)
    async def notification_loop(self):
        """Send notifications for new AI reports"""
        try:
            # Get unnotified reports
            unnotified_reports = self.db.get_unnotified_reports()
            
            if unnotified_reports:
                # Get configured servers
                configured_servers = self.db.get_all_configured_servers()
                
                for report in unnotified_reports:
                    for server_config in configured_servers:
                        try:
                            channel = self.get_channel(server_config['channel_id'])
                            if channel:
                                await self.discord_handler.notify_new_ai_report(
                                    channel, report
                                )
                        except Exception as e:
                            logger.error(f"Error notifying server: {e}")
                    
                    # Mark as notified
                    self.db.mark_report_notified(report['source'], report['patch_id'])
                    
        except Exception as e:
            logger.error(f"Error in notification loop: {e}")
    
    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            logger.warning(f"Command not found: {ctx.message.content}")
            await ctx.send(f"❌ Command not found. Use `!help` to see available commands.")
        else:
            logger.error(f"Command error: {error}")
            await ctx.send(f"❌ An error occurred: {error}")

def main():
    """Main entry point"""
    logger.info("Starting Enhanced BDO Bot with AI Analysis System...")
    
    try:
        bot = EnhancedBDOPatchBot()
        bot.run(Config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
