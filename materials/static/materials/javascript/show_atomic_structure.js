'use strict';

for (let element of document.getElementsByClassName('expand-hide-button')) {
  element.addEventListener('click', function() {
    const target =
      document.getElementById(element.dataset.target.split('#')[1]);
    if (target.id.startsWith('atomic-coordinates-body-') &&
        target.innerHTML === '') {
      const series_id = target.id.split('atomic-coordinates-body-jsmol-')[1]
                     || target.id.split('atomic-coordinates-body-')[1];
      axios
        .get('/materials/get-atomic-coordinates/' + series_id)
        .then(response => {
          let data = response['data'];
          let table = document.createElement('table');
          table.className = 'table-atomic-coordinates';
          let tr, td;
          for (let vector of data['vectors']) {
            tr = document.createElement('tr');
            td = document.createElement('td');
            td.innerHTML = 'lattice_vector';
            td.style = 'text-align:left';
            tr.append(td);
            for (let vector_comp of vector) {
              td = document.createElement('td');
              td.innerHTML = vector_comp;
              tr.append(td);
            }
            table.append(tr);
          }
          target.append(table);
          let coord_type;
          if (data['coord-type'] == 'atom_frac') {
            coord_type = 'atom_frac';
          } else {
            coord_type = 'atom';
          }
          table = document.createElement('table');
          table.className = 'table-atomic-coordinates';
          for (let coordinate of data['coordinates']) {
            tr = document.createElement('tr');
            td = document.createElement('td');
            td.innerHTML = coord_type;
            tr.append(td);
            for (let i=1; i<4; i++) {
              td = document.createElement('td');
              td.innerHTML = coordinate[i];
              tr.append(td);
            }
            td = document.createElement('td');
            td.style = 'text-align:left';
            td.innerHTML = coordinate[0];
            tr.append(td);
            table.append(tr);
          }
          target.append(table);
        });
    }
  });
}
