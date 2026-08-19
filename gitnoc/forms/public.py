from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired

from gitnoc.services.settings import parse_project_dir

__author__ = 'willmcginnis'


class ProfileForm(FlaskForm):
    profile = SelectField('Profile')

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)


class CreateProfileForm(FlaskForm):
    name = StringField('Profile Name')

    def __init__(self, *args, **kwargs):
        super(CreateProfileForm, self).__init__(*args, **kwargs)


class SettingsForm(FlaskForm):
    project_directory = StringField('Project Directory (absolute path)', validators=[DataRequired()])
    extensions = StringField('Extensions to Report On')
    ignore_dir = StringField('Directories to Ignore')
    branch = StringField('Branch to Analyze')

    def __init__(self, *args, **kwargs):
        super(SettingsForm, self).__init__(*args, **kwargs)

    def validate(self, extra_validators=None):
        initial_validation = super(SettingsForm, self).validate(extra_validators=extra_validators)
        if not initial_validation:
            return False

        self.project_directory.data = parse_project_dir(self.project_directory.data)

        if self.extensions.data is not None:
            self.extensions.data = [str(x).strip() for x in self.extensions.data.split(',')]
            if self.extensions.data == ['']:
                self.extensions.data = None

        if self.ignore_dir.data is not None:
            self.ignore_dir.data = [str(x).strip() for x in self.ignore_dir.data.split(',')]
            if self.ignore_dir.data == ['']:
                self.ignore_dir.data = None

        self.branch.data = (self.branch.data or '').strip() or 'master'

        return True
