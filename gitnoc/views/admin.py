"""
.. module::
    :platform: Unix, Linux, Windows
    :synopsis:

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com.com>

"""

from gitnoc.services import settings as settings_services
from gitnoc.forms.public import SettingsForm, ProfileForm, CreateProfileForm
from gitnoc.utils import render_wrapper
from flask import Blueprint, request, redirect, url_for

__author__ = 'willmcginnis'

blueprint = Blueprint('admin', __name__, static_folder="../static")


@blueprint.route('/settings', methods=["GET", "POST"])
def settings():
    form = SettingsForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        settings_services.update_profile(form.project_directory.data, form.extensions.data, form.ignore_dir.data)

    settings = settings_services.get_settings()
    extensions = settings.get('extensions', None)
    project_dir = settings.get('project_dir', None)
    ignore_dir = settings.get('ignore_dir', None)

    if project_dir is not None:
        if isinstance(project_dir, list):
            pdv = ','.join(project_dir)
        else:
            pdv = project_dir
    else:
        pdv = ''

    if extensions is not None:
        if isinstance(project_dir, list):
            ext = ','.join(extensions)
        else:
            ext = extensions
    else:
        ext = ''

    if ignore_dir is not None:
        if isinstance(project_dir, list):
            ign = ','.join(ignore_dir)
        else:
            ign = ignore_dir
    else:
        ign = ''

    return render_wrapper('public/settings.html', form=form, project_directory_values=pdv, ignore_dir_values=ign, extensions_values=ext)


@blueprint.route('/profile', methods=["GET", "POST"])
def profile():
    select_form = ProfileForm(request.form)
    create_form = CreateProfileForm(request.form)

    select_form.profile.choices = settings_services.get_profiles()

    if select_form.validate_on_submit():
        settings_services.change_profile(select_form.profile.data)
        return redirect(url_for('admin.settings'))
    elif create_form.validate_on_submit():
        settings_services.create_profile(create_form.name.data)
        settings_services.change_profile(create_form.name.data)
        return redirect(url_for('admin.settings'))

    select_form.profile.choices = settings_services.get_profiles()
    select_form.profile.default = settings_services.get_settings()['profile_name']
    select_form.process()

    return render_wrapper('public/profile.html', create_form=create_form, select_form=select_form)


def redirect_url(default='index'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)


@blueprint.route('/ignore_file/<file_name>/', methods=["GET", "POST"])
def ignore_file(file_name):
    settings_services.ignore_file(file_name)
    return redirect(redirect_url())
