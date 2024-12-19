let queryBuilderManager = {
  init: function () {
    $("#builder").queryBuilder({
      // plugins: ['bt-tooltip-errors'], not in the code/ cdn
      filters: [
        {
          id: "License Quantity",
          label: "License Quantity",
          type: "integer",
        },
        {
          id: "Asset Value",
          label: "Asset Value",
          type: "integer",
        },
      ],
    });
  },
  initQueryBuilder: function (columnDefs, index) {
    // Destroy existing query builder if it exists
    if ($("#builder").queryBuilder("getModel")) {
      $("#builder").queryBuilder("destroy");
    }

    // Create filters array from column definitions
    const filters = columnDefs.map((col) => {
      // Get all unique values for the column
      const colIndex = columnDefs.indexOf(col);
      const columnData = dataManager.data[index].data
        .slice(1)
        .map((row) => row[colIndex]);
      const uniqueValues = [...new Set(columnData)].filter(
        (val) => val !== null && val !== undefined
      );

      // Check if column is numeric
      const isNumeric = columnData.every(
        (val) => !isNaN(parseFloat(val)) && val !== null && val !== ""
      );

      // If column has few unique values and isn't numeric, treat as categorical
      const isCategorical = !isNumeric && uniqueValues.length <= 20; // Adjust threshold as needed

      let filterConfig = {
        id: col.field,
        label: col.headerName,
      };

      if (isNumeric) {
        // Numeric column configuration
        filterConfig.type = "double";
        filterConfig.operators = [
          "equal",
          "not_equal",
          "less",
          "less_or_equal",
          "greater",
          "greater_or_equal",
          "between",
        ];
      } else if (isCategorical) {
        // Categorical column configuration
        filterConfig.type = "string";
        filterConfig.input = "select";
        filterConfig.multiple = true; // Enable multiple selection
        filterConfig.plugin = "selectize"; // Use selectize for better UX
        filterConfig.plugin_config = {
          maxItems: null, // Allow any number of items
          delimiter: "|", // Delimiter for multiple values
          removeButton: true, // Show remove button
        };
        filterConfig.values = uniqueValues.reduce((obj, val) => {
          obj[val] = val;
          return obj;
        }, {});
        filterConfig.operators = ["equal", "not_equal", "in", "not_in"];
        filterConfig.valueSetter = function (rule, value) {
          rule.$el
            .find(".rule-value-container select")[0]
            .selectize.setValue(value);
        };
      } else {
        // Text column configuration
        filterConfig.type = "string";
        filterConfig.operators = [
          "equal",
          "not_equal",
          "contains",
          "not_contains",
          "begins_with",
          "ends_with",
          "is_empty",
          "is_not_empty",
        ];
      }

      return filterConfig;
    });

    // Initialize jQuery Query Builder
    $("#builder").queryBuilder({
      filters: filters,
      allow_empty: true,
      plugins: {
        // 'bt-tooltip-errors': { delay: 100 },
        // 'sortable': { icon: 'fa fa-sort' },
        // 'filter-description': { mode: 'bootbox' }
      },
      select_placeholder: "-- Select value --",
      optgroups: {},
      operators: [
        {
          type: "equal",
          nb_inputs: 1,
          multiple: false,
          apply_to: ["string", "number", "datetime", "boolean"],
        },
        {
          type: "not_equal",
          nb_inputs: 1,
          multiple: false,
          apply_to: ["string", "number", "datetime", "boolean"],
        },
        {
          type: "in",
          nb_inputs: 1,
          multiple: true,
          apply_to: ["string", "number", "datetime"],
        },
        {
          type: "not_in",
          nb_inputs: 1,
          multiple: true,
          apply_to: ["string", "number", "datetime"],
        },
        {
          type: "less",
          nb_inputs: 1,
          multiple: false,
          apply_to: ["number", "datetime"],
        },
        {
          type: "less_or_equal",
          nb_inputs: 1,
          multiple: false,
          apply_to: ["number", "datetime"],
        },
        {
          type: "greater",
          nb_inputs: 1,
          multiple: false,
          apply_to: ["number", "datetime"],
        },
        {
          type: "greater_or_equal",
          nb_inputs: 1,
          multiple: false,
          apply_to: ["number", "datetime"],
        },
        {
          type: "between",
          nb_inputs: 2,
          multiple: false,
          apply_to: ["number", "datetime"],
        },
        {
          type: "contains",
          nb_inputs: 1,
          multiple: false,
          apply_to: ["string"],
        },
        {
          type: "not_contains",
          nb_inputs: 1,
          multiple: false,
          apply_to: ["string"],
        },
        {
          type: "begins_with",
          nb_inputs: 1,
          multiple: false,
          apply_to: ["string"],
        },
        {
          type: "ends_with",
          nb_inputs: 1,
          multiple: false,
          apply_to: ["string"],
        },
        {
          type: "is_empty",
          nb_inputs: 0,
          multiple: false,
          apply_to: ["string"],
        },
        {
          type: "is_not_empty",
          nb_inputs: 0,
          multiple: false,
          apply_to: ["string"],
        },
      ],
    });

    // Add event handlers for filter buttons
    $("#btn-set")
      .off("click")
      .on("click", function () {
        const rules = $("#builder").queryBuilder("getRules");
        if ($.isEmptyObject(rules)) return;

        dataManager.applyFilter(rules);
      });

    $("#btn-reset")
      .off("click")
      .on("click", function () {
        $("#builder").queryBuilder("reset");
        dataManager.grid.setFilterModel(null);
      });
  },
  applyFilter: function (rules) {
    // Convert Query Builder rules to AG-Grid filter model
    const filterModel = this.convertRulesToFilterModel(rules);
    dataManager.grid.setFilterModel(filterModel);
  },
  convertRulesToFilterModel: function (rules) {
    const filterModel = {};

    function processRule(rule) {
      if (rule.condition) {
        // Handle groups of rules
        const conditions = rule.rules.map((r) => processRule(r));
        return {
          operator: rule.condition.toLowerCase(),
          conditions: conditions,
        };
      } else {
        // Handle individual rules
        const filterConfig = {
          filterType: "text",
          type: "contains",
          filter: rule.value,
        };

        // Adjust filter type and operator based on rule operator
        switch (rule.operator) {
          case "equal":
            filterConfig.type = "equals";
            break;
          case "not_equal":
            filterConfig.type = "notEqual";
            break;
          case "in":
            filterConfig.type = "equals";
            filterConfig.values = rule.value;
            break;
          case "not_in":
            filterConfig.type = "notEqual";
            filterConfig.values = rule.value;
            break;
          case "less":
            filterConfig.type = "lessThan";
            break;
          case "greater":
            filterConfig.type = "greaterThan";
            break;
          case "less_or_equal":
            filterConfig.type = "lessThanOrEqual";
            break;
          case "greater_or_equal":
            filterConfig.type = "greaterThanOrEqual";
            break;
          case "contains":
            filterConfig.type = "contains";
            break;
          case "begins_with":
            filterConfig.type = "startsWith";
            break;
          case "ends_with":
            filterConfig.type = "endsWith";
            break;
          case "is_empty":
            filterConfig.type = "empty";
            break;
          case "is_not_empty":
            filterConfig.type = "notEmpty";
            break;
        }

        filterModel[rule.field] = filterConfig;
        return filterConfig;
      }
    }

    processRule(rules);
    return filterModel;
  },
};
