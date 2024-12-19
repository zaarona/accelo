let gridManager = {
  grid: null,
  getTheme: function () {
    return agGrid.themeQuartz.withPart(agGrid.iconSetAlpine).withParams({
      accentColor: "#1B645B",
      borderColor: "#1B635B21",
      borderRadius: 2,
      browserColorScheme: "light",
      cellTextColor: "#1B645B",
      fontFamily: "inherit",
      fontSize: 11,
      headerFontSize: 13,
      headerFontWeight: 600,
      headerTextColor: "#1B645B",
      iconSize: 12,
      oddRowBackgroundColor: "#1B635B10",
      spacing: 3,
      wrapperBorderRadius: 2,
    });
  },
  getGridOptions: function (columnDefs, rowData) {
    return {
      columnDefs: columnDefs,
      rowData: rowData,
      autoSizeStrategy: {
        type: "fitCellContents",
      },
      defaultColDef: {
        flex: 1,
        editable: true,
        sortable: true,
        filter: true,
        resizable: true,
        minWidth: 150,
        maxWidth: 350,
      },
      tooltipShowDelay: 100,
      tooltipHideDelay: 5000,
      theme: gridManager.getTheme(),
    };
  },
  createGrid: function (container, viewName) {
    gridManager.calculateKpis(viewName);
    gridManager.createKpis($('#'+viewName+'-kpis-content'), viewName);
    if (gridManager.grid) {
      gridManager.grid.destroy();
    }

    const columnDefs = dataManager.data[viewName].data[0].map((header, index) => ({
      field: header || `col_${index}`,
      headerName: header || `Column ${index + 1}`,
      editable: true,
      sortable: true,
      filter: true,
      resizable: true,
      valueFormatter: function (params) {
        return helpers.beautifyValue(params.value);
      },
      headerTooltip: true,
      tooltipComponent: gridHeaderTooltip,
    }));

    // Initialize query builder with column definitions
    queryBuilderManager.initQueryBuilder(columnDefs, viewName);

    const rowData = dataManager.data[viewName].data.slice(1).map((row) => {
      const rowObj = {};
      row.forEach((cell, index) => {
        rowObj[columnDefs[index].field] = cell;
      });
      return rowObj;
    });

    dataManager.gridOptions = gridManager.getGridOptions(columnDefs, rowData);
    gridManager.grid = agGrid.createGrid(document.getElementById(container.get(0).id), dataManager.gridOptions);
    let s = `
        <svg viewBox="-4.41 -4.41 29.82 29.82" class="ag-icon ag-icon-export model-parameter-svg" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <title>save_item [#1411]</title> <desc>Created with Sketch.</desc> <defs> </defs> <g id="Page-1" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd"> <g id="Dribbble-Light-Preview" transform="translate(-419.000000, -640.000000)" fill="#000000"> <g id="icons" transform="translate(56.000000, 160.000000)"> <path d="M370.21875,484 C370.21875,483.448 370.68915,483 371.26875,483 C371.84835,483 372.31875,483.448 372.31875,484 C372.31875,484.552 371.84835,485 371.26875,485 C370.68915,485 370.21875,484.552 370.21875,484 L370.21875,484 Z M381.9,497 C381.9,497.552 381.4296,498 380.85,498 L379.8,498 L379.8,494 C379.8,492.895 378.86025,492 377.7,492 L369.3,492 C368.13975,492 367.2,492.895 367.2,494 L367.2,498 L366.15,498 C365.5704,498 365.1,497.552 365.1,497 L365.1,487.044 C365.1,486.911 365.15565,486.784 365.2533,486.691 L367.2,484.837 L367.2,486 C367.2,487.105 368.13975,488 369.3,488 L377.7,488 C378.86025,488 379.8,487.105 379.8,486 L379.8,482 L380.85,482 C381.4296,482 381.9,482.448 381.9,483 L381.9,497 Z M377.7,498 L369.3,498 L369.3,495 C369.3,494.448 369.7704,494 370.35,494 L376.65,494 C377.2296,494 377.7,494.448 377.7,495 L377.7,498 Z M369.3,482.837 L370.17885,482 L377.7,482 L377.7,485 C377.7,485.552 377.2296,486 376.65,486 L370.35,486 C369.7704,486 369.3,485.552 369.3,485 L369.3,482.837 Z M381.9,480 L369.7347,480 C369.45645,480 369.18975,480.105 368.99235,480.293 L363.30765,485.707 C363.11025,485.895 363,486.149 363,486.414 L363,498 C363,499.105 363.93975,500 365.1,500 L381.9,500 C383.06025,500 384,499.105 384,498 L384,482 C384,480.895 383.06025,480 381.9,480 L381.9,480 Z" id="save_item-[#1411]"> </path> </g> </g> </g> </g></svg>
    `;

    container.append(`${s}`);
    container.find(".ag-icon-export").on("click", function () {
        dataManager.exportData();
    });
  },
  calculateKpis: function (viewName) {
    // for each column, calculate average, count, sum, min, max
    let kpis = [];
    console.log(viewName);
    dataManager.data[viewName].data[0].forEach((column, i) => {
      let columnData = dataManager.data[viewName].data.map((row) => row[i]);
      columnData = columnData.filter((value) => !isNaN(value));
      if (
        typeof parseFloat(columnData[0]) === "number" &&
        columnData.length > 0
      ) {
        columnData = columnData.map((value) => parseFloat(value));
        // remove NaN values
        columnData = columnData.filter((value) => !isNaN(value));
        kpis.push({
          title: column,
          value: {
            average: columnData.reduce((a, b) => a + b, 0) / columnData.length,
            count: columnData.length,
            sum: columnData.reduce((a, b) => a + b, 0),
            min: Math.min(...columnData),
            max: Math.max(...columnData),
          },
        });
      }
      // else get the most frequent value, and count the number of unique values
      else {
        console.log(column);
        columnData = dataManager.data[viewName].data.map((row) => row[i]);
        kpis.push({
          title: column,
          value: {
            mostfrequent: helpers.getMostFrequentValue(columnData),
            uniquecount: new Set(columnData).size,
          },
        });
      }
    });
    dataManager.data[viewName].kpis = kpis;
  },
  createKpis: function (container, viewName) {
    container.empty();
    dataManager.data[viewName].kpis.forEach((kpi) => {
      [
        "Average",
        "Count",
        "Sum",
        "Most Frequent",
        "Unique Count",
      ].forEach((type) => {
        let typeLower = type.toLowerCase().replace(" ", "");
        if (
          kpi.value[typeLower] == Infinity ||
          kpi.value[typeLower] == -Infinity ||
          kpi.value[typeLower] == 0 ||
          kpi.value[typeLower] == NaN ||
          kpi.value[typeLower] == null ||
          kpi.value[typeLower] == undefined ||
          kpi.value[typeLower].toString() == "NaN" ||
          kpi.value[typeLower].toString() == "Infinity" ||
          kpi.value[typeLower].toString() == "-Infinity" ||
          kpi.value[typeLower].toString() == "0"
        ) {
          return;
        }
        if (typeLower in kpi.value) {
          container
            .append(`<div class="data-sheet-kpis-card">
                        <div class="data-sheet-kpis-card-header">
                            <div class="data-sheet-kpis-card-header-title">${
                              kpi.title
                            } (${type})</div>
                            <div class="data-sheet-kpis-card-header-value">${helpers.beautifyValue(
                              kpi.value[typeLower]
                            )}</div>
                        </div>
                    </div>`);
        }
      });
    });
  },
  exportData: function () {
    const columnDefs = dataManager.grid.getColumnDefs();
    const headers = columnDefs.map((col) => col.headerName);
    const rowData = [];
    dataManager.grid.forEachNode((node) => rowData.push(node.data));
    const data = [headers]; // First row is headers
    rowData.forEach((row) => {
      const rowValues = columnDefs.map((col) => row[col.field]);
      data.push(rowValues);
    });
    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.aoa_to_sheet(data);
    XLSX.utils.book_append_sheet(workbook, worksheet, "Sheet1");
    const filename =
      [
        $("#active-project-name").val(),
        $("#active-version-name").val(),
        $("#active-view-selector option:selected").text(),
        new Date().toISOString().split("T")[0],
      ].join("_") + ".xlsx";
    XLSX.writeFile(workbook, filename);
  },
};
