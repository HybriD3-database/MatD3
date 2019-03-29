/* Change "click to expand" to "click to hide" and vice versa */
$('.expand-hide-button').click(function() {
  if ($(this).html().includes('expand)')) {
    $(this).html($(this).html().split('expand)')[0] + 'hide)');
  } else {
    $(this).html($(this).html().split('hide)')[0] + 'expand)');
  }
});
