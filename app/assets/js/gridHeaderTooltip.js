
class gridHeaderTooltip {
    init(params) {
      this.eGui = document.createElement('div');
      // add class
      this.eGui.classList.add('custom-tooltip');
      const colName = params.colDef.field;
      // get data from aggrid (if filtered, get filtered data)
      let tableData = [];
      params.api.forEachNodeAfterFilter(node => {
        tableData.push(node.data);
      });
      const columnData = tableData.map(row => row[colName]);
      // if numbers are more than 70 percent excluding empty values, use echarts
      const numbericValues = columnData.map(v => parseFloat(v)).filter(v => !isNaN(v) && v !== null && v !== '');
      const isNumeric = numbericValues.length > columnData.length * 0.7;
      let content = '';
      
      if (isNumeric) {
        // For numeric columns
        const numbers = columnData.map(v => parseFloat(v)).filter(v => !isNaN(v));
        const stats = {
          min: Math.min(...numbers),
          max: Math.max(...numbers),
          avg: numbers.reduce((a, b) => a + b, 0) / numbers.length,
          sum: numbers.reduce((a, b) => a + b, 0),
          count: numbers.length
        };
  
        // Create container for ECharts
        const chartContainer = document.createElement('div');
        chartContainer.style.width = '400px';
        chartContainer.style.height = '250px';
        this.eGui.appendChild(chartContainer);
  
        // Calculate histogram data
        const bins = 20;  // Number of bins
        const binWidth = (stats.max - stats.min) / bins;
        const histogramData = new Array(bins).fill(0);
        const binRanges = [];
  
        numbers.forEach(num => {
          const binIndex = Math.min(Math.floor((num - stats.min) / binWidth), bins - 1);
          histogramData[binIndex]++;
        });
  
        // Create bin ranges for x-axis
        for (let i = 0; i < bins; i++) {
          const start = stats.min + (i * binWidth);
          const end = start + binWidth;
          binRanges.push(`${helpers.beautifyValue(start)}-${helpers.beautifyValue(end)}`);
        }
  
        // Initialize ECharts
        const chart = echarts.init(chartContainer);
        const option = {
          grid: {
              left: '40px',
              right: '10%',
              top: '10%',
              bottom: '15%'
          },
          title: {
              show: false
          },
          tooltip: {
            trigger: 'item',
            formatter: function(params) {
              const binStart = stats.min + (params.dataIndex * binWidth);
              const binEnd = binStart + binWidth;
              return `Range: ${helpers.beautifyValue(binStart)} - ${helpers.beautifyValue(binEnd)}<br/>
                      Count: ${params.value}`;
            }
          },
          xAxis: {
            type: 'category',
            data: binRanges,
            axisLabel: {
              rotate: 90,
              fontSize: 10,
              formatter: function(value) {
                return value.slice(0, 10);
              }
            }
          },
          yAxis: {
            type: 'value',
            axisLabel: {
              formatter: function(value) {
                return helpers.beautifyValue(value);
              }
            }
          },
          series: [{
            data: histogramData,
            type: 'bar',
            itemStyle: {
              color: '#1B645B'
            },
            barWidth: '90%'
          }]
        };
  
        chart.setOption(option);
        // Add statistics below the chart
        const statsDiv = document.createElement('div');
        statsDiv.innerHTML = `
          <div style="margin-top: 10px; padding: 10px; background: #f5f5f5; border-radius: 4px;">
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;">
              <div style="font-size: 12px;">
                <strong>Min:</strong> ${helpers.beautifyValue(stats.min)}
              </div>
              <div style="font-size: 12px;">
                <strong>Max:</strong> ${helpers.beautifyValue(stats.max)}
              </div>
              <div style="font-size: 12px;">
                <strong>Average:</strong> ${helpers.beautifyValue(stats.avg)}
              </div>
              <div style="font-size: 12px;">
                <strong>Count:</strong> ${stats.count}
              </div>
              <div style="font-size: 12px; grid-column: span 2;">
                <strong>Sum:</strong> ${helpers.beautifyValue(stats.sum)}
              </div>
            </div>
          </div>
        `;
        this.eGui.appendChild(statsDiv);
  
      } else {
        // For string columns
        const valueCounts = {};
        columnData.forEach(val => {
          valueCounts[val] = (valueCounts[val] || 0) + 1;
        });
  
        const sortedCounts = Object.entries(valueCounts)
          .sort(([,a], [,b]) => b - a)
          .slice(0, 5);
  
        const maxCount = Math.max(...sortedCounts.map(([,count]) => count));
        
        const barsHtml = sortedCounts
          .map(([value, count]) => {
            const width = (count / maxCount) * 100;
            return `
              <div class="custom-tooltip-bars" style="margin-bottom: 5px; background-color: #1B645B10;">
                <div style="display: flex; align-items: center;">
                  <div style="width: 100px; overflow: hidden; text-overflow: ellipsis; font-size: 12px; font-weight: 600;">${helpers.beautifyValue(value)}</div>
                  <div style="flex-grow: 1;">
                    <div style="background: #1B645B; height: 15px; width: ${width}%"></div>
                  </div>
                  <div style="margin-left: 5px; font-size: 12px; font-weight: 600;">${count}</div>
                </div>
              </div>
            `;
          })
          .join('');
  
        content = `
          <div style="font-size: 12px;">
            <div style="margin-bottom: 10px; font-weight: 600; text-align: center; color: #1b645b;">Top 5 Values:</div>
            ${barsHtml}
            <div style="margin-top: 10px;">
              <div class="custom-tooltip-row">
                <div class="custom-tooltip-value-label">Unique Values:</div> 
                <div class="custom-tooltip-value-value">${Object.keys(valueCounts).length}</div>
              </div>
              <div class="custom-tooltip-row">
                <div class="custom-tooltip-value-label">Total Count:</div> 
                <div class="custom-tooltip-value-value">${columnData.length}</div>
              </div>
            </div>
          </div>
        `;
        this.eGui.innerHTML = content;
      }
    }
  
    getGui() {
      return this.eGui;
    }
  }
  