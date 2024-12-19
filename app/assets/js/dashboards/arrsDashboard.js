function arrsDashboard() {
  let data = dataManager.data["arrs"];
  // create a grid with arr_dist_table
  let columnDefs = data["arrs"]["columnDefs"];
  let rowData = data["arrs"]["rowData"];
  let pinnedBottomRowData = data["arrs"]["pinnedBottomRowData"];
  let heatmap_arr = data['arrs']['arrs_heatarr'];
  data['arrs']['columnDefs'][2]['children'].forEach(function(column) {
      column.cellStyle = function(params) {
          if(data['arrs']['cohort_list'].includes(params.data[data['arrs']['cohort_column']])){
              let backgroundColor = helpers.scaledColor(params.value, heatmap_arr, '#ffffff', '#1b645b');
              return {color: helpers.getTextColorBasedOnBackground(backgroundColor), backgroundColor: backgroundColor};
          }
      },
      column.valueFormatter = function(params) {
          if(data['arrs']['cohort_list'].includes(params.data[data['arrs']['cohort_column']])){
              return helpers.beautifyValue(params.value);
          }
      }
  });
  
  data['arrs']['columnDefs'][1].valueFormatter = function(params) {
      if(data['arrs']['cohort_list'].includes(params.data[data['arrs']['cohort_column']])){
          return helpers.beautifyValue(params.value);
      }
  }

  let gridOptions = gridManager.getGridOptions(columnDefs, rowData);
  gridOptions.pinnedBottomRowData = pinnedBottomRowData;
  // add formatters for the columns
  gridOptions.theme = gridManager.getTheme();
  gridOptions.tooltipShowDelay = 100;
  gridOptions.tooltipHideDelay = 5000;

  dashboardManager.arrs.grid = agGrid.createGrid(
    document.getElementById("arrs-grid"),
    gridOptions
  );


  // arrs_chartjs
  let labels = data['arrs_chartjs']['labels'];
  let datasets = data['arrs_chartjs']['datasets'];
  let greenColors = helpers.createColorGradient('#ffffff', '#1b645b', datasets.length);
  // create echarts chart, this will be a stacked bar chart
  let chart = echarts.init(document.getElementById('arrs-chart'));
  let series = [];
  for(let i = 0; i < datasets.length; i++){
    series.push({
      name: datasets[i]['label'],
      type: 'bar',
      stack: 'arrs',
      emphasis: {
        focus: 'series'
      },
      color: greenColors[i % greenColors.length],
      data: datasets[i]['data']
    });
  }
  let option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: function(params) {
        let tooltip = params[0].axisValue + '<br/><br/>';  // x-axis label
        let total = 0;
        params.forEach(param => {
          total += param.value;
          tooltip += `<span>${param.marker} ${param.seriesName}: ${helpers.beautifyValue(param.value)}</span><br/>`;
        });
        
        // Add total at the bottom
        tooltip += `<br/><strong>Total: ${helpers.beautifyValue(total)}</strong>`;
        return tooltip;
      }
    },
    legend: {
        show: false
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: [
      {
        type: 'category',
        data: labels
      }
    ],
    yAxis: [
      {
        type: 'value',
        axisLabel: {
          formatter: function(value) {
            return helpers.beautifyValue(value);
          }
        }
      }
    ],
    series: series
  };
  chart.setOption(option);
}
