"""Fixed database methods with proper date-based ordering"""
import sqlite3
import logging
from typing import Optional, Dict, Any, List
import json
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class BotDatabase:
    """Fixed database with proper patch date ordering"""
    
    def __init__(self, db_path: str = "bdo_bot.db"):
        self.db_path = db_path
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables with date parsing"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Server configurations
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS server_configs (
                        guild_id INTEGER PRIMARY KEY,
                        patch_channel_id INTEGER,
                        language TEXT DEFAULT 'en',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Enhanced AI reports table with date parsing
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT NOT NULL,
                        patch_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        date TEXT,
                        parsed_date DATE,  -- NEW: Properly parsed date for ordering
                        link TEXT,
                        report_filename TEXT,
                        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_notified BOOLEAN DEFAULT FALSE,
                        patch_data JSON,
                        UNIQUE(source, patch_id)
                    )
                ''')
                
                # Create index for better performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_reports_source_date 
                    ON ai_reports(source, parsed_date DESC, id DESC)
                ''')
                
                conn.commit()
                logger.info("Updated database tables created successfully")
                
        except Exception as e:
            logger.error(f"Database creation error: {e}")
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse various date formats into YYYY-MM-DD format"""
        if not date_str:
            return None
            
        try:
            # Clean the date string
            date_str = date_str.strip()
            
            # Try different formats
            formats = [
                '%Y-%m-%d',          # 2025-08-06
                '%Y.%m.%d',          # 2025.08.06
                '%b %d, %Y',         # Aug 6, 2025
                '%Y/%m/%d',          # 2025/08/06
                '%m/%d/%Y'           # 08/06/2025
            ]
            
            for fmt in formats:
                try:
                    parsed = datetime.strptime(date_str, fmt)
                    return parsed.strftime('%Y-%m-%d')
                except:
                    continue
            
            # Try regex patterns for partial matches
            patterns = [
                r'(\d{4})[.-](\d{1,2})[.-](\d{1,2})',  # 2025-08-06 or 2025.08.06
                r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # 08/06/2025
                r'(Aug|Jul|Sep|Oct|Nov|Dec|Jan|Feb|Mar|Apr|May|Jun)\s+(\d{1,2}),?\s+(\d{4})'  # Aug 6, 2025
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_str, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    if len(groups) == 3:
                        try:
                            if re.match(r'\d{4}', groups[0]):  # Year first
                                year, month, day = groups
                                parsed = datetime(int(year), int(month), int(day))
                            elif groups[2].isdigit() and len(groups[2]) == 4:  # Year last
                                month, day, year = groups
                                if groups[0].isalpha():  # Month name
                                    month_names = {
                                        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                                        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                                    }
                                    month = month_names.get(groups[0].lower()[:3], 1)
                                parsed = datetime(int(year), int(month), int(day))
                            return parsed.strftime('%Y-%m-%d')
                        except:
                            continue
            
            # If all parsing fails, try to extract just year-month-day numbers
            numbers = re.findall(r'\d+', date_str)
            if len(numbers) >= 3:
                # Assume first number > 2000 is year
                for i, num in enumerate(numbers):
                    if int(num) > 2000:
                        try:
                            year = int(num)
                            remaining = [int(x) for x in numbers if x != num]
                            if len(remaining) >= 2:
                                month, day = remaining[0], remaining[1]
                                if month > 12:  # Swap if needed
                                    month, day = day, month
                                parsed = datetime(year, month, day)
                                return parsed.strftime('%Y-%m-%d')
                        except:
                            continue
            
        except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {e}")
        
        return None
    
    def store_ai_report(self, patch_data: Dict[str, Any], report_filename: str, source: str) -> bool:
        """Store AI report with proper date parsing"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Parse the date properly
                parsed_date = self._parse_date(patch_data.get('date', ''))
                
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_reports 
                    (source, patch_id, title, date, parsed_date, link, report_filename, patch_data, generated_at, is_notified) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, FALSE)
                ''', (
                    source,
                    patch_data['id'],
                    patch_data['title'],
                    patch_data.get('date', ''),
                    parsed_date,
                    patch_data.get('link', ''),
                    report_filename,
                    json.dumps(patch_data)
                ))
                conn.commit()
                logger.info(f"Stored AI report: {report_filename} with parsed date: {parsed_date}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing AI report: {e}")
            return False
    
    def get_latest_report(self, source: str) -> Optional[Dict[str, Any]]:
        """Get latest AI report based on actual patch date - FIXED"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT patch_id, title, date, link, report_filename, generated_at, patch_data, parsed_date
                    FROM ai_reports 
                    WHERE source = ? 
                    ORDER BY 
                        CASE WHEN parsed_date IS NOT NULL THEN parsed_date ELSE '1900-01-01' END DESC,
                        generated_at DESC,
                        id DESC
                    LIMIT 1
                ''', (source,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'patch_id': result[0],
                        'title': result[1],
                        'date': result[2],
                        'link': result[3],
                        'report_filename': result[4],
                        'generated_at': result[5],
                        'patch_data': json.loads(result[6]),
                        'parsed_date': result[7]
                    }
                    
        except Exception as e:
            logger.error(f"Error getting latest report: {e}")
        
        return None
    
    def get_report_by_index(self, source: str, index: int) -> Optional[Dict[str, Any]]:
        """Get report by chronological index (1=latest by patch date)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT patch_id, title, date, link, report_filename, generated_at, patch_data, parsed_date
                    FROM ai_reports 
                    WHERE source = ? 
                    ORDER BY 
                        CASE WHEN parsed_date IS NOT NULL THEN parsed_date ELSE '1900-01-01' END DESC,
                        generated_at DESC,
                        id DESC
                    LIMIT 1 OFFSET ?
                ''', (source, index - 1))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'patch_id': result[0],
                        'title': result[1],
                        'date': result[2],
                        'link': result[3],
                        'report_filename': result[4],
                        'generated_at': result[5],
                        'patch_data': json.loads(result[6]),
                        'parsed_date': result[7]
                    }
                    
        except Exception as e:
            logger.error(f"Error getting report by index: {e}")
        
        return None
    
    def get_all_reports(self, source: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all reports ordered by patch date"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT patch_id, title, date, link, report_filename, generated_at, patch_data, parsed_date
                    FROM ai_reports 
                    WHERE source = ? 
                    ORDER BY 
                        CASE WHEN parsed_date IS NOT NULL THEN parsed_date ELSE '1900-01-01' END DESC,
                        generated_at DESC,
                        id DESC
                    LIMIT ?
                ''', (source, limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'patch_id': row[0],
                        'title': row[1],
                        'date': row[2],
                        'link': row[3],
                        'report_filename': row[4],
                        'generated_at': row[5],
                        'patch_data': json.loads(row[6]),
                        'parsed_date': row[7]
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting all reports: {e}")
            return []
    
    def update_existing_dates(self):
        """Update existing records with parsed dates - RUN ONCE"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all records without parsed_date
                cursor.execute('SELECT id, date FROM ai_reports WHERE parsed_date IS NULL')
                records = cursor.fetchall()
                
                for record_id, date_str in records:
                    parsed_date = self._parse_date(date_str)
                    cursor.execute('UPDATE ai_reports SET parsed_date = ? WHERE id = ?', 
                                 (parsed_date, record_id))
                
                conn.commit()
                logger.info(f"Updated {len(records)} records with parsed dates")
                
        except Exception as e:
            logger.error(f"Error updating existing dates: {e}")
    
    def count_reports(self, source: str) -> int:
        """Count total reports for a source - NEW METHOD"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM ai_reports WHERE source = ?', (source,))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error counting reports: {e}")
            return 0

    def is_report_new(self, source: str, patch_id: str) -> bool:
        """Check if we need to generate a new report"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id FROM ai_reports 
                    WHERE source = ? AND patch_id = ?
                ''', (source, patch_id))
                
                return cursor.fetchone() is None
                
        except Exception as e:
            logger.error(f"Error checking if report is new: {e}")
            return True
    
    def mark_report_notified(self, source: str, patch_id: str) -> bool:
        """Mark report as notified to Discord"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE ai_reports 
                    SET is_notified = TRUE 
                    WHERE source = ? AND patch_id = ?
                ''', (source, patch_id))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error marking report as notified: {e}")
            return False
    
    def get_unnotified_reports(self) -> List[Dict[str, Any]]:
        """Get reports that haven't been sent to Discord yet"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT source, patch_id, title, report_filename, patch_data
                    FROM ai_reports 
                    WHERE is_notified = FALSE 
                    ORDER BY generated_at ASC
                ''')
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'source': row[0],
                        'patch_id': row[1],
                        'title': row[2],
                        'report_filename': row[3],
                        'patch_data': json.loads(row[4])
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting unnotified reports: {e}")
            return []
    
    # Server configuration methods
    def set_patch_channel(self, guild_id: int, channel_id: int) -> bool:
        """Set patch notification channel for a server"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO server_configs 
                    (guild_id, patch_channel_id, updated_at) 
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (guild_id, channel_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting patch channel: {e}")
            return False
    
    def set_language(self, guild_id: int, language: str) -> bool:
        """Set language for a server"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO server_configs 
                    (guild_id, language, updated_at) 
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (guild_id, language))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting language: {e}")
            return False
    
    def get_server_config(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Get server configuration"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT patch_channel_id, language 
                    FROM server_configs 
                    WHERE guild_id = ?
                ''', (guild_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'channel_id': result[0],
                        'language': result[1]
                    }
        except Exception as e:
            logger.error(f"Error getting server config: {e}")
        return None
    
    def get_all_configured_servers(self) -> List[Dict[str, Any]]:
        """Get all servers with patch channels configured"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT guild_id, patch_channel_id, language 
                    FROM server_configs 
                    WHERE patch_channel_id IS NOT NULL
                ''')
                
                return [
                    {
                        'guild_id': row[0],
                        'channel_id': row[1],
                        'language': row[2] or 'en'
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Error getting configured servers: {e}")
            return []
