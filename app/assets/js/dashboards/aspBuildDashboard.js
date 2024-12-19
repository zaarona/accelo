let transpose = false;
// create gradient of green colors
let charts = {};

function aspBuildDashboard() {
    // destroy all charts:
    Object.keys(charts).forEach(function(key) {
        if(charts[key]){
            charts[key].destroy();
        }
    });

    let data = dataManager.data["asp-build"].data;

    let transpose = false;
    let max1 = Math.max(...Object.values(data['selection1']['asp_percentile_table']).map(function(o) { return Math.max(...Object.values(o)); }));
    let max2 = Math.max(...Object.values(data['selection2']['asp_percentile_table']).map(function(o) { return Math.max(...Object.values(o)); }));
    let maxasp = Math.max(max1, max2);
    charts['asp1'] = drawASPChart(1, Math.max(max1, max2), data);
    charts['asp2'] = drawASPChart(2, Math.max(max1, max2), data);
    
    let max3 = Math.max(...Object.values(data['selection1']['licence_quantity_percentile_table']).map(function(o) { return Math.max(...Object.values(o)); }));
    let max4 = Math.max(...Object.values(data['selection2']['licence_quantity_percentile_table']).map(function(o) { return Math.max(...Object.values(o)); }));
    let maxlicense = Math.max(max3, max4);
    charts['license1'] = drawLicenseQuantityChart(1, Math.max(max3, max4), data);
    charts['license2'] = drawLicenseQuantityChart(2, Math.max(max3, max4), data);
    
    let max5 = Math.max(...Object.values(data['selection1']['sample_size_table']));
    let max6 = Math.max(...Object.values(data['selection2']['sample_size_table']));
    
    charts['sample1'] = drawSampleSize(1,  Math.max(max5, max6), data);
    charts['sample2'] = drawSampleSize(2,  Math.max(max5, max6), data);
    
    let max7 = Math.max(...Object.values(data['selection1']['arr_filtered_table']));
    let max8 = Math.max(...Object.values(data['selection2']['arr_filtered_table']));
    
    charts['arr1'] = drawARRFiltered(1, Math.max(max7, max8), data);
    charts['arr2'] = drawARRFiltered(2, Math.max(max7, max8), data);
    
    console.log('aspBuildDashboard');
}


    // Object.keys(data['cohort_lists']).forEach(function(key) {
    //     data['cohort_lists'][key].forEach(function(value) {
    //         $('#asp_'+key.toLocaleLowerCase().replaceAll(' ','_')+'_1').append(`
    //             <option value="`+value+`">`+value+`</option>
    //         `);
    //         $('#asp_'+key.toLocaleLowerCase().replaceAll(' ','_')+'_2').append(`
    //             <option value="`+value+`">`+value+`</option>
    //         `);
    //     });
    // });


// $('#rearrange_data').click(function(){
//     transpose = !transpose;
//     charts['asp1'].destroy();
//     charts['asp2'].destroy();
//     charts['asp1'] = drawASPChart(1, maxasp);
//     charts['asp2'] = drawASPChart(2, maxasp);
//     charts['license1'].destroy();
//     charts['license2'].destroy();
//     charts['license1'] = drawLicenseQuantityChart(1, maxlicense);
//     charts['license2'] = drawLicenseQuantityChart(2, maxlicense);

// });

function getValuesOfDict(dict){
    let values = [];
    Object.keys(dict).forEach(function(key){
        values.push(dict[key]);
    });
    return values;
}

function drawASPChart(no, max, data){
    let d = data['selection'+no]['asp_percentile_table'];
    if(transpose) d = JSON.parse(JSON.stringify(transposeDict(d)));
    let labels = Object.keys(d[Object.keys(d)[0]]);
    let datasets = [];
    let greens = helpers.createColorGradient('#ffffff', '#1b645b', Object.keys(d).length);
    Object.keys(d).forEach(function(key, index){
        datasets.push({
            label: key,
            data: getValuesOfDict(d[key]),
            backgroundColor: greens[index],
            tension: 0.1
        });
    });
    let config = cc('bar', {labels: labels, datasets: datasets});
    config.options.plugins.legend.position = 'bottom';
    config.options.plugins.legend.labels = {boxWidth: 12};



    // set title:
    config.options.plugins.title = {
        display: true,
        text: 'ASP'
    };
    // set y-axis max
    config.options.scales.y.max = max;
    var asp_chartjs_1 = new Chart(document.getElementById('asp_chartjs_1'+no), config);
    return asp_chartjs_1;
}

