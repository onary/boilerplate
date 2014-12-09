$(function () {
	$('.admin-delete').on('click', function() {
		$.ajax({
			url: $(this).data().url,
			type: 'DELETE',
			contentType: "application/json; charset=utf-8",
			success: function(result) {
				window.location.href = result;
			}
		});
	});
});
