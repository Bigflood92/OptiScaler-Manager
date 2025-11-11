"""Logging utilities for FSR Injector."""

import logging
import os
from datetime import datetime
from ..config.paths import LOG_DIR

class LogManager:
    """Manages logging operations for FSR Injector."""
    
    def __init__(self, log_dir=None):
        """Initialize the log manager.
        
        Args:
            log_dir (str): Directory to store log files. If None, uses LOG_DIR from paths.py
        """
        self.log_dir = str(log_dir) if log_dir else str(LOG_DIR)
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Configure file handler
        log_file = os.path.join(self.log_dir, f"fsr_injector_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # Configure console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Configure root logger
        self.logger = logging.getLogger('fsr_injector')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Map log levels to colors/prefixes for UI
        self.ui_log_config = {
            'INFO': ('#00FF00', '[INFO] '),
            'WARN': ('#FFFF00', '[WARN] '),
            'ERROR': ('#FF4500', '[ERROR] '),
            'TITLE': ('#00BFFF', '[OP] '),
            'OK': ('#00FF00', '[OK] ')
        }

    def log_to_ui(self, log_type, message, textbox=None):
        """Log a message to both the logger and UI textbox if provided.
        
        Args:
            log_type (str): Type of log message ('INFO', 'WARN', 'ERROR', etc.)
            message (str): The message to log
            textbox (CTkTextbox, optional): CustomTkinter textbox to display the message
        """
        # Map UI log types to logging levels
        level_map = {
            'INFO': logging.INFO,
            'WARN': logging.WARNING,
            'ERROR': logging.ERROR,
            'TITLE': logging.INFO,
            'OK': logging.INFO
        }
        
        # Log to file/console
        level = level_map.get(log_type, logging.INFO)
        self.logger.log(level, message)
        
        # Log to UI if textbox provided
        if textbox:
            try:
                color, prefix = self.ui_log_config.get(log_type, ('white', ''))
                textbox.configure(state="normal")
                textbox.insert("end", prefix, log_type)
                textbox.tag_config(log_type, foreground=color)
                textbox.insert("end", f"{message}\n")
                textbox.configure(state="disabled")
                
                # Scroll to end if auto-scroll is enabled
                if hasattr(textbox, 'auto_scroll') and textbox.auto_scroll:
                    textbox.see("end")
            except Exception as e:
                self.logger.error(f"Failed to log to UI: {e}")
                
    def archive_old_logs(self, max_age_days=30):
        """Archive log files older than specified days.
        
        Args:
            max_age_days (int): Maximum age of logs in days before archiving
        """
        try:
            now = datetime.now()
            archive_dir = os.path.join(self.log_dir, "archive")
            os.makedirs(archive_dir, exist_ok=True)
            
            for file in os.listdir(self.log_dir):
                if not file.endswith(".log"):
                    continue
                    
                file_path = os.path.join(self.log_dir, file)
                file_date = datetime.fromtimestamp(os.path.getmtime(file_path))
                age_days = (now - file_date).days
                
                if age_days > max_age_days:
                    archive_path = os.path.join(archive_dir, file)
                    os.rename(file_path, archive_path)
                    self.logger.info(f"Archived old log file: {file}")
        except Exception as e:
            self.logger.error(f"Failed to archive old logs: {e}")
            
    def cleanup_archives(self, max_archive_size_mb=100):
        """Clean up archived logs if total size exceeds limit.
        
        Args:
            max_archive_size_mb (int): Maximum size of archive directory in MB
        """
        try:
            archive_dir = os.path.join(self.log_dir, "archive")
            if not os.path.exists(archive_dir):
                return
                
            # Get all log files with their sizes and dates
            log_files = []
            total_size = 0
            for file in os.listdir(archive_dir):
                if file.endswith(".log"):
                    file_path = os.path.join(archive_dir, file)
                    size = os.path.getsize(file_path)
                    date = os.path.getmtime(file_path)
                    log_files.append((file_path, size, date))
                    total_size += size
            
            # Convert to MB
            total_size_mb = total_size / (1024 * 1024)
            
            if total_size_mb > max_archive_size_mb:
                # Sort by date (oldest first)
                log_files.sort(key=lambda x: x[2])
                
                # Delete oldest files until under limit
                for file_path, size, _ in log_files:
                    os.remove(file_path)
                    total_size_mb -= size / (1024 * 1024)
                    self.logger.info(f"Deleted old archive: {os.path.basename(file_path)}")
                    if total_size_mb <= max_archive_size_mb:
                        break
        except Exception as e:
            self.logger.error(f"Failed to clean up archives: {e}")
            
    def get_recent_errors(self, max_count=10):
        """Get the most recent error messages from the current log file.
        
        Args:
            max_count (int): Maximum number of errors to retrieve
            
        Returns:
            list: List of recent error messages
        """
        try:
            errors = []
            with open(self.logger.handlers[0].baseFilename, 'r', encoding='utf-8') as f:
                for line in reversed(list(f)):
                    if 'ERROR' in line:
                        errors.append(line.strip())
                        if len(errors) >= max_count:
                            break
            return errors
        except Exception as e:
            self.logger.error(f"Failed to retrieve recent errors: {e}")
            return []