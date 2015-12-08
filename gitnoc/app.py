from flask import Flask, render_template, redirect, url_for, request
import json
import os
from gitpandas import ProjectDirectory
from gitnoc.forms.public import SettingsForm

TITLE = "GitNOC"

scripts = [
    "./js/queue.js",
    "./bower_components/jquery/dist/jquery.min.js",
    "./bower_components/d3/d3.min.js",
    "./bower_components/nvd3/build/nv.d3.min.js",
    "./js/main.js",
]

css = [
    "./bower_components/bootstrap/dist/css/bootstrap.min.css",
    "./bower_components/nvd3/build/nv.d3.min.css",
    "./css/main.css"
]

app = Flask(__name__)
app.secret_key = 'CHANGEME'


def get_settings():
    try:
        return json.load(open('settings.json', 'r'))
    except:
        return {}


@app.route('/', methods=["GET"])
def index():
    return render_template('index.html', title=TITLE, base_scripts=scripts, css=css)


@app.route('/settings', methods=["GET", "POST"])
def settings():
    form = SettingsForm(request.form)
    if form.validate_on_submit():
        settings = get_settings()
        settings.update({
            'ignore_dir': form.ignore_dir.data,
            'project_dir': form.project_directory.data,
            'extensions': form.extensions.data
        })
        json.dump(settings, open('settings.json', 'w'))

    settings = get_settings()
    extensions = settings.get('extensions', None)
    if extensions is not None:
        form.extensions.default = ', '.join(extensions)

    project_dir = settings.get('project_dir', None)
    if project_dir is not None:
        if isinstance(project_dir, list):
            form.project_directory.default = ', '.join(project_dir)
        else:
            form.project_directory.default = project_dir

    ignore_dir = settings.get('ignore_dir', None)
    if ignore_dir is not None:
        form.ignore_dir.default = ', '.join(ignore_dir)

    form.process()

    return render_template('settings.html', form=form, title=TITLE, base_scripts=scripts, css=css)


@app.route('/cumulative_author_blame', methods=['GET', 'POST'])
def cumulative_author_blame():
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    extensions = settings.get('extensions', None)
    ignore_dir = settings.get('ignore_dir', None)

    repo = ProjectDirectory(working_dir=project_dir)
    cb = repo.cumulative_blame(extensions=extensions, ignore_dir=ignore_dir)
    cb = cb[~cb.index.duplicated()]
    t = json.loads(cb.to_json(orient='columns'))

    d3_data = []
    for committer in t.keys():
        blob = dict()
        blob['key'] = committer
        blob['values'] = []
        for data_point in t[committer].keys():
            blob['values'].append([int(float(data_point)), t[committer][data_point]])
            blob['values'] = sorted(blob['values'], key=lambda x: x[0])
        d3_data.append(blob)

    # dump the data to disk
    filename = 'cumulative_author_blame.json'
    json.dump(d3_data, open(str(os.path.dirname(os.path.abspath(__file__))) + os.sep + 'static' + os.sep + 'data' + os.sep + filename, 'w'))
    return redirect(url_for('index'))


@app.route('/cumulative_project_blame', methods=['GET', 'POST'])
def cumulative_project_blame():
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    extensions = settings.get('extensions', None)
    ignore_dir = settings.get('ignore_dir', None)

    repo = ProjectDirectory(working_dir=project_dir)
    cb = repo.cumulative_blame(extensions=extensions, ignore_dir=ignore_dir, by='project')
    cb = cb[~cb.index.duplicated()]
    t = json.loads(cb.to_json(orient='columns'))

    d3_data = []
    for committer in t.keys():
        blob = dict()
        blob['key'] = committer
        blob['values'] = []
        for data_point in t[committer].keys():
            blob['values'].append([int(float(data_point)), t[committer][data_point]])
            blob['values'] = sorted(blob['values'], key=lambda x: x[0])
        d3_data.append(blob)

    # dump the data to disk
    filename = 'cumulative_project_blame.json'
    json.dump(d3_data, open(str(os.path.dirname(os.path.abspath(__file__))) + os.sep + 'static' + os.sep + 'data' + os.sep + filename, 'w'))
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
