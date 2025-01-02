"""IMAP connection and email operations handler"""

import imaplib
import threading
from typing import List, Optional

class IMAPHandler:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._thread_local = threading.local()

    def get_connection(self) -> Optional[imaplib.IMAP4_SSL]:
        """Get or create thread-local IMAP connection"""
        if not hasattr(self._thread_local, 'imap'):
            try:
                self._thread_local.imap = imaplib.IMAP4_SSL(
                    host=self.host,
                    port=self.port,
                    timeout=30
                )
                self._thread_local.imap.login(self.username, self.password)
            except Exception as e:
                print(f"Connection failed: {str(e)}")
                return None
        return self._thread_local.imap

    def close_connection(self) -> None:
        """Close thread-local IMAP connection if it exists"""
        if hasattr(self._thread_local, 'imap'):
            try:
                self._thread_local.imap.close()
                self._thread_local.imap.logout()
            except:
                pass
            delattr(self._thread_local, 'imap')

    def search_emails(self, from_email: str, subject: str) -> List[bytes]:
        """Search for emails matching criteria"""
        try:
            imap = self.get_connection()
            if not imap:
                return []
                
            imap.select('INBOX')
            search_criteria = f'(FROM "{from_email}" SUBJECT "{subject}")'
            _, message_numbers = imap.search(None, search_criteria)
            
            return message_numbers[0].split() if message_numbers and message_numbers[0] else []
        except Exception as e:
            print(f"Search failed: {str(e)}")
            return [] 