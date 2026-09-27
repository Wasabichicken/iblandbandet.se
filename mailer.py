import os
import shutil
import smtplib
import subprocess
from email.mime.text import MIMEText


def _build_message(to_addr, subject, body):
    message = MIMEText(body, 'plain', 'utf-8')
    message['Subject'] = subject
    message['From'] = os.environ['SMTP_FROM']
    message['To'] = to_addr
    return message


def _find_sendmail():
    return shutil.which('sendmail') or next(
        (path for path in ('/usr/sbin/sendmail', '/usr/lib/sendmail') if os.path.exists(path)), None)


def _send_via_local_sendmail(message):
    # Hands off to the host's own local MTA - no credentials needed, since
    # local mail submission is trusted by virtue of running as a real
    # local user (same "ident" trust pattern accum.se's Postgres also
    # relies on), not by proving a password. Confirmed empirically on
    # accum.se: this actually delivers (a raw SMTP connection to
    # localhost:25 does not - nothing listens there).
    path = _find_sendmail()
    if path is None:
        raise FileNotFoundError('no sendmail binary found')
    proc = subprocess.run(
        [path, '-t', '-oi'],
        input=message.as_string().encode('utf-8'),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
    )
    if proc.returncode != 0:
        raise OSError('sendmail exited {}: {}'.format(
            proc.returncode, proc.stderr.decode('utf-8', 'replace')))


def _send_via_smtp_auth(message, to_addr):
    host = os.environ.get('SMTP_HOST', 'mail.accum.se')
    port = int(os.environ.get('SMTP_PORT', 465))
    with smtplib.SMTP_SSL(host, port) as server:
        server.login(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
        server.sendmail(os.environ['SMTP_FROM'], [to_addr], message.as_string())


def send_email(to_addr, subject, body):
    message = _build_message(to_addr, subject, body)
    try:
        _send_via_local_sendmail(message)
    except Exception:
        _send_via_smtp_auth(message, to_addr)
