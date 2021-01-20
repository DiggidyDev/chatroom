import getpass
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from user import User


class Emailer:

    CTX = ssl.create_default_context()
    EMAIL = "admin@diggydev.co.uk"
    PORT = 465
    PW = getpass.getpass("Password: ")
    SRV = "diggydev.co.uk"

    def __init__(self):
        pass

    @staticmethod
    def send_password_reset_to(self):
        pass

    def send_welcome_email_to(self, user: User = None):
        if not isinstance(user, User):
            raise TypeError(f"{type(user)!r} is not a valid target for sending emails to.")

        target = user.email

        msg = MIMEMultipart("alternative")

        msg["Subject"] = "Chatroom Registration"
        msg["From"] = self.EMAIL
        msg["To"] = target

        p_body = f"""
Hi {user}, thanks for joining Chatroom!
"""

        f_body = f"""
<html>
  <body>
    <p>Hi {user}!<br>Thanks for creating an account on Chatroom!<br><br>
    Regards,<br>Valentine
    </p>
  </body>
</html>
"""

        plain_text = MIMEText(p_body, "plain")
        fancy_text = MIMEText(f_body, "html")

        msg.attach(plain_text)
        msg.attach(fancy_text)

        with smtplib.SMTP_SSL(self.SRV, self.PORT, context=self.CTX) as server:
            server.login(self.EMAIL, self.PW)
            server.sendmail(self.EMAIL, target, msg.as_string())


pw = Emailer()
