import argparse
from src.email_to_pdf import EmailToPDF

def main():
    parser = argparse.ArgumentParser(description='Convert emails to PDF based on search criteria')
    parser.add_argument('--host', required=True, help='IMAP server host')
    parser.add_argument('--port', type=int, required=True, help='IMAP server port')
    parser.add_argument('--username', required=True, help='Email username')
    parser.add_argument('--password', required=True, help='Email password')
    parser.add_argument('--from-email', required=True, help='Search for emails from this address')
    parser.add_argument('--subject', required=True, help='Search for emails with this subject')

    args = parser.parse_args()

    converter = EmailToPDF(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password
    )

    converter.process_emails(args.from_email, args.subject)

if __name__ == "__main__":
    main() 