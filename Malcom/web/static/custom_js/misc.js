$(
	function navigation_highlight() {
		section = location.href.split(url_static_prefix)[1].split('/')[0];
		$('#'+section+"-nav").addClass('active');


		$(".toggle-control").each(function(){
			$(this).prepend("<span class='glyphicon glyphicon-chevron-right'></span> ")
		});

		$(".toggle-control").click(function(event) {
			event.preventDefault();
			target_id = $(this).data('toggle-target');
			$("#"+target_id).toggle();
			i = $(this).find('span.glyphicon');
			i.toggleClass('glyphicon-chevron-right');
			i.toggleClass('glyphicon-chevron-down');
		})
});



function format_date(date, millis)
{
	// hours part from the timestamp
	var hours = date.getHours() < 10 ? '0' + date.getHours() : date.getHours();
	// minutes part from the timestamp
	var minutes = date.getMinutes() < 10 ? '0' + date.getMinutes() : date.getMinutes()
	// seconds part from the timestamp
	var seconds = date.getSeconds() < 10 ? '0' + date.getSeconds() : date.getSeconds()
	if (millis == true) {
		m = date.getMilliseconds()
		if (m < 10)
			m = "00"+m
		if (m > 10 && m < 100)
			m = "0"+m
		seconds += "." + m
	}

	var day = date.getDate() < 10 ? '0' + date.getDate() : date.getDate()
	var month = date.getMonth()+1 < 10 ? '0' + (date.getMonth()+1) : (date.getMonth()+1)
	var year = date.getFullYear();

	// will display time in 10:30:23 format
	var formattedTime = year+"-"+month+"-"+day +" ("+hours + ':' + minutes + ':' + seconds+")";

	return formattedTime;
}

function display_tags(tags) {
  out = ""

  for (i in tags) {
    tag = tags[i]
    out += '<span class="label label-tag-'+tag+'">'+tag+'</span>';
  }

  if (tags.length == 0) {
    out = '<span class="label label-default">N/A</span>';
  }

  return out;
}



