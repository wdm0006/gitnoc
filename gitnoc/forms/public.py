from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired

__author__ = 'willmcginnis'


class SettingsForm(Form):
    project_directory = StringField('Project Directory (absolute path)', validators=[DataRequired()])
    extensions = StringField('Extensions to Report On')
    ignore_dir = StringField('Directories to Ignore')

    def __init__(self, *args, **kwargs):
        super(SettingsForm, self).__init__(*args, **kwargs)

    def validate(self):
        initial_validation = super(SettingsForm, self).validate()
        if not initial_validation:
            return False

        self.project_directory.data = [str(x).strip() for x in self.project_directory.data.split(',')]
        if len(self.project_directory.data) == 1:
            self.project_directory.data = self.project_directory.data[0]

        if self.extensions.data is not None:
            self.extensions.data = [str(x).strip() for x in self.extensions.data.split(',')]

        if self.ignore_dir.data is not None:
            self.ignore_dir.data = [str(x).strip() for x in self.ignore_dir.data.split(',')]

        return True
