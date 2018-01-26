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

import logging
import os

from functools import (
    wraps
)

from flask import (
    abort,
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    session,
    g,
)


from onebase_common.util import (
    is_safe_url,
    hashpass,
)
from onebase_web.forms import (
    LoginForm,
    RegisterForm,
    # CreateNodeForm,
)
from onebase_api.models.auth import (
    User,
    Group,
)
from onebase_api.exceptions import OneBaseException
from onebase_common import settings as common_settings
from onebase_web import settings as web_settings
from onebase_web import app

logger = logging.getLogger(__name__)

_tpl_folder = os.path.join(web_settings.TEMPLATES_DIR, 'auth')
auth_views = Blueprint('auth', __name__,
                       template_folder=_tpl_folder)


def _create_password():
    import getpass
    (pw, pw2) = (None, 1)
    while pw != pw2:
        pw = getpass.getpass()
        pw2 = getpass.getpass('Confirm Password:')
        if pw != pw2:
            logger.error("Passwords do not match")
    return hashpass(pw)


def ensure_admin_exists():
    """ Ensure at least 1 administrator account exists. """
    logger.debug("Checking to make sure the administrator exists.")
    admin_group = Group.objects(name='admin').first()
    if not admin_group:
        logger.debug("creating admin group...")
        admin_group = Group(name='admin')
        admin_group.save()
    admin_user = User.objects(groups__in=[admin_group, ]).first()
    logger.debug(admin_user)
    if not admin_user:
        logger.info("The administrator account is being created.")
        logger.info("    - the email will be `admin@example.com`")
        logger.info("Please enter a password to use for adminstrator")
        admin_pw = _create_password()
        admin_user = User(email='admin@example.com', password=admin_pw,
                          groups=[admin_group, ],
                          is_active=True)
        admin_user.save()
        logger.info('Administrator created: {}'.format(admin_user))
    logger.debug('Done!')


def login_user(user):
    """ Log in the user.

    :return: True if the user has been logged in, False otherwise.

    """
    if user is None:
        return False
    logger.debug('User {} logged in'.format(user.id))
    g.user = user
    session['user'] = user.to_json()
    return True


def login_required(f):
    """ Require a user to log in to perform an action. """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if get_user() is None:
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def permissions_required(*permissions, **orig_kwargs):
    """ Require specific permissions to use a view.

    :param permissions: List of group permissions.

    :param logic: either 'and' or 'or'. defaults to 'and'

    """
    logic = orig_kwargs.get('logic', 'and')
    if logic not in ('and', 'or'):
        raise AttributeError('`logic` must be one of [\'and\', \'or\']')
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_user()
            if user is None:
                abort(403)
            if logic == 'or' and user.can_any(*permissions):
                return f(*args, **kwargs)
            elif logic == 'and' and user.can_all(*permissions):
                return f(*args, **kwargs)
            logger.error('User does not have permission!')
            raise OneBaseException('E-201', user=user,
                                   permissions=permissions)
        return decorated_function
    return decorator


def load_user(user_id):
    """ Load the user based on the user_id. """
    return User.objects(id=user_id).first()


def get_user(key='user', user_id_field='id'):
    """ Get the current user based on the session. """
    logger.debug("current user: {}".format(session.get('user')))
    with app.app_context():
        if key in session:
            if user_id_field in session[key]:
                return load_user(session[key][user_id_field])
    return None


@auth_views.route('/login', methods=['GET', 'POST'])
def login():
    """ Perform user login.

    Snippet taken from flask-login.
    """
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.

    title = 'Log In'
    template = 'login.html'

    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(formdata=request.form)
        pw = hashpass(form.data['password'])
        user = User.objects(email=form.data['email'],
                            password=pw).first()
        # Login and validate the user.
        # user should be an instance of your `User` class
        if not login_user(user):
            errors = ['Invalid Username or Password', ]
            return render_template(template,
                                   form=form,
                                   errors=errors,
                                   title=title)

        next = request.args.get('next')
        # is_safe_url should check if the url is safe for redirects.
        # See http://flask.pocoo.org/snippets/62/ for an example.
        if not is_safe_url(next):
            return abort(400)

        return redirect(next or url_for('index'))
    return render_template(template, form=form, title=title)


@auth_views.route('/register', methods=['GET', 'POST', ])
def register():
    """ Register a user. """
    form = RegisterForm()
    title = 'Register'
    template = 'register.html'
    if request.method == 'POST':
        logger.debug('method is post')
        form = RegisterForm(request.form)
        existing = User.objects(email=form.data['email']).first()
        if not form.validate():
            logger.debug('form did not validate')
            return render_template(template, title=title, form=form)
        if existing:
            logger.debug('user already exists')
            errors = [
                'User with email {} already exists'.format(existing.email),
            ]
            return render_template(template, errors=errors,
                                   title=title, form=form)
        user = User(email=form.data['email'],
                    password=hashpass(form.data['password']))
        user.save()
        u = '/validate?key={}'.format(user.verification)
        # TODO: send email to user
        logger.info('Verification URL: http://localhost:5000{}'.format(u))
        return render_template(template, email=form.email,
                               title=title)
    return render_template(template, title=title, form=form)


@auth_views.route('/logout', methods=['GET', ])
@login_required
def logout():
    """ End a user session. """
    del session['user']
    return redirect(url_for('index'))


@auth_views.route('/validate', methods=['GET', ])
def validate():
    """ Validate a user based on the key sent. """
    key = request.args.get('key')
    user = User.objects(verification=key).first()
    template = 'validate.html'
    title = 'User Account Verification'
    if user is None:
        errors = ['Verification key invalid.', ]
        return render_template(template, errors=errors, title=title)
    user.is_active = True
    user.save()
    return render_template(template, title=title, email=user.email)
