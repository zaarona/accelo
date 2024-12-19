function paretoAnalysisDashboard() {
  let data = dataManager.data["pareto-analysis"];
  let arr_dist_table = data["arr_dist_table"];
  let pareto_analysis = data["pareto_analysis"];
  let pareto_analysis_chartjs = data["pareto_analysis_chartjs"];
  let breakdown_list = data["breakdown_list"];
  let filter_values = data["filter_values"];

  let columnDefs = pareto_analysis["columnDefs"];
  let rowData = pareto_analysis["rowData"];
  let pinnedBottomRowData = pareto_analysis["pinnedBottomRowData"];

  let gridOptions = gridManager.getGridOptions(columnDefs, rowData);
  gridOptions.pinnedBottomRowData = pinnedBottomRowData;
  // add formatters for the columns
  gridOptions.theme = gridManager.getTheme();
  gridOptions.tooltipShowDelay = 100;
  gridOptions.tooltipHideDelay = 5000;
  // auto size columns
  gridOptions.autoSizeStrategy = {
    type: "fitGridWidth",
    defaultMinWidth: 80,
  };

  // create grid with pareto_analysis
  let pareto_analysis_grid = new agGrid.createGrid(
    document.getElementById("pareto-analysis-grid"),
    gridOptions
  );

  // create grid with arr_dist_table
  var arr = [];
  data["arr_dist_table"]["rowData"].forEach(function (row) {
    arr.push(row["peraccountdata"]);
  });
  let scaledColorList = [];
  data["arr_dist_table"]["columnDefs"][3]["cellStyle"] = function (params) {
    let backgroundColor = helpers.scaledColor(
      arr[params.rowIndex],
      arr,
      "#ffffff",
      "#1b645b"
    );
    let textColor = helpers.getTextColorBasedOnBackground(backgroundColor);
    scaledColorList.push(backgroundColor);
    return { color: textColor, backgroundColor: backgroundColor };
  };

  columnDefs = arr_dist_table["columnDefs"];
  rowData = arr_dist_table["rowData"];
  gridOptions = gridManager.getGridOptions(columnDefs, rowData);
  gridOptions.theme = gridManager.getTheme();
  gridOptions.tooltipShowDelay = 100;
  gridOptions.tooltipHideDelay = 5000;
  gridOptions.autoSizeStrategy = {
    type: "fitGridWidth",
    defaultMinWidth: 80,
  };
  let arr_dist_table_grid = new agGrid.createGrid(
    document.getElementById("pareto-analysis-dist-grid"),
    gridOptions
  );

  let config = chart_config("line", data["pareto_analysis_chartjs"]);
  config.options.plugins.annotation = {
    annotations: {
      // line1: {
      //     type: 'line',
      //     yMin: 0,
      //     yMax: 100,
      //     xMin: 10,
      //     xMax: 10,
      //     borderColor: 'rgb(0, 0, 0)',
      //     borderWidth: 2,
      // },
      // label1: {
      //     type: 'label',
      //     xValue: 10,
      //     yValue: Math.round(data['pareto_analysis_chartjs']['datasets'][1]['data'][9]),
      //     backgroundColor: 'rgb(255, 255, 255)',
      //     textAlign: 'left',
      //     position: 'start',
      //     fontSize: 12,
      //     content: 'Top 10 of Customers contribute '+ Math.round(data['pareto_analysis_chartjs']['datasets'][1]['data'][9])+'% of Revenue',
      //     enabled: true,
      // },
      // line2: {
      //     type: 'line',
      //     yMin: 0,
      //     yMax: 100,
      //     xMin: index,
      //     xMax: index,
      //     borderColor: 'rgb(0, 0, 0)',
      //     borderWidth: 2,
      // },
      // label2: {
      //     type: 'label',
      //     xValue: 10,
      //     yValue: Math.round(data['pareto_analysis_chartjs']['datasets'][1]['data'][index]),
      //     backgroundColor: 'rgb(255, 255, 255)',
      //     textAlign: 'left',
      //     position: 'start',
      //     fontSize: 12,
      //     content: 'Top ' + index + ' of Customers contribute 50% of Revenue',
      //     enabled: true,
      // }
    },
  };
  config.options.scales.y.min = 0;
  config.options.scales.y.max = 103;
  // set legend false:
  config.options.plugins.legend = {
    display: true,
  };
  // show only max tick on y-axis
  config.options.scales.y.ticks = {
    callback: function (value, index, values) {
      if (value != 103) return value + "%";
      else return "100%";
    },
  };

  let xticks = [];
  data["arr_dist_table"]["rowData"].forEach(function (row) {
    xticks.push(row["# of Accounts"]);
  });
  console.log(xticks);

  config.options.scales.x.ticks = {
    stepSize: 1,
    callback: function (value, index, values) {
      if (xticks.includes(index)) {
        return ["Top 10", "Top 10%", "Top 20%", "Top 50%", "Top 75%"][
          xticks.indexOf(index)
        ];
      } else return null;
    },
  };
  // set background color of datasets
  scaledColorList.push("#FFFFFF");
  config.data.datasets.forEach(function (dataset, index) {
    dataset.backgroundColor = scaledColorList[index++ % scaledColorList.length];
  });
  let greens = helpers.createColorGradient('#ffffff', '#1b645b', 6);
  config.data.datasets.forEach(function (dataset, index) {
    dataset.backgroundColor = greens[index];
  });

  var pareto_analysis_chart = new Chart(
    document.getElementById("pareto-analysis-chart"),
    config
  );
}

function chart_config(chart_type, data) {
  let activeTab = "tab_pareto_analysis";
  let stacked = false;
  let legend = true;
  let datalabels_display = "auto";
  let tooltip = true;
  datalabels_display = false;
  tooltip = false;
  let config = {
    type: chart_type,
    data: data,
    options: {
      plugins: {
        tooltip: {
          enabled: tooltip,
        },
        legend: {
          display: legend,
          labels: {
            font: {
              size: 10,
            },
            boxWidth: 10,
          },
        },
        datalabels: {
          display: datalabels_display,
          formatter: function (value, context) {
            return helpers.beautifyValue(value);
          },
          color: function (context) {
            return darkenColor(context.dataset.backgroundColor, 60);
          },
          labels: {
            title: {
              font: {
                size: 10,
              },
            },
          },
        },
      },
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          stacked: stacked,
          grid: {
            display: false,
          },
          ticks: {
            callback: function (value, index, values) {
              return helpers.beautifyValue(value, 1);
            },
          },
        },
        x: {
          stacked: stacked,
          grid: {
            display: false,
          },
        },
      },
    },
  };
  return config;
}
