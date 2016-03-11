from flask_assets import Bundle, Environment

css = Bundle(
    "./bower_components/bootstrap/dist/css/bootstrap.min.css",
    "./bower_components/nvd3/build/nv.d3.min.css",
    "./bower_components/datatables/media/css/jquery.dataTables.min.css",
    "./bower_components/datatables-buttons/css/buttons.dataTables.scss",
    "./css/main.css",
    filters="cssmin",
    output="public/css/common.css"
)

js = Bundle(
    "./js/queue.js",
    "./bower_components/jquery/dist/jquery.min.js",
    "./bower_components/bootstrap/dist/js/bootstrap.min.js",
    "./bower_components/d3/d3.min.js",
    "./bower_components/nvd3/build/nv.d3.min.js",
    "./bower_components/datatables/media/js/jquery.dataTables.min.js",
    "./bower_components/datatables-buttons/js/dataTables.buttons.js",
    filters='jsmin',
    output="public/js/common.js"
)

cumulative_blame_js = Bundle(
    "./js/cumulative_blame.js",
    filters='jsmin',
    output="public/js/cumulativeblame.js"
)

metrics_js = Bundle(
    "./js/punchcard.js",
    filters='jsmin',
    output="public/js/metrics.js"
)
assets = Environment()

assets.register("js_all", js)
assets.register("cumulative_blame_js", cumulative_blame_js)
assets.register("metrics_js", metrics_js)
assets.register("css_all", css)
