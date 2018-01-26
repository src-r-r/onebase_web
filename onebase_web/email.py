#!/usr/bin/env python3
"""
This file is part of 1Base.

1Base is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

1Base is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with 1Base.  If not, see <http://www.gnu.org/licenses/>.
"""

import smtplib

import imghdr

from email.message import EmailMessage
from email.policy import SMTP

from onebase_common.settings import CONFIG

EMAIL = CONFIG['email']['smtp']

class UserVerificationEmail(EmailMessage):

    def __init__(self, user, verify_url='/verify',
                 email_config=EMAIL):
        super(UserVerificationEmail, self).__init__(*args, **kwargs)
