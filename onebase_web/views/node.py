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
import logging

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
)
from wtforms import (
    StringField
)

from onebase_api.models.main import (
    Path,
    Node,
)
from onebase_web.views.auth import (
    login_required,
    permissions_required,
    get_user,
)
from onebase_web.forms import (
    CreateNodeForm,
)
from onebase_api.exceptions import (
    OneBaseException,
)
from onebase_common import settings as common_settings
from onebase_web import settings as web_settings

logger = logging.getLogger(__name__)

_tpl_dir = os.path.join(web_settings.TEMPLATES_DIR, 'node')

node_views = Blueprint('node', __name__, url_prefix='/node',
                       template_folder=_tpl_dir)


@node_views.route('/search', methods=['GET', ])
def find_node():
    """ Find a node by a given path. """
    search = request.args.get('path')
    node = Path.find(search)
    return render_template("search.html", node=node)


@node_views.route('/browse', methods=['GET', ])
def browse_nodes():
    """ Browse the nodes, one after another. """
    path = request.args.get('path', None)
    if path is None:
        current = None
        node = None
        children = Path.objects(parent=None).all()
    else:
        current = Path.find(path)
        node = current.node
        children = path.children()
    return render_template('browse.html',
                           title=(path or 'Browse Paths & Nodes'),
                           node=node,
                           path=current,
                           children=children)


@node_views.route('/create', methods=['GET', 'POST', ])
@login_required
@permissions_required('create_node')
def create_node(*args, **kwargs):
    """ Create a new Node. """
    class FieldedNodeForm(CreateNodeForm):
        pass
    key_count = int(request.values.get('keyCount', 1))
    for i in range(0, key_count+1):
        f1 = 'key_{}_name'.format(i)
        f2 = 'key_{}_type'.format(i)
        key_name = request.values.get(f1)
        key_type = request.values.get(f2)
        setattr(FieldedNodeForm, f1, StringField(value=key_name))
        setattr(FieldedNodeForm, f2, StringField(value=key_type))

    logger.debug('arguments: {}'.format(args))
    assert len(args) == 0 and len(kwargs.items()) == 0
    template = "create.html"
    path = request.args.get('path')
    form = CreateNodeForm(path=path)
    if request.method == 'POST':
        form = CreateNodeForm(**request.data)
        created = form.submit(get_user())
        if created is not None:
            return redirect(url_for='get_node', node_id=created.id)
    if path is None:
        raise OneBaseException('E-207')
    add_key_url = request.url + '?path=' + request.args.get('path') + \
                   '&keyCount=' + str(key_count+1)
    return render_template(template, form=form, path=path,
                           pathparts=path.split("/"),
                           add_key_url=add_key_url)


@node_views.route('/', methods=['GET', ])
def get_node(*args, **kwargs):
    """ View a node. """
    logger.debug('arguments: {}'.format(args))
    return render_template('view_node')
