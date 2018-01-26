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
    Type,
)
from onebase_web.views.auth import (
    login_required,
    permissions_required,
    get_user,
)
from onebase_web.forms import (
    CreateNodeForm,
    CreateTypeForm,
)
from onebase_common import settings as common_settings
from onebase_web import settings as web_settings

logger = logging.getLogger(__name__)

_tpl_dir = os.path.join(web_settings.TEMPLATES_DIR, 'type')

type_views = Blueprint('type', __name__, url_prefix='/type',
                       template_folder=_tpl_dir)


@type_views.route('/', methods=['GET', ])
def list_types():
    """ List types. """
    return render_template("list.html", types=Type.objects.all(),
                           title="Types")


@type_views.route('/create', methods=['GET', 'POST', ])
@login_required
@permissions_required('create_type')
def create_type():
    """ Create a new type. """
    form = CreateTypeForm()
    if request.method == 'POST':
        form = CreateTypeForm(**request.form)
        logger.debug("Form data: {}".format(form.data))
        logger.debug("Request values: {}".format(request.form))
        if form.validate():
            type = Type(name=form.data['name'][0],
                        repr=form.data['repr'][0],
                        is_primitive=form.data['is_primitive'],
                        validator=form.data['validator'][0])
            if type.save(get_user()):
                return redirect(url_for('type.show_type',
                                        type_id=type.id))
    return render_template('type/create_type.html', form=form,
                           title="Create Type")


@type_views.route('/<type_id>')
def show_type(type_id):
    """ Show a type. """
    return render_template('show.html', type=Type.objects(id=type_id).first())


@type_views.route('/<type_id>/modify', methods=['GET', 'POST', ])
@login_required
@permissions_required('update_type')
def update_type(type_id):
    """ Update a type. """
    type = Type.objects(id=type_id).first()
    form = CreateTypeForm(**type.to_json())
    if request.method == 'POST':
        if form.validate():
            type.update(**form.data)
            if type.save(get_user()):
                return redirect(url_for='type.show_type')
    return render_template('type/create.html', form=form)


@type_views.route('/<type_id>/delete', methods=['GET', ])
@login_required
@permissions_required('delete_type')
def delete_type(type_id):
    """ Delete a given type. """
    type = Type.objects(id=type_id).first()
    if 'confirm' in request.args:
        if int(request.args['confirm']) == 1:
            type.delete()
        return render_template('type/delete.html',
                               confirm=request.args['confirm'],
                               title="Delete {}".format(type.name),
                               type=type)
    return render_template('type/delete.html', type=type,
                           title="Delete {}".format(type.name))
