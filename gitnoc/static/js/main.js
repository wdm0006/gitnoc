var cumulative_author_blame = function (cab_data) {
  nv.addGraph(function() {
    var cab_chart = nv.models.stackedAreaChart()
                      .margin({right: 0})
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
  nv.addGraph(function() {
    var cpb_chart = nv.models.stackedAreaChart()
                      .margin({right: 0})
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

d3.json("/cumulative_author_blame", cumulative_author_blame);
d3.json("/cumulative_project_blame", cumulative_project_blame);

