function plot_data(element, data, x_property, x_unit, y_property, y_unit, series_label) {
  var ctx = document.getElementById(element).getContext('2d');
  var chart = new Chart(ctx, {
    type: 'scatter',
    data: {
      datasets: [
        {
          label: series_label,
          backgroundColor: 'rgba(0,0,0,0)',
          borderColor: 'blue',
          data: data
        },
      ]
    },
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

$('canvas').each(function() {
  var plot_id = $(this).attr('id');
  var plot_pk = plot_id.split('_')[1];
  $.getJSON('/materials/data-for-chart/' + plot_pk, function(response) {
    plot_data(plot_id, response['data'],
              response['secondary-property'],
              response['secondary-unit'],
              response['primary-property'],
              response['primary-unit'],
              response['series-label']);
  });
});
