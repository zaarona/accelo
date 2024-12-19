let myChart;
function clusteringDashboard(){
      let chartDom = document.getElementById('clustering-chart');
      if(myChart){
        myChart.dispose();
      }
      myChart = echarts.init(chartDom); 
      let options = dataManager.data.clustering.data.options;


      options.grid = {
        'left': '3%',
        'right': '7%',
        'bottom': '7%',
        'containLabel': true
      }
      options.tooltip = {
        'trigger': 'axis',
        'showDelay': 0,
        'axisPointer': {
            'show': true,
            'type': 'cross',
            'lineStyle': {
                'type': 'dashed',
                'width': 1
            }
        }
    }   
    options.toolbox = {
            'type': 'dashed',
            'width': 1
    }
    options.toolbox.feature = {
        'dataZoom': {},
        'brush': {
            'type': ['rect', 'polygon', 'clear']
        }
    }
    options.brush = {
        'type': ['rect', 'polygon', 'clear']
    }
    options.xAxis = [
        {
            'type': 'value',
            'scale': true,
            'splitLine': {
                'show': false
            }
        }
    ]
    options.yAxis = [
        {
            'type': 'value',
            'scale': true,
            'splitLine': {
                'show': false
            }
        }
    ]

    options.xAxis[0].axisLabel = {
        formatter: function(value){
          return helpers.beautifyValue(value, 0);
        }
      }
      options.yAxis[0].axisLabel = {
        formatter: function(value){
          return helpers.beautifyValue(value, 0);
        }
      }
      let greens = helpers.createColorGradient('#ffffff', '#1b645b', options.series.length);
      options.series.forEach(function(series, i){
//        series.color = greens[i];
        series.markLine.label = {
          formatter: function(value){
            let v = value.data.coord[0];
            if(v == -Infinity){
                v = value.data.coord[1];
            }
            return helpers.beautifyValue(v, 1);
          }
        }
        // series.markPoint.label = {
        //   formatter: function(value){
        //     return helpers.beautifyValue(value.data.coord[0], 1);
        //   }
        // }
      });

      myChart.setOption(options);
}