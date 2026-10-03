#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from layout import render
from session_auth import current_member


def main():
    member, _ = current_member()
    render(
        'privacy.mako',
        title='Integritetspolicy — (i)Blandbandet',
        member=member,
    )


if __name__ == '__main__':
    main()
