function bundlingDashboard() {
    let data = dataManager.data["bundling"];
    let bundling_table = data["bundling_table"];
    let heatmap_data = data["heatmap_data"];
    let table_type = 'percentage';
    data['bundling_table']['columnDefs'].forEach(function(column) {
        if(column.field != data['bundling_table']['columnDefs'][0].field){
            column.cellStyle = function(params) {
                let backgroundColor = helpers.scaledColor(params.value, data['bundling_table']['heatmap_data'], '#ffffff', '#1b645b');
                return {color: helpers.getTextColorBasedOnBackground(backgroundColor), backgroundColor: backgroundColor};
            }
            column.valueFormatter = function(params) {
                if(table_type == 'percentage')
                    return helpers.beautifyValue(params.value) + '%';
                else
                    return helpers.beautifyValue(params.value);
            }
        }
    });

    let columnDefs = bundling_table['columnDefs'];
    let rowData = bundling_table['rowData'];

    let gridOptions = gridManager.getGridOptions(columnDefs, rowData);
    gridOptions.theme = gridManager.getTheme();
    gridOptions.tooltipShowDelay = 100;
    gridOptions.tooltipHideDelay = 5000;

    agGrid.createGrid(
        document.getElementById("bundling"),
        gridOptions
    );
}