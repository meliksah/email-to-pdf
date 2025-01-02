"""Email content parsing and data extraction"""

import email
from email.header import decode_header
from datetime import datetime
import re
from typing import Dict, Any, Optional, Tuple

from bs4 import BeautifulSoup

class EmailParser:
    @staticmethod
    def extract_date_from_subject(subject: str, email_date: datetime) -> str:
        """Extract date from subject or fallback to email date"""
        pattern = r'on ([A-Za-z]+) (\d+)'
        match = re.search(pattern, subject)
        
        if match:
            try:
                month_name, day = match.groups()
                month_num = datetime.strptime(month_name, '%B').month
                return f"{email_date.year}{month_num:02d}{int(day):02d}"
            except ValueError:
                pass
        
        return email_date.strftime('%Y%m%d')

    @staticmethod
    def parse_email_content(msg_data: bytes) -> Dict[str, Any]:
        """Parse email content and extract relevant data"""
        email_body = msg_data[0][1]
        message = email.message_from_bytes(email_body)
        
        # Extract headers
        subject = decode_header(message["subject"])[0][0]
        subject = subject.decode() if isinstance(subject, bytes) else subject
        
        from_email = decode_header(message["from"])[0][0]
        from_email = from_email.decode() if isinstance(from_email, bytes) else from_email
        
        email_date = email.utils.parsedate_to_datetime(message["date"])
        
        # Get email body
        body = EmailParser._get_email_body(message)
        
        # Extract values from body
        gst_value, total_value = EmailParser._extract_values_from_body(body)
        
        return {
            "subject": subject,
            "from": from_email,
            "date": email_date,
            "body": body,
            "gst": gst_value,
            "total": total_value
        }

    @staticmethod
    def _get_email_body(message: email.message.Message) -> str:
        """Extract email body from message"""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() in ["text/html", "text/plain"]:
                    return part.get_payload(decode=True).decode(errors='ignore')
        return message.get_payload(decode=True).decode(errors='ignore')

    @staticmethod
    def _extract_values_from_body(body: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract GST and total values from email body"""
        soup = BeautifulSoup(body, 'html.parser')
        
        gst_value = None
        gst_row = soup.find('td', text=lambda t: t and 'GST' in t)
        if gst_row:
            gst_value_td = gst_row.find_next_sibling('td', class_='value')
            if gst_value_td:
                gst_value = gst_value_td.text.strip().replace('$', '').strip()

        total_value = None
        total_td = soup.find('td', class_='charge-total')
        if total_td:
            total_value = total_td.text.strip().replace('$', '').strip()

        return gst_value, total_value 