function upSellDashboard() {
    $("#xs-quant-sheet").addClass("hidden");
    $("#up-sell").removeClass("hidden");
    let data = dataManager.data["up-sell"].data;
    // get current industry, geo, and segment
    const industry = $("#industry").val();
    const geo = $("#region").val();
    const segment = $("#segment").val();
  
    $("#industry, #region, #segment").empty();
    data["common_industry_list"].forEach((industry) => {
      $("#industry").append(`<option value="${industry}">${industry}</option>`);
    });
    data["common_geo_list"].forEach((geo) => {
      $("#region").append(`<option value="${geo}">${geo}</option>`);
    });
    data["segment_list"].forEach((segment) => {
      $("#segment").append(`<option value="${segment}">${segment}</option>`);
    });
    $("#industry, #region, #segment").off("change");
    $("#industry").val(industry);
    $("#region").val(geo);
    $("#segment").val(segment);
    $("#industry, #region, #segment").trigger("chosen:updated");
    $("#industry, #region, #segment").change((e) => {
      dataManager.updateCrossSellData();
    });
  
    data["grid"].theme = gridManager.getTheme();
    data["grid"].tooltipShowDelay = 100;
    data["grid"].tooltipHideDelay = 5000;
    data["grid"].columnDefs.forEach((col) => {
      if (col.children) {
        col.children.forEach((child) => {
          child.headerTooltip = true;
          child.tooltipComponent = gridHeaderTooltip;
        });
      } else {
        col.headerTooltip = true;
        col.tooltipComponent = gridHeaderTooltip;
      }
    });
    // destroy the existing grid if it exists
    if (dashboardManager.upSellDashboard.grid) {
      dashboardManager.upSellDashboard.grid.destroy();
    }
    dashboardManager.upSellDashboard.grid = agGrid.createGrid(
      $(`#up-sell-grid`).get(0),
      data["grid"]
    );
  
    // get the heatmap data as ag-grid data
    let heatmapData = data["opportunity_heatmap"];
    // convert ag-grid data to echarts data
    let columns = heatmapData["columnDefs"].map((col) => col.field);
    let rows = heatmapData["rowData"].map((row) => row[columns[0]]);
    // remove the first column from the columns array
    let seriesData = [];
    heatmapData["rowData"].forEach((row) => {
      Object.keys(row).forEach((key) => {
        if (key !== columns[0]) {
          seriesData.push([
            columns.indexOf(key) - 1,
            rows.indexOf(row[columns[0]]),
            row[key],
          ]);
        }
      });
    });
    columns = columns.slice(1);
    let maxColumnIndex = Math.max(...seriesData.map((item) => item[0]));
    let maxRowIndex = Math.max(...seriesData.map((item) => item[1]));
    let minColumnValue = Math.min(
      ...seriesData
        .filter((item) => item[0] !== maxColumnIndex && item[1] !== maxRowIndex)
        .map((item) => item[2])
    );
    let maxColumnValue = Math.max(
      ...seriesData
        .filter((item) => item[0] !== maxColumnIndex && item[1] !== maxRowIndex)
        .map((item) => item[2])
    );
    // create a color set from white to 1b645b
    let colorSet = Array.from(
      { length: 100 },
      (_, i) => `rgba(27, 100, 91, ${i / 100})`
    );
    // destroy the existing heatmap if it exists
    if (dashboardManager.upSellDashboard.heatmap) {
      dashboardManager.upSellDashboard.heatmap.dispose();
    }
    dashboardManager.upSellDashboard.heatmap = echarts.init(
      document.getElementById("up-sell-heatmap-chart")
    );
    let options = {
      textStyle: {
        fontFamily: "Barlow, sans-serif", // Replace with your desired font
      },
      title: {
        text: "Opportunity Heatmap",
        left: "center", // Center-align the title horizontally
        top: "10px",
        textStyle: {
          fontFamily: "Barlow, sans-serif",
          fontSize: 14,
          fontWeight: "bold",
          color: "#1b645b",
        },
      },
      graphic: [],
      tooltip: {
        position: "top",
        padding: 0,
        borderRadius: 5,
        backgroundColor: "rgba(0, 0, 0, 0)",
        margin: 0,
        border: 0,
        formatter: function (params) {
          const value = params.value[2];
          const formattedValue = helpers.beautifyNumber(value, 0);
          const row = rows[params.value[1]];
          const column = columns[params.value[0]];
          return `<div class="echarts-tooltip" style="background-color: #1b645b; color: white;">
                              <div style="font-size: 13px;">${row} - ${column}</div>
                              <div style="font-size: 16px;">${formattedValue}</div>
                          </div>`;
        },
        textStyle: {
          fontFamily: "Barlow, sans-serif",
          fontSize: 12,
          color: "#fff",
        },
        extraCssText: "text-align: center;",
      },
      grid: {
        top: "40px",
        left: "90px",
        right: "10px",
        bottom: "30px",
        containLabel: false,
      },
      xAxis: {
        type: "category",
        data: columns,
        splitArea: {
          show: true,
        },
        axisLabel: {
          interval: 0, // Show all labels
          formatter: function (value) {
            return value.substring(0, 15);
          },
          fontSize: 10,
          fontWeight: 400,
          color: "#1b645b",
        },
        axisLine: {
          show: false,
        },
        axisTick: {
          show: false,
        },
      },
      yAxis: {
        type: "category",
        data: rows,
        splitArea: {
          show: true,
        },
        axisLabel: {
          interval: 0, // Show all labels
          formatter: function (value) {
            return value.substring(0, 15);
          },
          fontSize: 10,
          fontWeight: 400,
          color: "#1b645b",
        },
        axisLine: {
          show: false,
        },
        axisTick: {
          show: false,
        },
      },
      visualMap: [
        {
          show: true,
          min: minColumnValue,
          max: maxColumnValue,
          calculable: true,
          orient: "horizontal",
          right: "10px",
          itemWidth: 10,
          top: "5px",
          formatter: function (value) {
            return helpers.beautifyNumber(value, 0);
          },
          inRange: {
            color: colorSet,
          },
        },
        {
          seriesIndex: 1,
          show: false,
          inRange: { color: "#1b645b" },
        },
      ],
      series: [
        {
          name: "Opportunity",
          type: "heatmap",
          data: seriesData,
          label: {
            show: true,
            formatter: function (params) {
              return helpers.beautifyNumber(params.value[2], 0);
            },
            fontSize: 10,
            fontWeight: 400,
            formatter: function (params) {
              const value = params.value[2];
              const normalizedValue =
                (value - minColumnValue) / (maxColumnValue - minColumnValue);
              if (normalizedValue > 0.5) {
                return (
                  "{high|" + helpers.beautifyNumber(params.value[2], 0) + "}"
                );
              } else {
                return "{low|" + helpers.beautifyNumber(params.value[2], 0) + "}";
              }
            },
            rich: {
              high: {
                color: "white",
                fontSize: 10,
                fontWeight: "normal",
              },
              low: {
                color: "#1b645b",
                fontSize: 10,
                fontWeight: "normal",
              },
            },
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: "rgba(0, 0, 0, 0.5)",
            },
          },
        },
        {
          name: "Placeholder for Total row and column",
          type: "heatmap",
          data: seriesData.filter(
            (item) => item[0] === maxColumnIndex || item[1] === maxRowIndex
          ),
          label: {
            show: true,
            formatter: function (params) {
              return helpers.beautifyNumber(params.value[2], 0);
            },
            fontSize: 10,
            fontWeight: 600,
            color: "white",
          },
          itemStyle: {
            borderColor: "transparent",
            color: "transparent",
          },
        },
      ],
    };
    dashboardManager.upSellDashboard.heatmap.setOption(options);
  
    let x = data["opportunity_chartjs_1"]["datasets"][0]["data"];
    let total1 = [0];
    for (let i = 0; i < x.length - 2; i++) {
      total1.push(total1[i] + x[i]);
    }
    total1.push(0);
    // destroy the existing chart1 if it exists
    if (dashboardManager.upSellDashboard.chart1) {
      dashboardManager.upSellDashboard.chart1.dispose();
    }
    dashboardManager.upSellDashboard.chart1 = echarts.init(
      document.getElementById("up-sell-chart1")
    );
    let chart1options = {
      title: {
        text: "Total Opportunities",
        left: "center",
        top: "10px",
        textStyle: {
          fontFamily: "Barlow, sans-serif",
          fontSize: 12,
          fontWeight: "bold",
          color: "#1b645b",
        },
      },
      toolbox: {
        feature: {
          saveAsImage: {},
        },
      },
      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: "shadow",
        },
        formatter: function (params) {
          var tar = params[1];
          return (
            tar.name +
            "<br/>" +
            tar.seriesName +
            " : " +
            helpers.beautifyNumber(tar.value, 2)
          );
        },
      },
      grid: {
        top: "40px",
        left: "50px",
        right: "10px",
        bottom: "30px",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        axisLabel: {
          show: true,
          interval: 0,
          formatter: function (value) {
            return value.substring(0, 15);
          },
          fontSize: 10,
          fontWeight: 400,
          color: "#1b645b",
        },
        splitLine: { show: false },
        data: data["opportunity_chartjs_1"]["labels"],
      },
      yAxis: {
        type: "value",
        axisLabel: {
          formatter: function (value) {
            return helpers.beautifyNumber(value, 0);
          },
          fontSize: 10,
          fontWeight: 400,
          color: "#1b645b",
        },
      },
      series: [
        {
          name: "Placeholder",
          type: "bar",
          stack: "Total",
          itemStyle: {
            borderColor: "transparent",
            color: "transparent",
          },
          emphasis: {
            itemStyle: {
              borderColor: "transparent",
              color: "transparent",
            },
          },
          data: total1,
        },
        {
          name: "Opportunities",
          type: "bar",
          stack: "Total",
          color: "#1b645b40",
          label: {
            show: true,
            position: "inside",
            formatter: function (params) {
              return helpers.beautifyNumber(params.value, 0);
            },
            fontSize: 10,
            fontWeight: 600,
            color: "#1b645b",
          },
          data: data["opportunity_chartjs_1"]["datasets"][0]["data"],
        },
      ],
    };
    dashboardManager.upSellDashboard.chart1.setOption(chart1options);
  
    let x2 = data["opportunity_chartjs_2"]["datasets"][0]["data"];
    let total2 = [0];
    for (let i = 0; i < x2.length - 2; i++) {
      total2.push(total2[i] + x2[i]);
    }
    total2.push(0);
    // create chart 2
    // destroy the existing chart2 if it exists
    if (dashboardManager.upSellDashboard.chart2) {
      dashboardManager.upSellDashboard.chart2.dispose();
    }
    dashboardManager.upSellDashboard.chart2 = echarts.init(
      document.getElementById("up-sell-chart2")
    );
    let chart2options = {
      title: {
        text: "# of Accounts with Opportunities",
        left: "center",
        top: "10px",
        textStyle: {
          fontFamily: "Barlow, sans-serif",
          fontSize: 12,
          fontWeight: "bold",
          color: "#1b645b",
        },
      },
      toolbox: {
        feature: {
          saveAsImage: {},
        },
      },
      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: "shadow",
        },
        formatter: function (params) {
          var tar = params[0];
          return (
            tar.name +
            "<br/>" +
            tar.seriesName +
            " : " +
            helpers.beautifyNumber(tar.value, 2)
          );
        },
      },
      grid: {
        top: "40px",
        left: "50px",
        right: "10px",
        bottom: "30px",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        axisLabel: {
          show: true,
          interval: 0,
          formatter: function (value) {
            return value.substring(0, 15);
          },
          fontSize: 10,
          fontWeight: 400,
          color: "#1b645b",
        },
        splitLine: { show: false },
        data: data["opportunity_chartjs_2"]["labels"],
      },
      yAxis: {
        type: "value",
        axisLabel: {
          formatter: function (value) {
            return helpers.beautifyNumber(value, 0);
          },
          fontSize: 10,
          fontWeight: 400,
          color: "#1b645b",
        },
      },
      series: [
        {
          name: "# of Accounts",
          type: "bar",
          color: "#1b645b40",
          label: {
            show: true,
            position: "inside",
            formatter: function (params) {
              return helpers.beautifyNumber(params.value, 1);
            },
            fontSize: 10,
            fontWeight: 600,
            color: "#1b645b",
          },
          data: data["opportunity_chartjs_2"]["datasets"][0]["data"],
        },
      ],
    };
    dashboardManager.upSellDashboard.chart2.setOption(chart2options);
  
    let x3 = data["opportunity_chartjs_3"]["datasets"][0]["data"];
    let total3 = [0];
    for (let i = 0; i < x3.length - 2; i++) {
      total3.push(total3[i] + x3[i]);
    }
    total3.push(0);
    // create chart 2
    // destroy the existing chart3 if it exists
    if (dashboardManager.upSellDashboard.chart3) {
      dashboardManager.upSellDashboard.chart3.dispose();
    }
    dashboardManager.upSellDashboard.chart3 = echarts.init(
      document.getElementById("up-sell-chart3")
    );
    let chart3options = {
      title: {
        text: "Average Opportunity Value",
        left: "center",
        top: "10px",
        textStyle: {
          fontFamily: "Barlow, sans-serif",
          fontSize: 12,
          fontWeight: "bold",
          color: "#1b645b",
        },
      },
      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: "shadow",
        },
        formatter: function (params) {
          var tar = params[0];
          return (
            tar.name +
            "<br/>" +
            tar.seriesName +
            " : " +
            helpers.beautifyNumber(tar.value, 2)
          );
        },
      },
      toolbox: {
        feature: {
          saveAsImage: {},
        },
      },
      grid: {
        top: "40px",
        left: "50px",
        right: "10px",
        bottom: "30px",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        axisLabel: {
          show: true,
          interval: 0,
          formatter: function (value) {
            return value.substring(0, 15);
          },
          fontSize: 10,
          fontWeight: 400,
          color: "#1b645b",
        },
        splitLine: { show: false },
        data: data["opportunity_chartjs_2"]["labels"],
      },
      yAxis: {
        type: "value",
        axisLabel: {
          formatter: function (value) {
            return helpers.beautifyNumber(value, 0);
          },
          fontSize: 10,
          fontWeight: 400,
          color: "#1b645b",
        },
      },
      series: [
        {
          name: "Average Opportunity Value",
          type: "bar",
          color: "#1b645b40",
          label: {
            show: true,
            position: "inside",
            formatter: function (params) {
              return helpers.beautifyNumber(params.value, 1);
            },
            fontSize: 10,
            fontWeight: 600,
            color: "#1b645b",
          },
          data: data["opportunity_chartjs_2"]["datasets"][0]["data"],
        },
      ],
    };
    dashboardManager.upSellDashboard.chart3.setOption(chart3options);
  
    modelManager.setModelParameters(data["config"]);
  }
  