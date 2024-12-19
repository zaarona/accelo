let dataManager = {
  data: null,
  decompressData: function (base64String) {
    const compressed = atob(base64String);
    const uint8Array = Uint8Array.from(compressed, (c) => c.charCodeAt(0));
    const decompressed = pako.inflate(uint8Array, { to: "string" });
    return JSON.parse(decompressed);
  },
  loadDataSheet: function () {
    eventManager.showLoading();
    const projectName = $("#active-project-name").val();
    const versionName = $("#active-version-name").val();

    fetch(`${constants.HOST_URL}data/data-sheet/${projectName}/${versionName}`)
      .then((response) => response.text())
      .then((base64String) => {
        if (base64String === "") {
          eventManager.hideLoading();
          return;
        }
        dataManager.data = dataManager.decompressData(base64String);
        eventManager.updateActiveViewSelector();
        $('#active-view-selector').val('sales-data').trigger('change');
        eventManager.hideLoading();
      });
  },
  loadCrossSellData: async function () {
    eventManager.showLoading();
    const projectName = $("#active-project-name").val();
    const versionName = $("#active-version-name").val();
    fetch(`${constants.HOST_URL}xs-quant/${projectName}/${versionName}`)
      .then((response) => response.text())
      .then((base64String) => {
        dataManager.data = dataManager.decompressData(base64String);
        eventManager.updateActiveViewSelector();
        $('#active-view-selector').val('accounts').trigger('change');
        eventManager.hideLoading();
      });
  },
  updateCrossSellData: function () {
    eventManager.showLoading();
    const common_industry = $("#industry").val();
    const common_geo = $("#region").val();
    const segment = $("#segment").val();
    const projectName = $("#active-project-name").val();
    const versionName = $("#active-version-name").val();
    fetch(
      `${constants.HOST_URL}xs-quant/${projectName}/${versionName}?common_industry=${common_industry}&common_geo=${common_geo}&segment=${segment}`
    )
      .then((response) => response.text())
      .then((base64String) => {
        dataManager.data = dataManager.decompressData(base64String);
        render.updateView();
        eventManager.hideLoading();
      });
  },
  loadFactPackData: function () {
    eventManager.showLoading();
    const projectName = $("#active-project-name").val();
    const versionName = $("#active-version-name").val();
    fetch(`${constants.HOST_URL}fact-pack/${projectName}/${versionName}`)
      .then((response) => response.text())
      .then((base64String) => {
        dataManager.data = dataManager.decompressData(base64String);
        eventManager.updateActiveViewSelector();
        $('#active-view-selector').val('data-cube').trigger('change');
        eventManager.hideLoading();
      });
  },
  loadPriceUpliftData: function () {
    eventManager.showLoading();
    const projectName = $("#active-project-name").val();
    const versionName = $("#active-version-name").val();
    fetch(`${constants.HOST_URL}price-uplift/${projectName}/${versionName}`)
      .then((response) => response.text())
      .then((base64String) => {
        dataManager.data = dataManager.decompressData(base64String);
        eventManager.updateActiveViewSelector();
        $('#active-view-selector').val('asp-build').trigger('change');
        eventManager.hideLoading();
      });
  },
  loadSegmentationData: function () {
    eventManager.showLoading();
    const projectName = $("#active-project-name").val();
    const versionName = $("#active-version-name").val();
    // if projectName is null, wait for it to be set
    if (projectName === null) {
      setTimeout(dataManager.loadSegmentationData, 100);
      return;
    }
    fetch(`${constants.HOST_URL}segmentation/${projectName}/${versionName}`)
      .then((response) => response.text())
      .then((base64String) => {
        dataManager.data = dataManager.decompressData(base64String);
        eventManager.updateActiveViewSelector();
        $('#active-view-selector').val('clustering').trigger('change');
        eventManager.hideLoading();
      });
  }
};
