'use strict';

for (let element of document.getElementsByClassName('delete-button')) {
  element.addEventListener('click', function() {
    if (confirm(
      'Are you sure you want to remove this data set from the ' +
      'database?')) {
      window.open(this.getAttribute('data-reverse-url'), '_top');
    }
  });
}
