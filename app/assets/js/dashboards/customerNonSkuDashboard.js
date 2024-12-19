function customerNonSkuDashboard() {
    let data = dataManager.data["customer-non-sku"].data;
    let uplifts_table = data["uplift_table"];
    let columnDefs = uplifts_table['columnDefs'];
    let rowData = uplifts_table['rowData'];

    let gridOptions = gridManager.getGridOptions(columnDefs, rowData);
    gridOptions.theme = gridManager.getTheme();
    gridOptions.tooltipShowDelay = 100;
    gridOptions.tooltipHideDelay = 5000;
    gridOptions.autoSizeStrategy = {
        type: "fitGridWidth"
    };
    // formatter:
    columnDefs.forEach(function(col) {
        if (col.children) {
            col.children.forEach((child) => {
                child.headerTooltip = true;
                child.tooltipComponent = gridHeaderTooltip;
                child.valueFormatter = function(params) {
                    return helpers.beautifyValue(params.value);
                }
            });
        } else {
            col.headerTooltip = true;
            col.tooltipComponent = gridHeaderTooltip;
            col.valueFormatter = function(params) {
                return helpers.beautifyValue(params.value);
            }
        }
    });

    agGrid.createGrid(
        document.getElementById("customer-non-sku"),
        gridOptions
    );
}