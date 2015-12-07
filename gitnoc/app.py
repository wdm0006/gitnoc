from flask import Flask, render_template
import json
from gitpandas import ProjectDirectory

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

# use list for explicit declaration or string with directory of repos for implicit
project_dir = ['../../git-pandas', '../../stravalib']

app = Flask(__name__)


@app.route('/', methods=["GET"])
def index():
    return render_template('index.html', title=TITLE, base_scripts=scripts, css=css)


@app.route('/cumulative_author_blame', methods=['GET', 'POST'])
def cumulative_author_blame():
    # TODO: just write these to a static json file with a refresh button
    repo = ProjectDirectory(working_dir=project_dir)
    cb = repo.cumulative_blame(extensions=['py'])
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
    return json.dumps(d3_data)


@app.route('/cumulative_project_blame', methods=['GET', 'POST'])
def cumulative_project_blame():
    # TODO: just write these to a static json file with a refresh button
    repo = ProjectDirectory(working_dir=project_dir)
    cb = repo.cumulative_blame(extensions=['py'], by='project')
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
    return json.dumps(d3_data)

if __name__ == "__main__":
    app.run(debug=True)
