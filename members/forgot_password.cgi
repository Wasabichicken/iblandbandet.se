#!/usr/bin/env python3

import os
import smtplib
import sys
from urllib.parse import parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_path import absolute_url
from dal.members import get_member_by_email
from dal.password_resets import create_reset_token
from layout import render
from mailer import send_email
from session_auth import current_member

GENERIC_MESSAGE = ('Om det finns ett konto med den e-postadressen har ett e-postmeddelande '
                    'med instruktioner för att byta lösenord skickats dit.')

EMAIL_BODY = """Hej,

Vi har fått en begäran om att byta lösenord för ditt konto på (i)Blandbandet.
Om det var du som bad om detta, klicka på länken nedan för att välja ett
nytt lösenord. Länken slutar gälla om en timme.

{link}

Bad du inte om detta kan du bortse från det här meddelandet - ditt
lösenord ändras inte förrän någon klickar på länken ovan och väljer ett
nytt.

/(i)Blandbandet
"""


def render_page(message=None, message_kind=None):
    member, _ = current_member()
    render(
        'forgot_password.mako',
        title='Glömt lösenord — (i)Blandbandet',
        member=member,
        message=message,
        message_kind=message_kind,
    )


def read_form():
    length = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    body = sys.stdin.read(length)
    parsed = parse_qs(body)
    return parsed.get('email', [''])[0].strip()


def main():
    if os.environ.get('REQUEST_METHOD', 'GET') != 'POST':
        render_page()
        return

    email = read_form()
    member = get_member_by_email(email) if email else None

    if member is not None:
        token = create_reset_token(member.id)
        link = absolute_url('/members/reset_password.cgi?token={}'.format(token))
        try:
            send_email(member.email, 'Byt lösenord — (i)Blandbandet', EMAIL_BODY.format(link=link))
        except (smtplib.SMTPException, OSError):
            # Swallowed deliberately, not logged anywhere - accum.se gives no
            # accessible error log, and showing a different message here
            # would leak "this email has an account" to anyone who already
            # knows a valid one, undermining GENERIC_MESSAGE's whole point.
            # A real outage (this exact bug: an unfilled/expired
            # SMTP_PASSWORD) needs to be caught by testing the flow
            # directly, not by a user-visible signal.
            pass

    render_page(message=GENERIC_MESSAGE, message_kind='success')


if __name__ == '__main__':
    main()
