function filter_form(search_field, selector) {
    search_field.on('keyup', function() {
        var search_term = $(this).val().toLowerCase();
        if (search_term != '') {
            search_term = search_term.split('').reduce(function(a,b) {
                return a+'[^'+b+']*'+b;
            });
        }
        var pattern = new RegExp(search_term);
        var default_set = false;
        selector.children().filter(function() {
            var matching = pattern.test($(this).text().toLowerCase());
            $(this).toggle(matching);
            if (!default_set && matching) {
                selector.val($(this).attr('value'));
                default_set = true;
            }
        });
    });
}
