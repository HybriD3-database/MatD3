'use strict';

function plot_data(element, data, x_property, x_unit, y_property, y_unit) {
  const ctx = document.getElementById(element).getContext('2d');
  const datasets = [];
  const colors = [
    'rgb(89,112,216)', 'rgb(100,194,78)', 'rgb(162,88,201)', 'rgb(175,182,56)',
    'rgb(210,71,153)', 'rgb(80,144,44)', 'rgb(202,141,217)', 'rgb(75,189,128)',
    'rgb(211,68,88)', 'rgb(77,191,183)', 'rgb(208,88,49)', 'rgb(94,152,211)',
    'rgb(214,155,70)', 'rgb(122,94,160)', 'rgb(153,178,109)', 'rgb(156,69,98)',
    'rgb(58,128,80)', 'rgb(223,131,154)', 'rgb(116,115,42)', 'rgb(170,106,64)'
  ]
  for (let i = 0; i < data.length; i++) {
    datasets.push({
      label: data[i]['subset-label'],
      backgroundColor: 'rgba(0,0,0,0)',
      borderColor: colors[i],
      data: data[i]['values']
    });
  }
  const chart = new Chart(ctx, {
    type: 'scatter',
    data: {datasets: datasets},
    options: {
      scales: {
        xAxes: [{
          type: 'linear',
          scaleLabel: {
            display: true,
            labelString: x_property + ', ' + x_unit,
            fontSize: 14,
          },
        }],
        yAxes: [{
          type: 'linear',
          scaleLabel: {
            display: true,
            labelString: y_property + ', ' + y_unit,
            fontSize: 14,
          },
        }]
      }
    }
  });
}

for (let element of document.getElementsByTagName('canvas')) {
  const plot_id = element.id;
  const plot_pk = plot_id.split('_')[1];
  axios
    .get('/materials/data-for-chart/' + plot_pk)
    .then(response => {
      plot_data(plot_id, response['data']['data'],
                response['data']['secondary-property'],
                response['data']['secondary-unit'],
                response['data']['primary-property'],
                response['data']['primary-unit']);
    });
}
