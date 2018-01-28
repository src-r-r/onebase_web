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
    abort,
    url_for,
)
from wtforms import (
    IntegerField,
    StringField,
    SelectField,
    Label,
)

from onebase_api.models.history import (
    Action,
)
from onebase_api.models.main import (
    Path,
    Node,
    Type,
    Slot,
    Key,
    create_node_at_path,
)
from onebase_web.views.auth import (
    login_required,
    permissions_required,
    get_user,
)
from onebase_web.forms import (
    CreateNodeForm,
    SlotInsertForm,
)
from onebase_common.util import (
    reconstruct_url,
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


@node_views.route('/search', methods=['GET', 'POST', ])
def view_node():
    """ Find a node by a given path. """
    search = request.args.get('path')
    node = getattr(Path.find(search), 'node', None)
    title = 'No Node'
    offset = int(request.args.get('offset', 0))
    count = int(request.args.get('count', 100))
    query_set = []
    start=None
    end=None
    total=None
    node_keys = []
    if Path.find(search) is not None and node is None:
        return redirect(url_for('node.browse_nodes', path=search))
    if node is not None:
        if request.method == 'POST' and 'DELETE' in request.form:
            logger.debug("Delete nodes ?")
            if 'select_row' in request.form:
                rows = ','.join(request.form.getlist('select_row'))
                return redirect(url_for('node.drop_slot',
                                        path=search,
                                        rows=rows))
        environment = {
            'return_mimetype': 'application/html',
            'static_url': common_settings.CONFIG['static'][
                common_settings.ONEBASE_MODE],
        }
        total = node.row_count
        title = 'Node: {}'.format(node.title)
        total = node.row_count
        node_keys = node.get_keys()
        query_set = node.do_select(offset=offset,
                                   limit=count,
                                   expand_keys=True,
                                   expand_slots=True,
                                   environment=environment)
        import pprint
        logger.debug("Query set: {}".format(pprint.pformat(query_set)))
    return render_template("search.html", node=node,
                           path=Path.find(search),
                           title=title,
                           node_keys=node_keys,
                           query_set=query_set,
                           start=offset,
                           end=offset+count,
                           total=total)


@node_views.route('/slot/drop/', methods=['GET', 'POST'])
@login_required
@permissions_required('slot_drop')
def drop_slot():
    path = request.args['path']
    row_nums = [int(i) for i in request.args['rows'].split(",")]
    node = Path.find(path).node
    rows = []
    e = {'return_mimetype': 'application/html',
         'static_url': common_settings.CONFIG['static'][
             common_settings.ONEBASE_MODE], }
    to_delete = []
    for row_num in row_nums:
        row = []
        for key in node.get_keys():
            slot = Slot.objects(key=key, row=row_num).first()
            to_delete.append(slot)
            row.append(slot.get_repr(environment=e))
        rows.append(row)
    if request.method == 'GET':
        return render_template('drop.html', rows=rows)
    elif request.method == 'POST' and 'YES' in request.form:
        for s in to_delete:
            Slot.objects(id=s.id).delete()
    return redirect(url_for('node.view_node', path=request.args['path']))


@node_views.route('/slot/update/<row>', methods=['GET', 'POST'])
@login_required
@permissions_required('node_update')
def update_slow_row(row):
    path = request.args['path']
    node = Path.find(path).node
    if node is None:
        return abort(404)

    class DynSlotInsertForm(SlotInsertForm):
        pass

    for key in node.get_keys():
        slot = Slot.objects(row=int(row), key=key.id).first()
        logger.debug('adding field {}'.format(key.name))
        setattr(DynSlotInsertForm, key.name, StringField(default=slot.value))
        DynSlotInsertForm.ext_keys.update({key.name: key, })

    form = DynSlotInsertForm(request.form)

    if request.method == 'POST':
        if form.validate():
            form.submit(node=node, user=get_user(), update_row=row)
            return redirect(url_for('node.view_node', path=path))
    return render_template('update.html', form=form,
                           title='Insert into {}'.format(node.title))

@node_views.route('/slot/add', methods=['GET', 'POST'])
@login_required
@permissions_required('node_modify')
def add_slot_row():
    path = request.args['path']
    node = Path.find(path).node
    if node is None:
        return abort(500)

    class DynSlotInsertForm(SlotInsertForm):
        pass

    for key in node.get_keys():
        logger.debug('adding field {}'.format(key.name))
        setattr(DynSlotInsertForm, key.name, StringField())
        DynSlotInsertForm.ext_keys.update({key.name: key, })

    form = DynSlotInsertForm(request.form)

    if request.method == 'POST':
        if form.validate():
            form.submit(node=node, user=get_user())
            return redirect(url_for('node.view_node', path=path))
    return render_template('insert.html', form=form,
                           title='Insert into {}'.format(node.title))


@node_views.route('/browse', methods=['GET', ])
def browse_nodes():
    """ Browse the nodes, one after another. """
    path = request.args.get('path', '')
    current = None
    node = None
    children = []
    if path is None or path == '':
        children = Path.objects(parent=None).all()
    else:
        current = Path.find(path)
        if current:
            node = current.node
            children = current.paths()
    if node is not None:
        return redirect(url_for('node.view_node', path=path))
    return render_template('browse.html',
                           title=(path or 'Browse Paths & Nodes'),
                           node=node,
                           current=current,
                           children=children)


@node_views.route('/create', methods=['GET', 'POST', ])
@login_required
@permissions_required('create_node')
def create_node(*args, **kwargs):
    """ Create a new Node. """
    class FieldedNodeForm(CreateNodeForm):
        pass
    key_count = int(request.values.get('keyCount', 1))
    logger.debug("begin adding {} fields".format(key_count))
    for i in range(0, key_count):
        f1 = 'key_{}_name'.format(i)
        f2 = 'key_{}_type'.format(i)
        f3 = 'key_{}_size'.format(i)
        logger.debug("Adding {}, {}".format(f1, f2))
        key_name = request.values.get(f1)
        key_type = request.values.get(f2)
        setattr(FieldedNodeForm, f1, StringField('Key {} Name'.format(i),
                                                 default=key_name))
        setattr(FieldedNodeForm, f2, SelectField(default=key_type,
                                                 choices=Type.as_select()))
        setattr(FieldedNodeForm, f3, IntegerField())
        logger.debug("FieldedNodeForm now has {} fields".format(
            len(
                [f for f in FieldedNodeForm.__dict__.keys()
                    if f.startswith('key')]
            )
        ))

    if request.method == 'POST':
        logger.debug("Form data: {}".format(dict(request.form)))
        assert len(request.form['path']) > 1
        form = FieldedNodeForm(request.form)
        if form.validate():
            u = get_user()
            created_node = form.submit(u)
            return redirect(url_for('node.view_node',
                                    path=request.args['path']))
        logger.debug('{} did not validate'.format(form))

    logger.debug('arguments: {}'.format(args))
    assert len(args) == 0 and len(kwargs.items()) == 0
    template = "create.html"
    path = request.args.get('path')
    form = FieldedNodeForm(request.values)
    if path is None:
        raise OneBaseException('E-207')
    updated_kw = {'keyCount': str(key_count+1), }
    add_key_url = reconstruct_url(request, updated_kw)
    return render_template(template, form=form, path=path,
                           pathparts=path.split("/"),
                           add_key_url=add_key_url)


@node_views.route('/', methods=['GET', ])
def get_node(*args, **kwargs):
    """ View a node. """
    logger.debug('arguments: {}'.format(args))
    return render_template('view_node')
