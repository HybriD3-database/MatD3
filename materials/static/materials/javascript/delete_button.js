$('.delete_button').click(function() {
  if (confirm('Are you sure you want to remove this data set from the database?')) {
    window.open($(this).attr('data-reverse-url'), '_top');
  }
});
