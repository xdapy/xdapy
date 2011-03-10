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
});
