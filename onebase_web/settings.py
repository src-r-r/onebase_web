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

import os

from onebase_common import settings as common_settings


HERE = os.path.abspath(os.path.dirname(__file__))
HOME = os.path.expanduser('~')
TEMPLATES_DIR = os.path.join(HERE, 'templates')

# Persistent User
# When doing development the user is often logged out because the session
# is refreshed. This setting will essentially keep a user logged in so that
# the developer won't have to constantly log in.
# The value is the email address associated with the persistent user account.
# It's set with the `ONEBASE_PERSIST_USER` environment variable.
# IMPORTANT: ONLY USE THIS SETTING FOR DEVELOPMENT!!
# Nod your head if you understand.
ONEBASE_PERSIST_USER = None
if common_settings.ONEBASE_MODE == common_settings.ONEBASE_DEV:
    ONEBASE_PERSIST_USER = os.environ.get('ONEBASE_PERSIST_USER', None)
