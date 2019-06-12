'use strict';

for (let table_body of
  document.querySelectorAll('tbody[class="tabulated-data"]')) {
  const subset_pk = table_body.id.split('-')[1];
  axios.get('/materials/get-subset-values/' + subset_pk)
       .then(response => {
         let data = response['data'];
         const table = document.createElement('table');
         const fragment = document.createDocumentFragment();
         for (let value of data) {
           let tr = document.createElement('tr');
           let td = document.createElement('td');
           if ('x' in value) {
             td.innerHTML = value['x'];
             tr.appendChild(td);
           }
           td = document.createElement('td');
           td.innerHTML = value['y'];
           tr.appendChild(td);
           fragment.appendChild(tr);
         }
         table_body.append(fragment);
       });
}
