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

from onebase_api.models.main import (
    create_node_at_path,
    Key,
    Type,
    Node,
    Path,
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
            key_name = getattr(self, f1)
            _key_type = getattr(self, f2)
            if key_name is None:
                return keys
            key_type = Type.objects(name=_key_type.data).first()
            key_name = key_name.data
            key = Key(name=key_name.data,
                      type=key_type)
            key.save(user)
            keys.append(key)
        return keys

    def submit(self, user):
        """ Submit the form to create the node. """
        keys = self.create_keys_from_fields(user)
        node = Node(title=self.title.data, description=self.description.data,
                    keys=keys)
        node.save(user)
        return create_node_at_path(user, self.path, node)
