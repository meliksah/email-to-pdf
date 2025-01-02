"""Main converter class that coordinates email processing and PDF generation"""

import signal
from multiprocessing import Pool
from typing import Dict, Any, List, Tuple
import time
import os

from .handlers.imap_handler import IMAPHandler
from .handlers.pdf_handler import PDFGenerator
from .parsers.email_parser import EmailParser

class EmailToPDF:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.pdf_generator = PDFGenerator()
        self.max_retries = 3
        self.retry_delay = 1

    def process_emails(self, from_email: str, subject: str) -> None:
        """Process emails and convert them to PDFs"""
        try:
            # Create temporary IMAP handler for initial search
            imap_handler = IMAPHandler(self.host, self.port, self.username, self.password)
            message_numbers = imap_handler.search_emails(from_email, subject)
            
            if not message_numbers:
                print("No matching emails found")
                return

            # Prepare arguments for parallel processing
            process_args = [
                (msg_num, from_email, subject, self.host, self.port, self.username, self.password)
                for msg_num in message_numbers
            ]
            
            num_processes = min(os.cpu_count() or 1, len(message_numbers))
            with Pool(processes=num_processes, initializer=self._init_worker) as pool:
                results = [
                    pool.apply_async(self._process_email_in_process, args=(args,))
                    for args in process_args
                ]
                
                for result in results:
                    try:
                        pdf_file = result.get(timeout=60)
                        print(f"Created PDF: {pdf_file}")
                    except Exception as e:
                        print(f"Error processing email: {str(e)}")

        except Exception as e:
            print(f"Error in process_emails: {str(e)}")

    @staticmethod
    def _process_email_in_process(args: Tuple) -> str:
        """Static method to process email in a separate process"""
        message_number, from_email, subject, host, port, username, password = args
        
        # Create new IMAP handler in this process
        imap_handler = IMAPHandler(host=host, port=port, username=username, password=password)
        pdf_generator = PDFGenerator()
        
        try:
            imap = imap_handler.get_connection()
            if not imap:
                raise Exception("Could not establish IMAP connection")
            
            imap.select('INBOX')
            _, msg_data = imap.fetch(message_number, '(RFC822)')
            if not msg_data or not msg_data[0]:
                raise Exception("No email data received")
            
            email_data = EmailParser.parse_email_content(msg_data)
            return pdf_generator.generate_pdf(email_data)
            
        except Exception as e:
            raise Exception(f"Process error: {str(e)}")
        finally:
            imap_handler.close_connection()

    @staticmethod
    def _init_worker():
        """Initialize worker process to ignore SIGINT"""
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def __getstate__(self):
        """Control which attributes are pickled for multiprocessing"""
        return {
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            'pdf_generator': self.pdf_generator,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay
        }

    def __setstate__(self, state):
        """Restore instance attributes when unpickling"""
        self.__dict__.update(state)
        # Store credentials as class attributes for the static method
        EmailToPDF._process_email_in_process.host = state['host']
        EmailToPDF._process_email_in_process.port = state['port']
        EmailToPDF._process_email_in_process.username = state['username']
        EmailToPDF._process_email_in_process.password = state['password'] 