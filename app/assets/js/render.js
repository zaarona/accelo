let render = {
  activePanelView: null,
  updateView: function() {
    render.checkActiveView();
    render.activePanelView = eventManager.activePanel + '-' + eventManager.activeView;
    if(render.activePanelView === 'input-sales-data'){
      gridManager.createGrid($('#'+eventManager.activeView), eventManager.activeView);
    }
    if(render.activePanelView === 'input-product-lookup'){
      gridManager.createGrid($('#'+eventManager.activeView), eventManager.activeView);
    }
    if(render.activePanelView === 'input-industry-lookup'){
      gridManager.createGrid($('#'+eventManager.activeView), eventManager.activeView);
    }
    if(render.activePanelView === 'input-geo-lookup'){
      gridManager.createGrid($('#'+eventManager.activeView), eventManager.activeView);
    }
    if(render.activePanelView === 'input-customer-lookup'){
      gridManager.createGrid($('#'+eventManager.activeView), eventManager.activeView);
    }
    if(render.activePanelView === 'xs-quant-accounts'){
      gridManager.createGrid($('#'+eventManager.activeView), eventManager.activeView);
    }
    if(render.activePanelView === 'xs-quant-deal-size'){
      gridManager.createGrid($('#'+eventManager.activeView), eventManager.activeView);
    }
    if(render.activePanelView === 'xs-quant-cohorts'){
      gridManager.createGrid($('#'+eventManager.activeView), eventManager.activeView);
    }
    if(render.activePanelView === 'xs-quant-opportunities'){
      gridManager.createGrid($('#'+eventManager.activeView), eventManager.activeView);
    }
    if(render.activePanelView === 'xs-quant-cross-sell'){
      crossSellDashboard();
    }
    if(render.activePanelView === 'xs-quant-up-sell'){
      upSellDashboard();
    }
    if(render.activePanelView === 'fact-pack-data-cube'){
      dataCubeDashboard();
    }
    if(render.activePanelView === 'fact-pack-arrs'){
      arrsDashboard();
    }
    if(render.activePanelView === 'fact-pack-pareto-analysis'){
      paretoAnalysisDashboard();
    }
    if(render.activePanelView === 'fact-pack-attach-rates'){
      attachRatesDashboard();
    }
    if(render.activePanelView === 'fact-pack-bundling'){
      bundlingDashboard();
    }
    if(render.activePanelView === 'price-uplift-asp-build'){
      aspBuildDashboard();
    }
    if(render.activePanelView === 'price-uplift-customer-non-sku'){
      customerNonSkuDashboard();
    }
    if(render.activePanelView === 'segmentation-clustering'){
      clusteringDashboard();
    }
    if(render.activePanelView === 'segmentation-model-integration'){
      modelIntegrationDashboard();
    }
  },
  checkActiveView: function() {
    render.checkActivePanel();
  },
  checkActivePanel: function() {
    if(eventManager.activePanel === null){
      $('.nav-item[data-panel="input"]').click();
    }
  }
};

