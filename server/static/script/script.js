// Append PUT and DELETE methods à la jquery
//
jQuery.each( [ "PUT", "DELETE" ], function( i, method ) {
	jQuery[ method ] = function( url, data, callback, type ) {
		// shift arguments if data argument was omitted
		if ( jQuery.isFunction( data ) ) {
			type = type || callback;
			callback = data;
			data = undefined;
		}

		return jQuery.ajax({
			type: method,
			url: url,
			data: data,
			success: callback,
			dataType: type
		});
	};
} );



jQuery(document).ready( function() {
  jQuery(".button").click( function() {
    var input_string = $$("input#textfield").val();
    jQuery.ajax({
      type: "POST",
      data: {textfield : input_string},
      success: function(data) {
        jQuery('#foo').html(data).hide().fadeIn(1500);
      },
    });
    return false;
  });

  jQuery("button").click(query_server);

  $('input#search').keypress(function(e){
    if(e.which == 13){
      e.preventDefault();
      query_server();
    }
  });
});

function query_server() {
  var search = $("#search").val();
  var url = "/entity/" + search;// + "/param";
  $.get(url, show_entity, "json");
}


function render_parameters(e) {
  return e.param;
}

function render_parameters_delayed(e) {
  return "";/*\
              <input type='button' value='get' id='lkj' name='lkj' \
              onclick='$.ajax({
              type: \"GET\",
              dataType: \"json\",
              url: \"/entity/\" + e.id + "/param\",
              success: function(res) { $(\".p\").html(render_parameters(res)); }
              });'/>\
              ";*/
}

$(".DELETE").live("click", function() {
  var id = $(this).data("element-id");
  var elem = $(this)
  delete_entity(id).success( function() { 
    $(".data-element-" + id).hide();
    elem.hide()
  });
});

function delete_entity(id) {
  return $.DELETE("/entity/" + id);
}

function render_entity(e, expanded) {
  return "<div class='entity data-element-" + e.id + "'>" +
    "<span>" + e.id + "</span> " +
    "<span>" + e.type + "</span> " +
    "<span class='p'></span>" +
    (expanded
     ? render_parameters(e)
     : render_parameters_delayed(e)) +
    "<a class='DELETE' data-element-id='" + e.id + "'>delete</a>" +
    "</div>"
}

function show_entity(result){
  show_result(render_entity(result, false));
}

function show_result(result) {
  $('#result').html(result);
  $('.entity').hide().fadeIn(300);
}

