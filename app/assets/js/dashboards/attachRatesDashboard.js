function attachRatesDashboard() {
    let data = dataManager.data["attach-rates"];
    let attach_rates_table = data["attach_rates_table"];
    let heatmap_data = data["heatmap_data"];

    attach_rates_table['columnDefs'].forEach(function(column) {
        if(column.field != attach_rates_table['columnDefs'][0].field){
            column.cellStyle = function(params) {
                let backgroundColor = helpers.scaledColor(params.value, data['attach_rates_table']['heatmap_data'], '#ffffff', '#1b645b');
                return {color: helpers.getTextColorBasedOnBackground(backgroundColor), backgroundColor: backgroundColor};
            }
            column.valueFormatter = function(params) {
                return helpers.beautifyValue(params.value, 1) + '%';
            }
        }
    });

    let columnDefs = attach_rates_table['columnDefs'];
    let rowData = attach_rates_table['rowData'];

    let gridOptions = gridManager.getGridOptions(columnDefs, rowData);
    gridOptions.theme = gridManager.getTheme();
    gridOptions.tooltipShowDelay = 100;
    gridOptions.tooltipHideDelay = 5000;
  
    agGrid.createGrid(
      document.getElementById("attach-rates"),
      gridOptions
    );
}