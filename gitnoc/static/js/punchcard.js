// modified version of: http://gabekoss.com/blog/2014/06/creating_github_style_punchcard_graph_with_d3/

var fullWidth = document.getElementById('graph').offsetWidth;
var graphPadding = 120;
var width = (fullWidth-graphPadding);
var fullHeight = 380;
var height = (fullHeight-35);
var days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
var hours = [
  "12am", "1am", "2am", "3am", "4am", "5am", "6am", "7am", "8am",
  "9am", "10am", "11am", "12pm", "1pm", "2pm", "3pm", "4pm", "5pm",
  "6pm", "7pm", "8pm", "9pm", "10pm", "11pm"
];


var palette = d3.select("#graph").append("svg").
  attr("width", fullWidth).
  attr("height", fullHeight);

var dayGroup = palette.append("g");
var hourGroup = palette.append("g");
var circleGroup = palette.append("g");


$(document).ready(function(){
  $.getJSON('/punchcard_data', function(data){

    x = {
      min:  0,
      max:  width
    }
    x.step = x.max/24;

    y = {
      min:  0,
      max:  height
    }
    y.step = y.max/7;

  var dayText = dayGroup.selectAll("text")
                          .data(days)
                          .enter()
                          .append("text");
  var dayLabels = dayText
                   .attr("x", 0)
                   .attr("y", function(d) { return y.step*(days.indexOf(d)+1); })
                   .text(function (d) { return d; })
                   .attr("font-family", "sans-serif")
                   .attr("font-size", "12px");

  var hourText = hourGroup.selectAll("text")
                          .data(hours)
                          .enter()
                          .append("text");
  var hourLabels = hourText
                   .attr("x", function(d) {
                     return x.step*(hours.indexOf(d)+1)+32;
                   })
                   .attr("y", y.max+32)
                   .text(function (d) { return d; })
                   .attr("font-family", "sans-serif")
                   .attr("font-size", "12px");


  var scaleData = [];

  for (i in data){
    scaleData.push(data[i][2])
  }

  z = {
    data: scaleData
  }
  z.max    = d3.max(z.data)
  z.min    = d3.min(z.data)
  z.domain = [z.min, z.max]
  z.range  = [4, 15]
  z.scale  = d3.scale.linear().
  domain(z.domain).
  range(z.range);

  for (var i in data) {
    tuple = data[i];
    commits = tuple[2];
    if (commits > 0) {
      cy    = y.step*(tuple[0]+1);
      cx    = x.step*(tuple[1]+1)+50;
      r     = z.scale(commits);
      title = "Commits: " + commits;

      c = circleGroup.append("circle")
        .attr("cx",cx)
        .attr("cy",cy)
        .attr("r",r)
        .attr("title",title)
        .attr("class","hover-circle");

      }
    }

  })
});