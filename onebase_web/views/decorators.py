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

class AuthManager(object):

    def __init__(self, app):
        self.app = app

    def permissions_required(*permissions, **kwargs):
        """ Require specific permissions to use a view.

        :param permissions: List of group permissions.

        :param logic: either 'and' or 'or'. defaults to 'and'

        """
        logic = kwargs.get('logic', 'and')
        if logic not in ('and', 'or'):
            raise AttributeError()
        user = get_user()
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if user is None:
                    abort(403)
                if logic == 'or' and user.can_any(*permissions):
                    return f
                elif logic == 'and' and user.can_all(*permissions):
                    return f
                logger.error('User does not have permission!')
                raise OneBaseException('E-201', user=user)
            return decorated_function
        return decorator
