$(function() {
  $("#search").keyup(function() {
    console.log($('#search').val());
    $.ajax({
      type: "POST",
      url: "/materials/ajax-search",
      data: {
          'search_text': $('#search').val(),
          'csrfmiddlewaretoken': $("input[name=csrfmiddlewaretoken]").val()
      },
      success: searchSuccess,
      dataType: 'html'
    });
  });
});

function searchSuccess(data, textStatus, jqXHR)
{
    $('#search-results').html(data);
}
