function ParseWeeklyUpdate(json_url) {
  var response = UrlFetchApp.fetch(json_url);
  var data = JSON.parse(response.getContentText());

  var ss = SpreadsheetApp.create("TEMP");
  var bool_from = false;
  var from = null;
  var to = null;
  var first_deleted = false;
  var first_sheet = ss.getActiveSheet();
  for (i in data) {
    if (i == "counters") {
      var sheett = ss.insertSheet("Charts", 0);
      var chart_data = data[i];
      var row = 0;
      for (employee in chart_data) {
        var data_emp = chart_data[employee];
        for (r = 0; r < 7; r++) {
          row = row + 1;
          sheett.getRange(row, 1).setValue(data_emp[r][0]);
          sheett.getRange(row, 2).setValue(data_emp[r][1]);
        }
      }
      var row = 1;
      var plan = 1;
      for (employee in chart_data) {
        drawChart(employee, sheett, row, plan);
        row = row + 7;
        plan = plan + 4;
      }
      continue;
    }
    to = i;
    if (!bool_from) {
      from = i;
      bool_from = true;
    }
    var sheet = ss.insertSheet(i);
    if (!first_deleted) {
      ss.deleteSheet(first_sheet);
      first_deleted = true;
    }
    var last_pos = 1;
    for (employee in data[i]) {
      var column = sheet.insertColumnAfter(last_pos);
      column.getRange(1, last_pos).setValue(employee);
      column.getRange(1, last_pos).setBackground("#b7e1cd");
      column.getRange(1, last_pos).setFontWeight("bold");
      column.getRange(1, last_pos).setHorizontalAlignment("center");
      var cell = sheet.getActiveCell().getValue();
      last_pos = last_pos + 1;
      var item_pos = 2;
      var max_len = 0;
      for (item in data[i][employee]) {
        ss.toast(column.getIndex());
        var range = column.getRange(item_pos, last_pos - 1);
        item_pos = item_pos + 1;
        var msg = data[i][employee][item];
        range.setValue(msg);
      }
      sheet.autoResizeColumn(last_pos - 1);
    }
  }
  ss.rename("Status report " + from + " - " + to);
  ss.toast("All done");
}

function drawChart(title, sheet, row, plan) {
  var chart = sheet.newChart()
        .setChartType(Charts.ChartType.PIE)
        .addRange(sheet.getRange(row, 1, 7, 2))
        .setPosition(1, plan, 0, 0)
        .setOption('title', title)
        .setOption('width', 400)
        .setOption('height', 225)
        .build();
  sheet.insertChart(chart);
  }