"""Configuration commands for channel and language setup"""
import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class ConfigCommands(commands.Cog):
    """Commands for bot configuration"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
    
    @commands.command(name='usepatch')
    async def set_patch_channel(self, ctx):
        """Set the current channel for patch notifications"""
        try:
            # Check if user has manage channels permission OR is admin
            if not (ctx.author.guild_permissions.manage_channels or ctx.author.guild_permissions.administrator):
                await ctx.send("❌ You need 'Manage Channels' or 'Administrator' permission to use this command.")
                return
            
            success = self.db.set_patch_channel(ctx.guild.id, ctx.channel.id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Patch Channel Set",
                    description=f"This channel ({ctx.channel.mention}) will now receive BDO patch notifications from both Korean Notice and Global Labs.",
                    color=0x00ff00
                )
                
                embed.add_field(
                    name="Next Steps",
                    value="• Use `!bdolan en` to set language\n• Use `!config` to view settings\n• Bot will automatically check for patches every 15 minutes",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                logger.info(f"Patch channel set for guild {ctx.guild.id} to channel {ctx.channel.id}")
            else:
                await ctx.send("❌ Failed to set patch channel. Please try again.")
                
        except Exception as e:
            logger.error(f"Error in usepatch command: {e}")
            await ctx.send("❌ An error occurred. Please try again.")
    
    @commands.command(name='bdolan')
    async def set_language(self, ctx, language_code: str = 'en'):
        """Set translation language"""
        try:
            from config import Config
            
            if language_code not in Config.SUPPORTED_LANGUAGES:
                embed = discord.Embed(
                    title="❌ Invalid Language",
                    description="Supported languages:",
                    color=0xff0000
                )
                
                for code, name in Config.SUPPORTED_LANGUAGES.items():
                    embed.add_field(
                        name=f"`!bdolan {code}`",
                        value=name,
                        inline=True
                    )
                
                await ctx.send(embed=embed)
                return
            
            success = self.db.set_language(ctx.guild.id, language_code)
            
            if success:
                language_name = Config.SUPPORTED_LANGUAGES[language_code]
                embed = discord.Embed(
                    title="🌐 Language Updated",
                    description=f"Translation language set to: **{language_name}**",
                    color=0x00ff00
                )
                
                embed.add_field(
                    name="Note",
                    value="This affects all patch translations in this server.",
                    inline=False
                )
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Failed to set language. Please try again.")
                
        except Exception as e:
            logger.error(f"Error in bdolan command: {e}")
            await ctx.send("❌ An error occurred. Please try again.")
    
    @commands.command(name='config')
    async def show_config(self, ctx):
        """Show current server configuration"""
        try:
            config = self.db.get_server_config(ctx.guild.id)
            
            embed = discord.Embed(
                title="⚙️ Server Configuration",
                color=0x0099ff
            )
            
            if config and config['channel_id']:
                channel = ctx.guild.get_channel(config['channel_id'])
                channel_name = channel.mention if channel else "Channel not found"
                
                from config import Config
                language_name = Config.SUPPORTED_LANGUAGES.get(config['language'], 'English')
                
                embed.add_field(
                    name="📢 Patch Channel",
                    value=channel_name,
                    inline=True
                )
                
                embed.add_field(
                    name="🌐 Language",
                    value=language_name,
                    inline=True
                )
                
                embed.add_field(
                    name="🔄 Status",
                    value="✅ Active",
                    inline=True
                )
                
            else:
                embed.description = "❌ No configuration found.\n\nUse `!usepatch` to set up patch notifications."
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in config command: {e}")
            await ctx.send("❌ An error occurred. Please try again.")

# CRITICAL: This setup function was missing!
async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(ConfigCommands(bot))
