"""Enhanced Discord message posting with new notification pattern"""
import discord
import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging
from config import Config

logger = logging.getLogger(__name__)

class DiscordHandler:
    """Enhanced Discord posting with new notification pattern"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Source-specific configurations
        self.source_configs = {
            "Korean Notice": {
                "color": 0xFF6B6B,  # Red
                "icon": "🇰🇷",
                "flag": "KR",
                "title_prefix": "New BDO Korean Patch Notes"
            },
            "Global Labs": {
                "color": 0x00FF00,  # Green
                "icon": "🌍",
                "flag": "GL", 
                "title_prefix": "New BDO Global Labs Update"
            }
        }
    
    async def post_enhanced_patch(self, channel: discord.TextChannel, patch_data: Dict[str, Any], source: str) -> bool:
        """Post patch with new notification pattern"""
        try:
            # Get source configuration
            source_config = self.source_configs.get(source, {
                "color": 0x0099FF,
                "icon": "📰",
                "flag": "??",
                "title_prefix": "New BDO Update"
            })
            
            # Generate AI heading if available, otherwise use original title
            if patch_data.get('summary'):
                # Extract key points for heading
                ai_heading = await self._generate_ai_heading(patch_data)
            else:
                ai_heading = patch_data.get('title', 'Patch Update')[:100]
            
            # Create the new notification pattern
            embed = await self._create_new_pattern_embed(patch_data, source, source_config, ai_heading)
            
            # Send the notification
            message = await channel.send(embed=embed)
            
            # Add reactions
            try:
                await message.add_reaction("🔥")
                await message.add_reaction("👀")
            except:
                pass
            
            logger.info(f"Successfully posted {source} patch with new pattern to channel {channel.id}")
            return True
            
        except discord.Forbidden:
            logger.error(f"No permission to post in channel {channel.id}")
            return False
        except discord.HTTPException as e:
            logger.error(f"Discord API error posting to channel {channel.id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error posting {source} patch: {e}")
            return False
    
    async def _generate_ai_heading(self, patch_data: Dict[str, Any]) -> str:
        """Generate AI heading from summary"""
        try:
            summary = patch_data.get('summary', '')
            
            # Extract key changes from AI summary
            if '• ' in summary:
                lines = summary.split('\n')
                key_changes = []
                
                for line in lines:
                    if '• ' in line and 'None' not in line:
                        # Clean up the bullet point
                        change = line.split('• ')[1].strip() if '• ' in line else line.strip()
                        if change and len(change) > 5:
                            key_changes.append(change)
                
                if key_changes:
                    # Take first 2-3 key changes for heading
                    heading_parts = key_changes[:2]
                    return ' & '.join(heading_parts)[:80]
            
            # Fallback to original title
            return patch_data.get('title', 'Patch Update')[:80]
            
        except Exception as e:
            logger.error(f"Error generating AI heading: {e}")
            return patch_data.get('title', 'Patch Update')[:80]
    
    async def _create_new_pattern_embed(self, patch_data: Dict[str, Any], source: str, source_config: Dict[str, Any], ai_heading: str) -> discord.Embed:
        """Create embed with enhanced content handling"""
        
        # Main title
        title = source_config['title_prefix']
        
        # Check if this is a maintenance notice vs actual patch content
        is_maintenance = any(keyword in patch_data.get('title', '').lower() 
                            for keyword in ['maintenance', 'scheduled', 'server'])
        
        # Format description
        if is_maintenance:
            description = f"**{ai_heading}**\n\n⚠️ *This is a maintenance notice*"
        else:
            description = f"**{ai_heading}**"
        
        # Create embed
        embed = discord.Embed(
            title=title,
            description=description,
            color=source_config['color'],
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add effect date
        effect_date = self._format_effect_date(patch_data.get('date', 'Unknown'))
        embed.add_field(
            name="📅 Effect on Date",
            value=effect_date,
            inline=False
        )
        
        # Add original link
        patch_link = patch_data.get('link')
        if patch_link and patch_link.startswith('http'):
            embed.add_field(
                name="🔗 Original Link",
                value=f"[View Official Notice]({patch_link})",
                inline=False
            )
        
        # Add separator
        embed.add_field(
            name="━━━━━━━━━━━━━━━━━━━━━━━━━━",
            value="** **",
            inline=False
        )
        
        # Enhanced AI Summary handling
        if patch_data.get('summary'):
            formatted_summary = self._format_ai_summary(patch_data['summary'])
            embed.add_field(
                name="🤖 AI Summary",
                value=formatted_summary,
                inline=False
            )
        elif is_maintenance:
            # Special handling for maintenance notices
            embed.add_field(
                name="🔧 Maintenance Information",
                value="**📋 Details:**\n• Server maintenance scheduled\n• Services temporarily unavailable\n• Check official notice for exact times\n\n**🕐 Duration:**\n• Refer to official notice for maintenance window",
                inline=False
            )
        else:
            # Content patch without summary - attempt to generate one
            embed.add_field(
                name="🤖 AI Summary",
                value="**📋 Summary:**\n• AI summary generation in progress\n• Check original link for full details\n\n**⚠️ Note:**\n• Summary may be updated once processing completes",
                inline=False
            )
        
        # Footer
        embed.set_footer(
            text=f"Source: {source} • BDO Patch Bot",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        
        return embed

    def _format_effect_date(self, original_date: str) -> str:
        """Format date to match the requested pattern"""
        try:
            # Try to parse various date formats and convert to desired format
            if 'UTC' in original_date:
                return original_date
            
            # For Korean dates, try to convert format
            if any(char in original_date for char in ['년', '월', '일']):
                # Keep original Korean format but add UTC note
                return f"{original_date} (Check timezone in original notice)"
            
            # For other formats, try to standardize
            if '.' in original_date and len(original_date) > 8:
                # Assuming YYYY.MM.DD format
                parts = original_date.split('.')
                if len(parts) >= 3:
                    try:
                        year, month, day = parts[0], parts[1], parts[2][:2]
                        # Convert to readable format
                        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        month_name = months[int(month) - 1] if int(month) <= 12 else month
                        return f"{month_name} {int(day)}, {year} (UTC)"
                    except:
                        pass
            
            # Fallback - add UTC notation
            return f"{original_date} (UTC)"
            
        except Exception as e:
            logger.error(f"Error formatting date: {e}")
            return f"{original_date} (UTC)"
    
    def _format_ai_summary(self, summary: str) -> str:
        """Format AI summary to match your requested pattern"""
        try:
            # If summary is already well-formatted, use as-is
            if '**' in summary and '•' in summary:
                return summary[:Config.MAX_DISCORD_FIELD_LENGTH]
            
            # Generate structured summary if not available
            formatted_summary = f"""**🔥 Key Changes:**
    • {summary[:200]}...

    **⚔️ Class Updates:**
    • None detected in preview

    **🆕 New Content:**
    • Check full content for details

    **🔧 Bug Fixes:**
    • Check full content for details"""

            return formatted_summary[:Config.MAX_DISCORD_FIELD_LENGTH]
            
        except Exception as e:
            logger.error(f"Error formatting AI summary: {e}")
            return summary[:Config.MAX_DISCORD_FIELD_LENGTH] if summary else "Summary not available"

    
    # Legacy and utility methods
    
    async def post_patch_to_discord(self, patch_data: Dict[str, Any]) -> bool:
        """Legacy method for backward compatibility"""
        try:
            # Try to determine source from patch data
            source = patch_data.get('source', 'Korean Notice')
            
            # Get configured servers and post to all
            from database import BotDatabase
            db = BotDatabase()
            configured_servers = db.get_all_configured_servers()
            
            success_count = 0
            for server_config in configured_servers:
                channel = self.bot.get_channel(server_config['channel_id'])
                if channel:
                    if await self.post_enhanced_patch(channel, patch_data, source):
                        success_count += 1
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error in legacy post method: {e}")
            return False
    
    def create_info_embed(self, title: str, description: str, color: int = 0x00ff00) -> discord.Embed:
        """Create a simple info embed"""
        embed = discord.Embed(
            title=title,
            description=description[:2048],
            color=color,
            timestamp=datetime.now()
        )
        embed.set_footer(text="BDO Patch Bot", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        return embed
    
    def create_debug_embed(self, debug_info: Dict[str, Any]) -> discord.Embed:
        """Create debug information embed"""
        embed = discord.Embed(
            title="🔧 Debug Information",
            color=0xFFAA00,
            timestamp=datetime.now()
        )
        
        # Add debug fields
        for key, value in debug_info.items():
            if key != 'error':
                field_name = key.replace('_', ' ').title()
                field_value = str(value)[:Config.MAX_DISCORD_FIELD_LENGTH]
                embed.add_field(
                    name=field_name,
                    value=field_value,
                    inline=True
                )
        
        # Handle errors specially
        if 'error' in debug_info:
            error_text = str(debug_info['error'])[:Config.MAX_DISCORD_FIELD_LENGTH]
            embed.add_field(
                name="❌ Error",
                value=f"``````",
                inline=False
            )
        
        embed.set_footer(text="Debug Mode • BDO Patch Bot")
        return embed
    
    def create_error_embed(self, error_title: str, error_message: str) -> discord.Embed:
        """Create an error embed"""
        embed = discord.Embed(
            title=f"❌ {error_title}",
            description=error_message[:2048],
            color=0xFF0000,
            timestamp=datetime.now()
        )
        embed.set_footer(text="BDO Patch Bot")
        return embed
    
    def create_success_embed(self, success_title: str, success_message: str) -> discord.Embed:
        """Create a success embed"""
        embed = discord.Embed(
            title=f"✅ {success_title}",
            description=success_message[:2048],
            color=0x00FF00,
            timestamp=datetime.now()
        )
        embed.set_footer(text="BDO Patch Bot")
        return embed
    
    async def send_to_channel(self, channel_id: int, embed: discord.Embed = None, content: str = None) -> bool:
        """Utility method to send content to a specific channel"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.error(f"Channel {channel_id} not found")
                return False
            
            if embed and content:
                await channel.send(content=content, embed=embed)
            elif embed:
                await channel.send(embed=embed)
            elif content:
                await channel.send(content=content)
            else:
                logger.error("No content or embed provided to send")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending to channel {channel_id}: {e}")
            return False

    async def _create_content_file(self, content: str, source: str, content_type: str) -> str:
        """Create a temporary file for long content"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_source = source.lower().replace(" ", "_").replace("-", "_")
        filename = f"bdo_{safe_source}_{content_type}_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"BDO {source} - {content_type.title()}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                f.write(content)
                
            return filename
            
        except Exception as e:
            logger.error(f"Error creating content file: {e}")
            raise
    
    async def _cleanup_file(self, filename: str):
        """Safely clean up temporary files"""
        try:
            await asyncio.sleep(1)
            if os.path.exists(filename):
                os.remove(filename)
                logger.debug(f"Cleaned up file: {filename}")
        except Exception as e:
            logger.warning(f"Could not clean up file {filename}: {e}")
    
    def create_info_embed(self, title: str, description: str, color: int = 0x00ff00) -> discord.Embed:
        """Create a simple info embed"""
        embed = discord.Embed(
            title=title,
            description=description[:2048],
            color=color,
            timestamp=datetime.now()
        )
        embed.set_footer(text="BDO Patch Bot", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        return embed
    
    def create_debug_embed(self, debug_info: Dict[str, Any]) -> discord.Embed:
        """Create debug information embed"""
        embed = discord.Embed(
            title="🔧 Debug Information",
            color=0xFFAA00,
            timestamp=datetime.now()
        )
        
        for key, value in debug_info.items():
            if key != 'error':
                field_name = key.replace('_', ' ').title()
                field_value = str(value)[:Config.MAX_DISCORD_FIELD_LENGTH]
                embed.add_field(
                    name=field_name,
                    value=field_value,
                    inline=True
                )
        
        if 'error' in debug_info:
            error_text = str(debug_info['error'])[:Config.MAX_DISCORD_FIELD_LENGTH]
            embed.add_field(
                name="❌ Error",
                value=f"``````",
                inline=False
            )
        
        embed.set_footer(text="Debug Mode • BDO Patch Bot")
        return embed
    
    async def notify_new_ai_report(self, channel: discord.TextChannel, report_data: Dict[str, Any]) -> bool:
        """Notify about new AI report"""
        try:
            source = report_data['source']
            report_filename = report_data['report_filename']
            title = report_data['title']
            
            embed = discord.Embed(
                title=f"🆕 New {source} Analysis Available",
                description=f"**{title[:100]}...**",
                color=0x00ff88 if 'Global' in source else 0xff6b35,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="📊 AI Report Generated",
                value=f"Comprehensive analysis now available\nUse `!latest {source.split()[0].lower()}` to download",
                inline=False
            )
            
            embed.set_footer(text=f"Intelligence Report: {report_filename}")
            
            message = await channel.send(embed=embed)
            
            # Add reaction
            await message.add_reaction("📊")
            
            return True
            
        except Exception as e:
            logger.error(f"Error notifying about AI report: {e}")
            return False
