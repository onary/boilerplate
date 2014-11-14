# -*- coding: utf-8 -*-
import logging
from apps.core.forms import ModelForm, Form
from wtforms import StringField, PasswordField, BooleanField, validators
from wtforms.validators import ValidationError
from .models import UserModel

l = logging.getLogger(__name__)


class RegistrationForm(ModelForm):
    first_name = StringField('First Name')
    last_name = StringField('Last Name')
    email = StringField('Email Address', [validators.InputRequired(),
                                          validators.Email()])
    password = PasswordField('Password', [validators.InputRequired()])
    password_confirmation = PasswordField('Repeat password',
                                          [validators.InputRequired()])
    t_and_c = BooleanField('Terms and Conditions', default=False)

    _model = UserModel
    text_errors = {
        "password_mismatch": "Password mismatch",
        "email_occupied": "Already taken. Sorry.",
    }

    def validate_password_confirmation(self, field):
        if self.password.data != field.data:
            raise ValidationError(self.text_errors['password_mismatch'])


class LoginForm(Form):
    email = StringField('Email Address', [validators.InputRequired(),
                                          validators.Email()])
    password = PasswordField('Password', [validators.InputRequired()])

    text_errors = {
        'not_found': "Email and password mismatch",
        'wrong_password': "Email and password mismatch",
    }
