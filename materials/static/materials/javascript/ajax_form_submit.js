function ajax_submit(form, feedback) {
    form.on('submit', function(event){
        event.preventDefault();
        var data = new FormData(form.get(0));
        $.ajax({
            url: form.attr('action'),
            type: form.attr('method'),
            data: data,
            cache: false,
            processData: false,
            contentType: false,
            success: function(data) {
                feedback.html(data);
            },
            error: function(error) {
                feedback.html(
                    "<p class=\"alert alert-danger\">Something went wrong, please <a class=\"alert-link\" href=" + window.location.href + ">refresh</a> the page and try again.</p>"
                );
            },
        })
    });
}