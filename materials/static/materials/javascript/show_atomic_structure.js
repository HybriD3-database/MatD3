Array.from(document.getElementsByClassName('expand-hide-button')).forEach(function(element) {
  element.addEventListener('click', function() {
    var target = document.getElementById(element.dataset.target.split('#')[1]);
    if (target.id.startsWith('atomic-coordinates-body-') && target.innerHTML === '') {
      var series_id = target.id.split('atomic-coordinates-body-')[1];
      $.getJSON('/materials/get-atomic-coordinates/' + series_id, function(data) {
        var table = document.createElement('table');
        table.className = 'table-atomic-coordinates';
        var fragment = document.createDocumentFragment();
        for (var i=0; i<data['vectors'].length; i++) {
          var tr = document.createElement('tr');
          var td = document.createElement('td');
          td.innerHTML = 'lattice vector';
          td.style = 'text-align:left';
          tr.appendChild(td);
          for (var j=0; j<3; j++) {
            var td = document.createElement('td');
            td.innerHTML = data['vectors'][i][j];
            tr.appendChild(td);
          }
          fragment.appendChild(tr);
        }
        table.appendChild(fragment);
        target.append(table);
        var coord_type = document.createElement('div');
        coord_type.style.textAlign = 'center';
        coord_type.style.fontStyle = 'italic';
        if (data['coord-type'] == 'atom_frac') {
          coord_type.innerHTML = 'Fractional coordinates:';
        } else {
          coord_type.innerHTML = 'Absolute coordinates:';
        }
        target.append(coord_type);
        table = document.createElement('table');
        table.className = 'table-atomic-coordinates';
        for (var i=0; i<data['coordinates'].length; i++) {
          var tr = document.createElement('tr');
          var td = document.createElement('td');
          td.innerHTML = data['coordinates'][i][0];
          td.style = 'text-align:left';
          tr.appendChild(td);
          for (var j=1; j<4; j++) {
            var td = document.createElement('td');
            td.innerHTML = data['coordinates'][i][j];
            tr.appendChild(td);
          }
          fragment.appendChild(tr);
        }
        table.appendChild(fragment);
        target.append(table);
      });
    }
  });
});
