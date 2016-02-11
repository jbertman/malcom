$(function(){

	var url = $("#query").data('url');

	$("#query").keydown(function (event) {
		if (event.which == 13) {
			event.preventDefault();
			get_dataset($('#query').val(), url);
		}
	});

	get_dataset("", url);
	get_tags();
});


function clear_db() {
	var r=confirm("You sure?");
	if (r==true)
	  {
	 	document.location.href=url_static_prefix+'dataset/clear';
	  }
}

function dataset_remove(id) {
	$.ajax({
		dataType: "json",
		url: url_static_prefix+'api/dataset/remove/',
		data: {'_id': id},
		success:function(data){
			if (data['n'] == 1)
				$('#row_'+id).remove()
			else
				console.log("ERROR: Could not remove element "+id)
		}
	});
}

function get_dataset_csv(query, url) {
	queries = query.split(' ');
	querydict = {};

	for (var i in queries) {
		splitted = queries[i].split('=')
		if (splitted.length > 1)
			querydict[splitted[0]] = splitted[1];
		else if (splitted[0] != "")
			querydict['value'] = splitted[0]
	}

	if ($('#regex').prop('checked') == true)
		querydict['regex'] = 'true'

	url = url_static_prefix + url +"?"+ $.param(querydict)

	location.href = url
}

function change_page(arg, url) {
	console.log('Loading page ' + arg)
	query = $('#query').val()
	location.hash = arg
	get_dataset(query, url)
}

function get_tags() {
	t = $("#tag-table")

	$.ajax({
		dataType: "json",
		type: "GET",
		url: t.data('source'),
		success: function(data) {
			for (var i in data) {
				row = $("<tr><td><span class='label label-tag-"+data[i]['name']+"' data-tag='"+data[i]['name']+"'>"+data[i]['name']+"</span></td><td>"+data[i]['count']+"</td></tr>")
				$('.label', row).click(function(){
					get_dataset('tags='+$(this).data('tag'), $("#dataset-search").data('source'));
				})
				t.append(row)
			}
		}
	});



}

function get_dataset(query, url) {

	queries = query.split(' ');
	querydict = {};

	for (var i in queries) {
		splitted = queries[i].split('=')
		if (splitted.length > 1)
			querydict[splitted[0]] = splitted[1];
		else if (splitted[0] != "")
			querydict['value'] = splitted[0]
	}

	// un # dans l'url
	page = location.hash.split("#")[1]
	if (page == undefined) {
		page = 0;
	}

	regex = false;
	if ($('#regex').prop('checked') == true)
		regex = 'true'

	$.ajax({
	  dataType: "json",
	  type: 'GET',
	  url: url,
	  data: {query: JSON.stringify(querydict), page: page, regex: regex},
	  beforeSend: function(data) {
	  	$('#loading-spinner').addClass('show')
	  },
	  complete: function(data) {
	  	$('#loading-spinner').removeClass('show')
	  },
	  success: function(data){
	  	// empty the table and populate it
	  	dataset = $('#dataset')
	  	dataset.empty()
	  	head = $("<tr>")
	  	// get the headers
	  	for (var i in data.fields) {
	  		h = $("<th>").text(data.fields[i][1])
	  		if (['date_created', 'date_updated', 'last_analysis', 'date_first_seen', 'date_last_seen'].indexOf(data.fields[i][0]) != -1)
	  			h.addClass('timestamp')
	  		head.append(h)
	  	}

	  	head.append($("<th>").text(''))

	  	dataset.append(head)

	  	// loop over the elements

	  	for (var i in data.elements) {
	  		elt = data.elements[i]
	  		tags_links = new Array()
	  		//create row
	  		row = $("<tr id='row_"+elt['_id']['$oid']+"'></tr>")
	  		for (var key in data.fields) {
	  				k = data.fields[key][0]
	  				v = elt[k]
	  				if (v == "" || v == undefined)
	  					row.append($("<td />").text('-'))
	  				else if (k == 'tags')
	  					row.append($("<td />").append(display_tags(v)))
	  				else if (['date_created', 'date_updated', 'last_analysis', 'date_first_seen', 'date_last_seen'].indexOf(k) != -1)
	  					row.append($("<td />").text(format_date(new Date(v.$date))).addClass('timestamp'))
	  				else if (k == 'value') {
	  					l1 = $("<a class='graphicon' href='"+url_static_prefix+"nodes/value/"+encodeURIComponent(v)+"'><span class='glyphicon glyphicon-map-marker' aria-hidden='true'></span></a>")
	  					l2 = $('<a href="'+url_static_prefix+'search/?query='+v+'">'+v+'</a>')
	  					row.append($("<td class='value'></td>").append(l1).append(l2))
	  				}
	  				else
	  					row.append("<td>"+v+"</td>")
	  		}

	  		row.append("<td><span class='glyphicon glyphicon-remove' onclick='javascript:dataset_remove(\""+elt['_id']['$oid']+"\")'></span></td>")

	  		tags_links = row.find('.tags_links')

	  		for (var c in elt['tags']) {
	  			a = $('<a>')
	  			a.attr('href', url_static_prefix+'nodes/tags/'+elt['tags'][c])
	  			a.text(elt['tags'][c])
	  			if (c != 0)
	  				tags_links.append(', ')
	  			tags_links.append(a)
	  		}

	  		// append the created row to the table
	  		dataset.append(row)
	  	}

	  	// adjust pagination
	  	per_page = 50;
	  	if (data.total_results != 'many')	{
		  	total_pages = Math.floor(data.total_results / per_page) + 1;
		  	next_page = (page*1+1) <= total_pages ? page*1 + 1 : page*1;
	  	}
	  	else {
	  		total_pages = 'many';
	  		next_page = page*1+1;
	  	}
	  	previous_page = page - 1 >= 0 ? page - 1 : 0;


	  	prev = $("#pagination-prev")
	  	next = $("#pagination-next")
	  	$("#pagination-page").text("Page "+(page*1+1)+" of "+ (total_pages))
	  	$("#total-results").text(data.total_results)

	  	prev.attr('data-nav', previous_page)
	  	next.attr('data-nav', next_page)
	  }
	});

}

