function plot_data(element, data, x_property, x_unit, y_property, y_unit) {
    var ctx = document.getElementById(element).getContext('2d');
    var chart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: '',
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
