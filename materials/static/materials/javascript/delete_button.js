Array.from(document.getElementsByClassName('delete_button')).forEach(function(element) {
  element.addEventListener('click', function() {
    if (confirm('Are you sure you want to remove this data set from the database?')) {
      window.open(this.getAttribute('data-reverse-url'), '_top');
    }
  });
});
