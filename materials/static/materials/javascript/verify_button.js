'use strict';

for (let element of document.getElementsByClassName('verify-button')) {
  element.addEventListener('click', function() {
    if (confirm('Have you verified the correctness of the data?')) {
      window.open(this.getAttribute('data-reverse-url'), '_top');
    }
  });
}
