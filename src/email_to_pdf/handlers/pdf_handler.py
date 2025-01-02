"""PDF generation and file management handler"""

import os
import gc
import fcntl
from pathlib import Path
from typing import Dict, Any
import threading

from weasyprint import HTML
from jinja2 import Template

from ..parsers.email_parser import EmailParser

class PDFGenerator:
    def __init__(self):
        self.lock_dir = Path(os.getcwd()) / '.locks'
        self.lock_dir.mkdir(exist_ok=True, parents=True)
        self._lock = threading.Lock()

    def generate_pdf(self, email_data: Dict[str, Any]) -> str:
        """Generate PDF from email data"""
        html = self._render_template(email_data)
        filename = self._generate_filename(email_data)
        
        try:
            doc = HTML(string=html)
            doc.write_pdf(filename)
            
            if not os.path.exists(filename):
                raise Exception("PDF creation failed")
                
            return filename
        except Exception as e:
            raise Exception(f"PDF creation error: {str(e)}")
        finally:
            gc.collect()

    def _render_template(self, email_data: Dict[str, Any]) -> str:
        """Render HTML template with email data"""
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{{ subject }}</title>
        </head>
        <body>
            <div class="content">
                {{ body }}
            </div>
        </body>
        </html>
        """)
        
        return template.render(
            subject=email_data["subject"],
            from_email=email_data["from"],
            date=email_data["date"].strftime("%Y-%m-%d %H:%M:%S"),
            body=email_data["body"]
        )

    def _generate_filename(self, email_data: Dict[str, Any]) -> str:
        """Generate unique filename for PDF"""
        date_str = EmailParser.extract_date_from_subject(
            email_data["subject"], 
            email_data["date"]
        )
        
        base_filename = f"{date_str} - Lyft"
        if email_data.get('total'):
            base_filename += f" - {email_data['total']}"
        if email_data.get('gst'):
            base_filename += f" - GST {email_data['gst']}"
        base_filename = base_filename.replace("/", "-").replace(":", "-")
        
        return self._get_unique_filename(base_filename)

    def _get_unique_filename(self, base_filename: str) -> str:
        """Get unique filename using file locking"""
        lock_file = self.lock_dir / 'filename.lock'
        lock_file.touch(exist_ok=True)
        
        with open(lock_file, 'a+') as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                counter = 0
                while True:
                    filename = f"{base_filename}{' (' + str(counter) + ')' if counter else ''}.pdf"
                    if not os.path.exists(filename):
                        return filename
                    counter += 1
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN) 