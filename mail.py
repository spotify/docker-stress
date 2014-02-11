import logging
import socket
import smtplib
from email.mime.text import MIMEText


log = logging.getLogger(__name__)


def send_mail(to=None, fromaddr=None, message=None):
    if not to:
        return
    try:
        assert message
        fqdn = socket.getfqdn()
        fromaddr = fromaddr or 'docker-stress@%s' % (fqdn, )

        msg = MIMEText(message)
        msg['Subject'] = 'docker-stress report for %s' % (fqdn, )
        msg['From'] = fromaddr
        msg['To'] = ','.join(to)

        s = smtplib.SMTP('localhost')
        s.sendmail(fromaddr, to, msg.as_string())
        s.quit()
    except:
        log.exception('failed to send alert email')
