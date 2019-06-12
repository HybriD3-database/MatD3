'use strict';

// Change "click to expand" to "click to hide" and vice versa
for (let element of document.getElementsByClassName('expand-hide-button')) {
  element.addEventListener('click', function() {
    const text = this.innerText;
    if (text.includes('expand)')) {
      this.innerText = text.split('expand)')[0] + 'hide)';
    } else {
      this.innerText = text.split('hide)')[0] + 'expand)';
    }
  });
}
