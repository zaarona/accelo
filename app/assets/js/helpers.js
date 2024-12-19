let helpers = {
  beautifyNumber: function (number, decimals = 1) {
    if (isNaN(number)) {
      return 0;
    }
    if (number >= 1000000000) {
      return (number / 1000000000).toFixed(decimals) + "B";
    }
    if (number >= 1000000) {
      return (number / 1000000).toFixed(decimals) + "M";
    }
    if (number >= 1000) {
      return (number / 1000).toFixed(decimals) + "K";
    }
    return number.toFixed(decimals);
  },
  unbeautifyNumber: function (number, decimals = 1) {
    if (number.endsWith("B")) {
      return parseFloat(number.replace("B", "")) * 1000000000;
    }
    if (number.endsWith("M")) {
      return parseFloat(number.replace("M", "")) * 1000000;
    }
    return parseFloat(number.replace("K", "")) * 1000;
  },
  beautifyValue: function (value) {
    if (value === null) {
      return "";
    }
    if (parseFloat(value) !== NaN && typeof value === "number") {
      return helpers.beautifyNumber(value);
    }
    return value;
  },
  beautifyDate: function (date) {
    // 01 Jan 2024 12:00:00
    return new Date(date).toLocaleDateString("en-US", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  },
  pivotData: function (jsonData, rowKeys, colKeys, valueKey) {
    // Extract unique combinations of column keys
    const colCombinations = [];
    jsonData.forEach((item) => {
      const combination = colKeys.map((key) => item[key]).join("|");
      if (!colCombinations.includes(combination)) {
        colCombinations.push(combination);
      }
    });

    // Create a mapping of rows with their corresponding values for each column combination
    const rows = [];
    const rowMap = new Map();

    jsonData.forEach((item) => {
      const rowKey = rowKeys.map((key) => item[key]).join("|");
      const colKey = colKeys.map((key) => item[key]).join("|");

      if (!rowMap.has(rowKey)) {
        rowMap.set(rowKey, {
          row: Object.fromEntries(rowKeys.map((key) => [key, item[key]])),
          values: {},
        });
      }

      const row = rowMap.get(rowKey);
      row.values[colKey] = item[valueKey];
    });

    // Build the result structure
    rowMap.forEach((rowData, rowKey) => {
      const row = { ...rowData.row };
      colCombinations.forEach((colCombination) => {
        row[colCombination] = rowData.values[colCombination] || null;
      });
      rows.push(row);
    });

    return { rows, colHeaders: colCombinations };
  },
  getMostFrequentValue: function (columnData) {
    const frequency = {};
    columnData.forEach((value) => {
      frequency[value] = (frequency[value] || 0) + 1;
    });
    return Object.keys(frequency).reduce((a, b) =>
      frequency[a] > frequency[b] ? a : b
    );
  },
  scaledColor: function (number, array, color_start, color_end) {
    // Ensure the number is within the range of the array
    var min_val = Math.min(...array);
    var max_val = Math.max(...array);
    if (number < min_val) {
      return color_start;
    }
    if (number > max_val) {
      return color_end;
    }

    // Calculate the scale position of the number between min and max
    var scale_position = (number - min_val) / (max_val - min_val);

    // Parse the start and end colors to get RGB values
    var start_rgb = parseInt(color_start.slice(1), 16);
    var end_rgb = parseInt(color_end.slice(1), 16);
    var start_r = (start_rgb >> 16) & 0xff;
    var start_g = (start_rgb >> 8) & 0xff;
    var start_b = start_rgb & 0xff;
    var end_r = (end_rgb >> 16) & 0xff;
    var end_g = (end_rgb >> 8) & 0xff;
    var end_b = end_rgb & 0xff;

    // Calculate the new color components
    var new_r = Math.round(start_r + (end_r - start_r) * scale_position);
    var new_g = Math.round(start_g + (end_g - start_g) * scale_position);
    var new_b = Math.round(start_b + (end_b - start_b) * scale_position);

    // Return the new color in hexadecimal format
    return (
      "#" +
      ((1 << 24) + (new_r << 16) + (new_g << 8) + new_b)
        .toString(16)
        .slice(1)
        .toUpperCase()
    );
  },
  getTextColorBasedOnBackground: function (hexString) {
    let r = parseInt(hexString.slice(1, 3), 16);
    let g = parseInt(hexString.slice(3, 5), 16);
    let b = parseInt(hexString.slice(5, 7), 16);
    let brightness = Math.sqrt(0.299 * r*r + 0.587 * g*g + 0.114 * b*b);
    if(brightness > 130){
        return '#000000';
    } else {
        return '#FFFFFF';
    }
  },
  createColorGradient: function(color_start, color_end, length){
    let colors = [];
    for(let i = 0; i < length; i++){
      colors.push(helpers.scaledColor(i+2, [0, length+2], color_start, color_end));
    }
    return colors;
  }
};
