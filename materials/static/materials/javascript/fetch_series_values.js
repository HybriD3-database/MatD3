Array.from(document.querySelectorAll('tbody[class="tabulated-data"]')).forEach(function(table_body) {
  var series_pk = table_body.id.split('-')[1];
  $.getJSON('/materials/get-series-values/' + series_pk, function(data) {
    var table = document.createElement('table');
    var fragment = document.createDocumentFragment();
    for (var i=0; i<data.length; i++) {
      var tr = document.createElement('tr');
      var td = document.createElement('td');
      if ('x' in data[i]) {
        td.innerHTML = data[i]['x'];
        tr.appendChild(td);
      }
      td = document.createElement('td');
      td.innerHTML = data[i]['y'];
      tr.appendChild(td);
      fragment.appendChild(tr);
    }
    table_body.append(fragment);
  });
});
