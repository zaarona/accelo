let modelManager = {
  revenueSlider: null,
  spendSlider: null,
  init: function () {
    console.log("modelManager init");
  },
  getModelParameters: function () {
    let cutoff_date = $("#cutoff-date").val();
    let breakdown_variable = $("#breakdown-variable").val();
    let aggregation_variable = $('#aggregation-variable').val();
    let minimum_sample_size = $('#minimum-sample-size').val();
    let percentile = $('#percentile').val();
    let cohort_vars = $("#cohort-vars").val();
    let subscription_products = $("#subscription-products").val();
    let perpetual_products = $("#perpetual-products").val();
    let breakdown_params = {};
    let revenue_buckets = $("#revenue-buckets").val();
    let spend_buckets = $("#spend-buckets").val();
    // convert revenue_buckets and spend_buckets to arrays
    revenue_buckets = revenue_buckets.split(',').map(bucket => helpers.unbeautifyNumber(bucket, 0));
    spend_buckets = spend_buckets.split(',').map(bucket => helpers.unbeautifyNumber(bucket, 0));

    subscription_products.forEach(product => {
      breakdown_params[product] = 'SUBSCRIPTION';
    });
    perpetual_products.forEach(product => {
      breakdown_params[product] = 'PERPETUAL';
    });
    return {
      'this_year': parseInt(cutoff_date.split('-')[0]),
      'breakdown_column': breakdown_variable,
      'aggregation_variable': aggregation_variable,
      'minimum_sample_size': minimum_sample_size,
      'percentile': percentile,
      'cohort_columns': cohort_vars,
      'breakdown_params': breakdown_params,
      'revenue_buckets': revenue_buckets,
      'spend_buckets': spend_buckets,
    };
  },
  setModelParameters: function (config) {
    this.disableChangeListeners();

    let cohort_vars = config.cohort_columns.split(' - ');
    $('#cutoff-date').val(config.this_year+'-12-31');
    $('#breakdown-variable').val(config.breakdown_column);
    $('#aggregation-variable').val(config.aggregation_variable);
    $('#minimum-sample-size').val(config.minimum_sample_size);
    $('#percentile').val(config.percentile);
    $('#cohort-vars').val(cohort_vars);

    $("#cutoff-date, #cohort-vars, #breakdown-variable, #aggregation-variable, #minimum-sample-size, #percentile").trigger("chosen:updated");
    
    let subscriptionProducts = [];
    let perpetualProducts = [];
    Object.keys(config["breakdown_params"]).forEach(key => {
      if (config["breakdown_params"][key] === "SUBSCRIPTION") {
        subscriptionProducts.push(key);
      } else {
        perpetualProducts.push(key);
      }
    });
    $("#subscription-products").empty();
    $("#perpetual-products").empty();
    let allProducts = subscriptionProducts.concat(perpetualProducts);
    allProducts.forEach(product => {
      $("#subscription-products").append(`<option value="${product}">${product}</option>`);
      $("#perpetual-products").append(`<option value="${product}">${product}</option>`);
    });
    $("#subscription-products").val(subscriptionProducts);
    $("#perpetual-products").val(perpetualProducts);
    $("#subscription-products").trigger("chosen:updated");
    $("#perpetual-products").trigger("chosen:updated");

    $("#subscription-products").change((e) => {
      let selectedProducts = $("#subscription-products").val();
      $("#perpetual-products").val(perpetualProducts.filter(product => !selectedProducts.includes(product)));
      $("#perpetual-products").trigger("chosen:updated");
    });
    $("#perpetual-products").change((e) => {
      let selectedProducts = $("#perpetual-products").val();
      $("#subscription-products").val(subscriptionProducts.filter(product => !selectedProducts.includes(product)));
      $("#subscription-products").trigger("chosen:updated");
    });
    // destroy the existing sliders if they exist
    if (this.revenueSlider) {
      this.revenueSlider.destroy();
    }
    if (this.spendSlider) {
      this.spendSlider.destroy();
    }

    // create nouislider for revenue buckets
    let revenueBuckets = config.revenue_buckets.map(bucket => helpers.beautifyNumber(bucket, 0));
    let spendBuckets = config.spend_buckets.map(bucket => helpers.beautifyNumber(bucket, 0));
    $("#revenue-buckets").val(revenueBuckets.join(', '));
    $("#spend-buckets").val(spendBuckets.join(', '));

    
    modelManager.attachChangeListeners();
  },
  disableChangeListeners: function () {
    $('#cutoff-date, #breakdown-variable, #aggregation-variable, #minimum-sample-size, #percentile, #cohort-vars, #subscription-products, #perpetual-products, #revenue-buckets, #spend-buckets').off('change');
  },
  attachChangeListeners: function () {
    this.disableChangeListeners();
    $('#cutoff-date, #breakdown-variable, #aggregation-variable, #minimum-sample-size, #percentile, #cohort-vars, #subscription-products, #perpetual-products, #revenue-buckets, #spend-buckets').change(function () {
      modelManager.updateModelParameters(modelManager.getModelParameters());
    });
  },
  updateModelParameters: function (params) {
    eventManager.showLoading();
    $.ajax({
      url: '/xs-quant/update-config/' + $('#active-project-name').val() + '/' + $('#active-version-name').val(),
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(params),
      success: function (response) {
        eventManager.hideLoading();
        dataManager.updateCrossSellData();
      },
    });
  },
};