function drawLicenseQuantityChart(no, max, data){
    let d = data['selection'+no]['licence_quantity_percentile_table'];
    if(transpose) d = JSON.parse(JSON.stringify(transposeDict(d)));
    let labels = Object.keys(d[Object.keys(d)[0]]);
    let datasets = [];
    let greens = helpers.createColorGradient('#ffffff', '#1b645b', Object.keys(d).length);
    Object.keys(d).forEach(function(key, index){
        datasets.push({
            label: key,
            data: getValuesOfDict(d[key]),
            backgroundColor: greens[index],
            tension: 0.1
        });
    });
    let config = cc('bar', {labels: labels, datasets: datasets});
    config.options.plugins.legend.position = 'bottom';
    config.options.plugins.legend.labels = {boxWidth: 12};
    // set title:
    config.options.plugins.title = {
        display: true,
        text: 'License Quantity'
    };
    // set y-axis max
    config.options.scales.y.max = max;
    var asp_chartjs_2 = new Chart(document.getElementById('asp_chartjs_2'+no), config);
    return asp_chartjs_2;
}

function drawSampleSize(no, max, data){
    let d = data['selection'+no]['sample_size_table'];
    let labels = ['Sample Size'];
    let datasets = [];
    let greens = helpers.createColorGradient('#ffffff', '#1b645b', Object.keys(d).length);
    Object.keys(d).forEach(function(key, index){
        datasets.push({
            label: key,
            data: [d[key]],
            backgroundColor: greens[index],
            tension: 0.1
        });
    });
    let config = cc('bar', {labels: labels, datasets: datasets});
    config.options.plugins.legend.position = 'bottom';
    config.options.plugins.legend.labels = {boxWidth: 12};
    // set title:
    config.options.plugins.title = {
        display: true,
        text: 'Sample Size'
    };
    // set y-axis max
    config.options.scales.y.max = max;
    var asp_chartjs_3 = new Chart(document.getElementById('asp_chartjs_3'+no), config);
    return asp_chartjs_3;
}

function drawARRFiltered(no, max, data){
    let d = data['selection'+no]['arr_filtered_table'];
    let labels = ['ARR'];
    let datasets = [];
    let greens = helpers.createColorGradient('#ffffff', '#1b645b', Object.keys(d).length);
    Object.keys(d).forEach(function(key, index){
        datasets.push({
            label: key,
            data: [d[key]],
            backgroundColor: greens[index],
            tension: 0.1
        });
    });
    let config = cc('bar', {labels: labels, datasets: datasets});
    config.options.plugins.legend.position = 'bottom';
    config.options.plugins.legend.labels = {boxWidth: 12};
    // set title:
    config.options.plugins.title = {
        display: true,
        text: 'ARR Filtered'
    };
    // set y-axis max
    config.options.scales.y.max = max;
    var asp_chartjs_4 = new Chart(document.getElementById('asp_chartjs_4'+no), config);
    return asp_chartjs_4;
}

function transposeDict(dict){
    let transposed = {};
    Object.keys(dict).forEach(function(key){
        Object.keys(dict[key]).forEach(function(subkey){
            if(!transposed[subkey]) transposed[subkey] = {};
            transposed[subkey][key] = dict[key][subkey];
        });
    });
    return transposed;
}


function cc(chart_type, data) {
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
              // if background color of dataset is dark, use white text, else use black text
              let hexString = context.dataset.backgroundColor;
              let r = parseInt(hexString.slice(1, 3), 16);
              let g = parseInt(hexString.slice(3, 5), 16);
              let b = parseInt(hexString.slice(5, 7), 16);
              let brightness = Math.sqrt(0.299 * r*r + 0.587 * g*g + 0.114 * b*b);
              if(brightness > 130){
                  return '#000000';
              } else {
                  return '#FFFFFF';
              }
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
  