"""Enhanced patch commands with history access"""
import discord
from discord.ext import commands
import logging
import os
import math

logger = logging.getLogger(__name__)

class PatchCommands(commands.Cog):
    """Enhanced patch commands with history access"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.ai_analyzer = bot.ai_analyzer
    
    @commands.command(name='latest')
    async def latest_command(self, ctx, source: str = 'both'):
        """Send latest AI analysis reports"""
        
        if source.lower() in ['gl', 'globallab', 'global']:
            await self._send_latest_report(ctx, 'Global Labs')
        elif source.lower() in ['ko', 'korean', 'kr']:
            await self._send_latest_report(ctx, 'Korean Notice')
        else:
            # Send both
            await ctx.send("📊 **Fetching latest AI analysis reports...**")
            await self._send_latest_report(ctx, 'Global Labs')
            await self._send_latest_report(ctx, 'Korean Notice')
    
    @commands.command(name='history')
    async def history_command(self, ctx, source: str = None, index: int = None):
        """Access historical reports - Usage: !history gl 3 OR !history ko 1"""
        
        if not source:
            await self._show_history_help(ctx)
            return
        
        # Determine source
        if source.lower() in ['gl', 'globallab', 'global']:
            source_name = 'Global Labs'
        elif source.lower() in ['ko', 'korean', 'kr']:
            source_name = 'Korean Notice'
        else:
            await ctx.send("❌ Invalid source. Use `gl` for Global Labs or `ko` for Korean notices.")
            return
        
        # If no index provided, show available reports list
        if index is None:
            await self._show_available_reports(ctx, source_name)
            return
        
        # Validate index
        if index < 1:
            await ctx.send("❌ Index must be 1 or higher (1=latest, 2=second latest, etc.)")
            return
        
        # Get and send specific report
        await self._send_report_by_index(ctx, source_name, index)
    
    @commands.command(name='archive')
    async def archive_command(self, ctx, source: str = None):
        """Show paginated archive of all reports"""
        
        if not source:
            await ctx.send("📚 **Archive Help**\n`!archive gl` - Global Labs archive\n`!archive ko` - Korean archive")
            return
        
        # Determine source
        if source.lower() in ['gl', 'globallab', 'global']:
            source_name = 'Global Labs'
        elif source.lower() in ['ko', 'korean', 'kr']:
            source_name = 'Korean Notice'
        else:
            await ctx.send("❌ Invalid source. Use `gl` or `ko`.")
            return
        
        await self._show_paginated_archive(ctx, source_name)
    
    async def _send_latest_report(self, ctx, source: str):
        """Send the latest AI report file for a source - ENHANCED"""
        try:
            # Get latest report from database
            report_info = self.db.get_latest_report(source)
            
            if not report_info:
                await ctx.send(f"❌ No AI analysis reports found for {source}")
                return
            
            # Get report file path
            report_filename = report_info['report_filename']
            report_path = os.path.join(self.ai_analyzer.reports_folder, report_filename)
            
            if not os.path.exists(report_path):
                await ctx.send(f"❌ Report file not found: {report_filename}")
                return
            
            # Check total reports count
            total_reports = self.db.count_reports(source)
            
            # Create embed
            embed = discord.Embed(
                title=f"📊 {source} - Latest AI Analysis Report",
                description=f"**{report_info['title'][:100]}...**",
                color=0x00ff88 if 'Global' in source else 0xff6b35,
                timestamp=ctx.message.created_at
            )
            
            embed.add_field(
                name="📋 Report Details",
                value=(
                    f"**Date:** {report_info['date']}\n"
                    f"**Generated:** {report_info['generated_at'][:16]}\n"
                    f"**Position:** #1 of {total_reports} total reports"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🎯 Contains",
                value=(
                    "• Executive Summary & Strategic Analysis\n"
                    "• Detailed Content & Balance Changes\n"
                    "• Competitive Intelligence & Meta Impact\n"
                    "• Player Action Items & Recommendations"
                ),
                inline=False
            )
            
            # Get file size
            file_size = os.path.getsize(report_path)
            embed.add_field(
                name="📄 File Info",
                value=f"**Size:** {file_size:,} bytes\n**Format:** Plain Text (.txt)",
                inline=True
            )
            
            if total_reports > 1:
                source_short = 'gl' if 'Global' in source else 'ko'
                embed.add_field(
                    name="📚 Access History",
                    value=f"Use `!history {source_short}` to see all {total_reports} reports\nOr `!history {source_short} 2` for 2nd latest",
                    inline=True
                )
            
            embed.set_footer(text="AI-Generated Intelligence Report • BDO Patch Bot")
            
            # Send file with embed
            with open(report_path, 'rb') as f:
                discord_file = discord.File(f, filename=report_filename)
                message = await ctx.send(embed=embed, file=discord_file)
            
            # Add reactions
            await message.add_reaction("📊")
            await message.add_reaction("⭐")
            if total_reports > 1:
                await message.add_reaction("📚")  # Archive indicator
            
            logger.info(f"Sent latest AI report for {source} to {ctx.guild.name}")
            
        except Exception as e:
            logger.error(f"Error sending latest report for {source}: {e}")
            await ctx.send(f"❌ Error retrieving {source} analysis report")
    
    async def _send_report_by_index(self, ctx, source: str, index: int):
        """Send a specific report by its index"""
        try:
            # Get total count first
            total_reports = self.db.count_reports(source)
            
            if index > total_reports:
                await ctx.send(f"❌ Only {total_reports} reports available for {source}. Use index 1-{total_reports}")
                return
            
            # Get specific report
            report_info = self.db.get_report_by_index(source, index)
            
            if not report_info:
                await ctx.send(f"❌ Report #{index} not found for {source}")
                return
            
            # Get report file path
            report_filename = report_info['report_filename']
            report_path = os.path.join(self.ai_analyzer.reports_folder, report_filename)
            
            if not os.path.exists(report_path):
                await ctx.send(f"❌ Report file not found: {report_filename}")
                return
            
            # Create embed
            position_text = "Latest" if index == 1 else f"#{index} of {total_reports}"
            
            embed = discord.Embed(
                title=f"📊 {source} - Historical Report ({position_text})",
                description=f"**{report_info['title'][:100]}...**",
                color=0x00ff88 if 'Global' in source else 0xff6b35,
                timestamp=ctx.message.created_at
            )
            
            embed.add_field(
                name="📋 Report Details",
                value=(
                    f"**Date:** {report_info['date']}\n"
                    f"**Generated:** {report_info['generated_at'][:16]}\n"
                    f"**Position:** {position_text}"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🎯 Contains",
                value=(
                    "• Executive Summary & Strategic Analysis\n"
                    "• Detailed Content & Balance Changes\n"
                    "• Competitive Intelligence & Meta Impact\n"
                    "• Player Action Items & Recommendations"
                ),
                inline=False
            )
            
            # Get file size
            file_size = os.path.getsize(report_path)
            embed.add_field(
                name="📄 File Info",
                value=f"**Size:** {file_size:,} bytes\n**Format:** Plain Text (.txt)",
                inline=True
            )
            
            source_short = 'gl' if 'Global' in source else 'ko'
            embed.add_field(
                name="🔄 Navigation",
                value=f"`!history {source_short}` - Show all reports\n`!latest {source_short}` - Get latest report",
                inline=True
            )
            
            embed.set_footer(text=f"Historical Report #{index} • BDO Patch Bot")
            
            # Send file with embed
            with open(report_path, 'rb') as f:
                discord_file = discord.File(f, filename=report_filename)
                message = await ctx.send(embed=embed, file=discord_file)
            
            # Add reactions
            await message.add_reaction("📊")
            await message.add_reaction("📚")
            
            logger.info(f"Sent historical report #{index} for {source} to {ctx.guild.name}")
            
        except Exception as e:
            logger.error(f"Error sending report #{index} for {source}: {e}")
            await ctx.send(f"❌ Error retrieving historical report")
    
    async def _show_available_reports(self, ctx, source: str):
        """Show list of available reports for a source"""
        try:
            reports = self.db.get_all_reports(source, 10)  # Get last 10
            total_count = self.db.count_reports(source)
            
            if not reports:
                await ctx.send(f"❌ No reports found for {source}")
                return
            
            embed = discord.Embed(
                title=f"📚 {source} - Available Reports ({total_count} total)",
                color=0x00ff88 if 'Global' in source else 0xff6b35
            )
            
            # Add recent reports
            report_list = []
            for i, report in enumerate(reports[:10], 1):
                date_short = report['generated_at'][:10]  # YYYY-MM-DD
                title_short = report['title'][:60] + "..." if len(report['title']) > 60 else report['title']
                report_list.append(f"`#{i}` **{date_short}** - {title_short}")
            
            embed.add_field(
                name=f"📋 Recent Reports (Showing {len(reports)} of {total_count})",
                value="\n".join(report_list),
                inline=False
            )
            
            source_short = 'gl' if 'Global' in source else 'ko'
            embed.add_field(
                name="📖 Usage Examples",
                value=(
                    f"`!history {source_short} 1` - Get latest report\n"
                    f"`!history {source_short} 3` - Get 3rd latest report\n"
                    f"`!latest {source_short}` - Get latest with file\n"
                    f"`!archive {source_short}` - Browse all reports"
                ),
                inline=False
            )
            
            if total_count > 10:
                embed.add_field(
                    name="ℹ️ Note",
                    value=f"Showing latest 10 reports. Use `!archive {source_short}` to browse all {total_count} reports.",
                    inline=False
                )
            
            embed.set_footer(text="BDO Intelligence Archive • Historical Reports")
            
            message = await ctx.send(embed=embed)
            await message.add_reaction("📚")
            
        except Exception as e:
            logger.error(f"Error showing available reports for {source}: {e}")
            await ctx.send("❌ Error retrieving reports list")
    
    async def _show_history_help(self, ctx):
        """Show help for history command"""
        embed = discord.Embed(
            title="📚 History Command Help",
            description="Access historical AI analysis reports",
            color=0x0099ff
        )
        
        embed.add_field(
            name="📖 Usage Examples",
            value=(
                "`!history gl` - List Global Labs reports\n"
                "`!history ko` - List Korean reports\n"
                "`!history gl 3` - Get 3rd latest Global Labs report\n"
                "`!history ko 1` - Get latest Korean report"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔢 Index System",
            value=(
                "• Index 1 = Latest report\n"
                "• Index 2 = Second latest\n"
                "• Index 3 = Third latest\n"
                "• And so on..."
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎯 Other Commands",
            value=(
                "`!latest` - Get latest reports with files\n"
                "`!archive gl/ko` - Browse all reports\n"
                "`!reports` - List available report files"
            ),
            inline=False
        )
        
        embed.set_footer(text="BDO Intelligence Archive • Command Help")
        await ctx.send(embed=embed)
    
    async def _show_paginated_archive(self, ctx, source: str):
        """Show paginated archive (simplified version)"""
        try:
            all_reports = self.db.get_all_reports(source, 50)  # Get up to 50
            
            if not all_reports:
                await ctx.send(f"❌ No reports found in {source} archive")
                return
            
            embed = discord.Embed(
                title=f"📚 {source} - Complete Archive ({len(all_reports)} reports)",
                color=0x00ff88 if 'Global' in source else 0xff6b35
            )
            
            # Show all reports in a compact format
            report_list = []
            for i, report in enumerate(all_reports, 1):
                date_short = report['generated_at'][:10]
                title_short = report['title'][:40] + "..." if len(report['title']) > 40 else report['title']
                report_list.append(f"`#{i}` {date_short} - {title_short}")
            
            # Split into chunks if too long
            chunk_size = 20
            chunks = [report_list[i:i + chunk_size] for i in range(0, len(report_list), chunk_size)]
            
            for i, chunk in enumerate(chunks[:3]):  # Show max 3 chunks (60 reports)
                field_name = "📋 Reports" if i == 0 else f"📋 Reports (continued {i+1})"
                embed.add_field(
                    name=field_name,
                    value="\n".join(chunk),
                    inline=False
                )
            
            if len(all_reports) > 60:
                embed.add_field(
                    name="ℹ️ Note",
                    value=f"Showing first 60 reports of {len(all_reports)} total. Use specific index to access older reports.",
                    inline=False
                )
            
            source_short = 'gl' if 'Global' in source else 'ko'
            embed.add_field(
                name="📖 Access Reports",
                value=f"Use `!history {source_short} [number]` to get specific reports",
                inline=False
            )
            
            embed.set_footer(text="BDO Intelligence Complete Archive")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing archive for {source}: {e}")
            await ctx.send("❌ Error retrieving archive")
    
    @commands.command(name='reports')
    async def list_reports(self, ctx):
        """List available AI reports (existing command - keep as is)"""
        try:
            reports_folder = self.ai_analyzer.reports_folder
            
            if not os.path.exists(reports_folder):
                await ctx.send("📂 No reports folder found")
                return
            
            files = [f for f in os.listdir(reports_folder) if f.endswith('.txt')]
            
            if not files:
                await ctx.send("📂 No AI analysis reports available")
                return
            
            # Sort by creation time
            files_with_time = [(f, os.path.getctime(os.path.join(reports_folder, f))) for f in files]
            files_with_time.sort(key=lambda x: x[1], reverse=True)
            
            embed = discord.Embed(
                title="📊 Available AI Analysis Reports (Files)",
                color=0x00ff88
            )
            
            global_lab_reports = []
            korean_reports = []
            
            for filename, _ in files_with_time[:10]:  # Show latest 10
                if 'global_lab' in filename:
                    global_lab_reports.append(filename)
                elif 'korean' in filename:
                    korean_reports.append(filename)
            
            if global_lab_reports:
                embed.add_field(
                    name="🌐 Global Labs Reports",
                    value="\n".join([f"• `{f}`" for f in global_lab_reports[:5]]),
                    inline=False
                )
            
            if korean_reports:
                embed.add_field(
                    name="🇰🇷 Korean Notice Reports", 
                    value="\n".join([f"• `{f}`" for f in korean_reports[:5]]),
                    inline=False
                )
            
            embed.add_field(
                name="💡 Better Commands",
                value=(
                    "`!latest gl` - Get latest Global Labs report\n"
                    "`!history ko 3` - Get 3rd latest Korean report\n"
                    "`!archive gl` - Browse all Global Labs reports"
                ),
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error listing reports: {e}")
            await ctx.send("❌ Error retrieving report list")
    
    @commands.command(name='help')
    async def help_command(self, ctx):
        """Show comprehensive help information for all bot commands"""
        
        # Create main help embed
        embed = discord.Embed(
            title="📖 BDO Patch Bot - Complete Command Guide",
            description="🤖 **AI-Powered Black Desert Online Patch Analysis & Intelligence Reports**\n\n*Your comprehensive BDO patch monitoring and analysis companion*",
            color=0x0099ff,
            timestamp=ctx.message.created_at
        )
        
        # Latest Reports Section
        embed.add_field(
            name="📊 **Latest Reports Commands**",
            value=(
                "`!latest` - Get latest AI analysis reports from both sources\n"
                "`!latest gl` - Get latest Global Labs intelligence report\n"
                "`!latest ko` - Get latest Korean notice intelligence report\n"
                "`!latest global` - Alternative for Global Labs\n"
                "`!latest korean` - Alternative for Korean notices"
            ),
            inline=False
        )
        
        # Historical Access Section
        embed.add_field(
            name="📚 **Historical Access Commands**",
            value=(
                "`!history gl` - List all available Global Labs reports\n"
                "`!history ko` - List all available Korean notice reports\n"
                "`!history gl 3` - Get 3rd latest Global Labs report\n"
                "`!history ko 1` - Get latest Korean report (by index)\n"
                "`!history` - Show help for history command usage"
            ),
            inline=False
        )
        
        # Archive & File Management
        embed.add_field(
            name="🗄️ **Archive & File Commands**",
            value=(
                "`!archive gl` - Browse complete Global Labs archive\n"
                "`!archive ko` - Browse complete Korean notice archive\n"
                "`!reports` - List all available report files\n"
                "`!status` - Show database status and latest report info"
            ),
            inline=False
        )
        
        # Configuration Commands
        embed.add_field(
            name="⚙️ **Server Configuration Commands**",
            value=(
                "`!usepatch` - Set current channel for patch notifications\n"
                "`!bdolan <lang>` - Set translation language\n"
                "`!config` - Show current server configuration settings"
            ),
            inline=False
        )
        
        # Language Options
        embed.add_field(
            name="🌐 **Supported Languages**",
            value=(
                "**Available for `!bdolan` command:**\n"
                "• `en` - English (default)\n"
                "• `ko` - Korean\n"
                "• `es` - Spanish\n"
                "• `fr` - French\n"
                "• `de` - German\n"
                "• `ja` - Japanese"
            ),
            inline=True
        )
        
        # Bot Features
        embed.add_field(
            name="🤖 **AI Analysis Features**",
            value=(
                "• **Deep Content Analysis** of patch notes\n"
                "• **Strategic Intelligence Reports** with meta impact\n"
                "• **Professional Military-Style Briefings**\n"
                "• **Automatic Monitoring** every 15 minutes\n"
                "• **Historical Archive Access** for all reports\n"
                "• **Multi-Language Support** for translations"
            ),
            inline=True
        )
        
        # Usage Examples
        embed.add_field(
            name="💡 **Quick Start Examples**",
            value=(
                "**Setup:** `!usepatch` → `!bdolan en`\n"
                "**Get Latest:** `!latest gl` or `!latest ko`\n"
                "**Browse History:** `!history gl` → `!history gl 3`\n"
                "**Check Status:** `!status`\n"
                "**View Archive:** `!archive ko`"
            ),
            inline=False
        )
        
        # Bot Information
        embed.add_field(
            name="ℹ️ **How It Works**",
            value=(
                "1. **Monitors** Korean notices & Global Labs automatically\n"
                "2. **AI Analyzes** patch content using advanced language models\n"
                "3. **Generates** comprehensive intelligence reports (.txt files)\n"
                "4. **Delivers** reports instantly via Discord commands\n"
                "5. **Maintains** complete historical archive for reference"
            ),
            inline=False
        )
        
        # Footer with additional info
        embed.set_footer(
            text="BDO Intelligence Division • AI-Powered Analysis • Developed for Competitive Players",
            icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None
        )
        
        # Add thumbnail if bot has avatar
        if ctx.bot.user.avatar:
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)
        
        # Send the main help embed
        message = await ctx.send(embed=embed)
        
        # Add helpful reactions
        try:
            await message.add_reaction("📊")  # Analysis
            await message.add_reaction("⚙️")  # Config
            await message.add_reaction("📚")  # Archive
            await message.add_reaction("🤖")  # AI
        except:
            pass  # Ignore reaction errors
        
        # Send follow-up embed with permissions and troubleshooting
        followup_embed = discord.Embed(
            title="🔧 Additional Information",
            color=0x36393f
        )
        
        followup_embed.add_field(
            name="🛡️ **Required Permissions**",
            value=(
                "**For `!usepatch`:** Manage Channels or Administrator\n"
                "**For other commands:** No special permissions needed\n"
                "**Bot needs:** Send Messages, Attach Files, Add Reactions"
            ),
            inline=False
        )
        
        followup_embed.add_field(
            name="🆘 **Troubleshooting**",
            value=(
                "• **No reports?** Check `!status` for database info\n"
                "• **Old reports?** Bot prioritizes by actual patch date\n"
                "• **Korean text issues?** UTF-8 encoding automatically handled\n"
                "• **Missing files?** Reports are generated automatically"
            ),
            inline=False
        )
        
        followup_embed.add_field(
            name="🎯 **Pro Tips**",
            value=(
                "• Use `!history` for accessing older intelligence reports\n"
                "• Reports include strategic analysis and meta implications\n"
                "• Bot distinguishes between Global Labs tests and live patches\n"
                "• All reports are saved as downloadable .txt files"
            ),
            inline=False
        )
        
        await ctx.send(embed=followup_embed)

# Setup function
async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(PatchCommands(bot))
