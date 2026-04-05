# run this as a standalone script from your project root
import smtplib, os
from dotenv import load_dotenv

load_dotenv()

with smtplib.SMTP(os.environ["MAIL_SERVER"], int(os.environ["MAIL_PORT"])) as smtp:
    smtp.ehlo()
    smtp.starttls()
    smtp.login(os.environ["MAIL_USERNAME"], os.environ["MAIL_PASSWORD"])
    print("LOGIN OK")
