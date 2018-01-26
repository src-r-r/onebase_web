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
from onebase_common.log.setup import configure_logging

from mongoengine import connect

from flask import (
    Flask,
    request,
    render_template,
)
from flask_login import (
    LoginManager
)

from onebase_api.models.main import (
    Path,
)
from onebase_web.views.auth import (
    ensure_admin_exists,
    auth_views,
    permissions_required,
    login_required,
)
from onebase_web.views.node import node_views
from onebase_web.views.types import type_views

from onebase_common.settings import CONFIG

from onebase_web import app


""" Set up logging
"""
configure_logging()
logger = logging.getLogger()

connect(CONFIG['collection'][CONFIG['mode']])

BLUEPRINTS = (
    auth_views,
    node_views,
    type_views,
)

for bp in BLUEPRINTS:
    app.register_blueprint(bp)

ensure_admin_exists()


@app.route('/', methods=['GET', ])
def index():
    """ Index landing page. """
    return render_template('index.html', title='Home')
