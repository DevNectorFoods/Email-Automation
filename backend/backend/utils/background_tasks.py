import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional

from ..config import Config
from ..models.db_models import db_manager
from ..services.email_service import EmailService

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    """Manages background tasks for the application."""
    
    def __init__(self):
        """Initialize the background task manager."""
        self.logger = logging.getLogger(__name__)
        self._running = False
        self._thread = None
        self._email_service = None
        self._interval = Config.BACKGROUND_TASK_INTERVAL
        
    def start(self):
        """Start the background task manager."""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._run_tasks)
        self._thread.daemon = True
        self._thread.start()
        
        self.logger.info("Background task manager started")
    
    def stop(self):
        """Stop the background task manager."""
        self._running = False
        if self._thread:
            self._thread.join()
            self._thread = None
    
    def _run_tasks(self):
        """Run background tasks in a loop."""
        self.logger.info(f"Background tasks started with {self._interval}s interval")
        
        while self._running:
            try:
                self._fetch_emails()
                self._sync_read_status()
                time.sleep(self._interval)
            except Exception as e:
                self.logger.error(f"Error in background tasks: {str(e)}")
                time.sleep(self._interval)
    
    def _sync_read_status(self):
        """Sync read status from email server to local database."""
        try:
            self.logger.info("Starting read status sync")
            
            if not self._email_service:
                self._email_service = EmailService()
            
            accounts = db_manager.get_email_accounts()
            if not accounts:
                self.logger.warning("No email accounts configured for read status sync")
                return
            
            for account in accounts:
                try:
                    self._email_service.sync_read_status_from_server(account)
                except Exception as e:
                    self.logger.error(f"Error syncing read status for {account.email}: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Background read status sync failed: {str(e)}")
    
    def _fetch_emails(self):
        """Fetch emails from all configured accounts."""
        try:
            self.logger.info("Starting automatic email fetch")
            
            if not self._email_service:
                self._email_service = EmailService()
            
            accounts = db_manager.get_email_accounts()
            if not accounts:
                self.logger.warning("No email accounts configured")
                return
            
            for account in accounts:
                try:
                    self._email_service.fetch_emails_from_account(account)
                except Exception as e:
                    self.logger.error(f"Error fetching emails for {account.email}: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Background email fetch failed: {str(e)}")
    
    def get_status(self) -> dict:
        """Get the status of background tasks."""
        return {
            'running': self._running,
            'last_run': getattr(self, '_last_run', None),
            'interval': self._interval,
            'thread_alive': self._thread and self._thread.is_alive()
        }
