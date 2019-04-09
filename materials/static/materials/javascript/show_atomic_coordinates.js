$('.expand-hide-button').click(function() {
  var target_id = $(this).data('target');
  if (target_id.startsWith('#atomic-coordinates-body-') && $(target_id).is(':empty')) {
    var series_id = target_id.split('#atomic-coordinates-body-')[1];
    $.getJSON('/materials/get-atomic-coordinates/' + series_id, function(data) {
      var table = document.createElement('table');
      table.className = 'table-atomic-positions';
      var fragment = document.createDocumentFragment();
      var i, j;
      for (i=0; i<data['vectors'].length; i++) {
        var tr = document.createElement('tr');
        var td = document.createElement('td');
        td.innerHTML = 'lattice vector';
        td.style = 'text-align:left';
        tr.appendChild(td);
        for (j=0; j<3; j++) {
          var td = document.createElement('td');
          td.innerHTML = data['vectors'][i][j];
          tr.appendChild(td);
        }
        fragment.appendChild(tr);
      }
      table.appendChild(fragment);
      $(target_id).html(table);
      table = document.createElement('table');
      table.className = 'table-atomic-positions';
      for (i=0; i<data['coordinates'].length; i++) {
        var tr = document.createElement('tr');
        var td = document.createElement('td');
        td.innerHTML = data['coordinates'][i][0];
        td.style = 'text-align:left';
        tr.appendChild(td);
        for (j=1; j<4; j++) {
          var td = document.createElement('td');
          td.innerHTML = data['coordinates'][i][j];
          tr.appendChild(td);
        }
        fragment.appendChild(tr);
      }
      table.appendChild(fragment);
      $(target_id).append(table);
    });
  }
});
