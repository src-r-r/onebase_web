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

import requests
import logging
from http import HTTPStatus as STATUS

logger = logging.getLogger(__name__)

from onebase_api.models.main import (
    create_node_at_path,
    Key,
    Type,
    Node,
    Path,
    Slot,
)

from onebase_api.exceptions import (
    OneBaseException,
)

from wtforms import (
    Form,
    StringField,
    PasswordField,
    TextAreaField,
    HiddenField,
    BooleanField,
    )
from wtforms.fields.html5 import EmailField

from onebase_web.fields import ReadOnlyField


class LoginForm(Form):
    email = EmailField()
    password = PasswordField()


class RegisterForm(Form):
    email = EmailField()
    password = PasswordField()
    password_confirm = PasswordField()

    def validate(self):
        if self.data['password'] == self.data['password_confirm']:
            return True
        errors = ('Passwords do not match', )
        self.password.errors = errors
        self.password_confirm.errors = errors
        return False


class CreateTypeForm(Form):
    """ Form to create database types. """
    name = StringField()
    repr = StringField(label='Representation URL')
    is_primitive = BooleanField()
    validator = StringField(label='Validator URL')


class SlotInsertForm(Form):

    ext_keys = {}

    def validate(self):
        for (k, v) in self.data.items():
            if k not in self.ext_keys:
                continue
            ext_key = self.ext_keys[k]
            t = ext_key.soft_type.fetch()
            try:
                t.validate_value(v, ext_key.size)
            except OneBaseException as e:
                if k not in self.errors:
                    self.errors[k] = []
                self.errors[k].append('{} - {}'.format(e.error_code, e))
                return False
        return True

    def submit(self, node, user, update_row=None):
        """ Insert a record for the node.

        :param node: Node to which we're adding a slot.

        :param user: User doing the adding.

        :return: List of saved slots.
        """
        _saved = []
        row = node.row_count
        for (data_key, data_value) in self.data.items():
            if data_key not in self.ext_keys:
                continue
            doc_key = self.ext_keys[data_key]
            # t = doc_key.soft_type.fetch()
            if update_row is not None:
                slot = Slot.objects(key=doc_key, row=update_row).first()
                slot.value = data_value
                slot.save()
                continue
            slot = Slot(key=doc_key, row=row, value=data_value)
            logger.debug("INSERT: saving {}".format(slot.to_json()))
            slot.save(user)
            _saved.append(slot)
        return _saved


class CreateNodeForm(Form):
    """ Form that allows users to create a new node. """

    maximum_keys = 2048

    path = HiddenField()
    title = StringField()
    description = TextAreaField()

    def create_keys_from_fields(self, user):
        """ Helper function to create node keys from fields. """
        keys = []
        for i in range(0, self.maximum_keys):
            f1 = 'key_{}_name'.format(i)
            f2 = 'key_{}_type'.format(i)
            f3 = 'key_{}_size'.format(i)
            if f1 not in self.data:
                break
            key_name = self.data[f1]
            key_size = self.data[f3]
            _key_type = self.data[f2]
            if key_name is None:
                return keys
            key_type = Type.objects(id=_key_type).first()
            key = Key(name=key_name,
                      size=key_size,
                      soft_type=key_type)
            key.save(user)
            keys.append(key)
        return keys

    def validate(self):
        for (k, v) in self.data.items():
            if isinstance(v, list):
                self.data[k] = v[0]
        return True

    def submit(self, user):
        """ Submit the form to create the node. """
        keys = self.create_keys_from_fields(user)
        node = Node(title=self.title.data, description=self.description.data,
                    keys=keys)
        node.save(user)
        return create_node_at_path(user, self.data['path'], node)


class ChangeApiKeyForm(Form):

    """ Form for the user's API Key. """

    api_key = ReadOnlyField(render_kw={'size': 70, })
