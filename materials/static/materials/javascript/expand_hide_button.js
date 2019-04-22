/* Change "click to expand" to "click to hide" and vice versa */
Array.from(document.getElementsByClassName('expand-hide-button')).forEach(function(element) {
  element.addEventListener('click', function() {
    var text = this.innerText;
    if (text.includes('expand)')) {
      this.innerText = text.split('expand)')[0] + 'hide)';
    } else {
      this.innerText = text.split('hide)')[0] + 'expand)';
    }
  });
});
