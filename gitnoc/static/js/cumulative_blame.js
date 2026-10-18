var toggle_empty_hint = function (hint_id, data) {
  var empty = !data || (Array.isArray(data) ? data.length === 0 : Object.keys(data).length === 0);
  document.getElementById(hint_id).style.display = empty ? 'block' : 'none';
  return empty;
};

var cumulative_author_blame = function (cab_data) {
  if (toggle_empty_hint('empty_cumulative_author_blame', cab_data)) { return; }
  nv.addGraph(function() {
    var cab_chart = nv.models.stackedAreaChart()
                      .margin({right: 100})
                      .x(function(d) { return d[0] })
                      .y(function(d) { return d[1] })
                      .useInteractiveGuideline(true)
                      .rightAlignYAxis(true)
                      .showControls(true)
                      .clipEdge(true);
    cab_chart.xAxis
        .tickFormat(function(d) {
          return d3.time.format('%x')(new Date(d))
    });
    d3.select('#chart_cumulative_author_blame svg')
      .datum(cab_data)
      .call(cab_chart);
    nv.utils.windowResize(cab_chart.update);
    return cab_chart;
  });
};

var cumulative_project_blame = function (cpb_data) {
  if (toggle_empty_hint('empty_cumulative_project_blame', cpb_data)) { return; }
  nv.addGraph(function() {
    var cpb_chart = nv.models.stackedAreaChart()
                      .margin({right: 100})
                      .x(function(d) { return d[0] })
                      .y(function(d) { return d[1] })
                      .useInteractiveGuideline(true)
                      .rightAlignYAxis(true)
                      .showControls(true)
                      .clipEdge(true);
    cpb_chart.xAxis
        .tickFormat(function(d) {
          return d3.time.format('%x')(new Date(d))
    });
    d3.select('#chart_cumulative_project_blame svg')
      .datum(cpb_data)
      .call(cpb_chart);
    nv.utils.windowResize(cpb_chart.update);
    return cpb_chart;
  });
};

d3.json("/cumulative_author_blame_data", cumulative_author_blame);
d3.json("/cumulative_project_blame_data", cumulative_project_blame);

