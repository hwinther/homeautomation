//these should perhaps be loaded via base.html instead of this particular view
var focused = true;

window.onfocus = function() {
    focused = true;
};
window.onblur = function() {
    focused = false;
};

$(window).load(function() {
	$(".se-pre-con").fadeOut("slow");
});

$('.container').shapeshift();
$('.container2').shapeshift();

$( document ).ready(function() {
	
	function getCookie(name) {
		var cookieValue = null;
		if (document.cookie && document.cookie != '') {
			var cookies = document.cookie.split(';');
			for (var i = 0; i < cookies.length; i++) {
				var cookie = jQuery.trim(cookies[i]);
				// Does this cookie string begin with the name we want?
				if (cookie.substring(0, name.length + 1) == (name + '=')) {
					cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
					break;
				}
			}
		}
		return cookieValue;
	}
	var csrftoken = getCookie('csrftoken');

	function csrfSafeMethod(method) {
		// these HTTP methods do not require CSRF protection
		return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
	}
	$.ajaxSetup({
		beforeSend: function(xhr, settings) {
			//if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
				xhr.setRequestHeader("X-CSRFToken", csrftoken);
			//}
		}
	});
	
	function updateWithJsonState(json)
	{
		//console.log('updateWithJsonState: ' + json);
		
		//console.log('json.HACec: ' + json['HACec']);
		//console.log('json.HAPhilipsHue: ' + json.HAPhilipsHue);
		
		if (typeof json.HACec !== "undefined") {
			for (var i=0; i < json.HACec.cecdevices.length; i++)
			{
				var dev = json.cecdevices[i];
				//console.log(dev);
				if (dev.PowerStatus == true) {
					html = html + '<li>' + dev.Name + ' ' + '<a href="javascript:CallWS(\'/cec/standby/' + i + '\');">Off</a></li>';
				}
				else {
					html = html + '<li>' + dev.Name + ' ' + '<a href="javascript:CallWS(\'/cec/power_on/' + i + '\');">On</a></li>';
				}
			}
			$('#cecdevices').html(html);
		}
		
		if (typeof json.HAPhilipsHue !== "undefined") {
			// console.log('updating lights - ' + json.HAPhilipsHue.lights.length);
			var html = '';
							
			for (var i=0; i < json.HAPhilipsHue.lights.length; i++)
			{
				//console.log(json.HAPhilipsHue.lights[i]);
				var light = json.HAPhilipsHue.lights[i];
				
				html = html + '<div class="ui-grid-a" id="lightgridinner">';
				html = html + '<div class="ui-block-a">';
				html = html + '	<input type="checkbox" id="chkLight-' + light.name + '" name="chkLight-' + light.name + '" class="chkLights">';
				html = html + '	<label for="chkLight-' + light.name + '">' + light.name + '</label>';
				html = html + '</div>';
				html = html + '<div class="ui-block-b">';
				html = html + '	<select name="flip-' + light.name + '" id="flip-' + light.name + '" class="flipadelphia2" data-role="slider" data-mini="true" data-arg-a="' + light.name + '">';
				if (light.on == true) {
					html = html + '			<option value="off">Off</option>';
					html = html + '			<option value="on" selected>On</option>';
				} else {
					html = html + '			<option value="off" selected>Off</option>';
					html = html + '			<option value="on">On</option>';
				}
				html = html + '	</select>';
				html = html + '</div>';
				html = html + '</div><!-- /grid-a -->';
			}

			html = html + '<script type="text/javascript">';
			//html = html + '$("#lightgridinner").update();';
			html = html + "	$('.flipadelphia2').change(function(event) {";
			html = html + "event.stopPropagation();";
			html = html + "var myswitch = $(this);";
			//html = html + "window.myswitch = $(this);";
			html = html + "var show     = myswitch[0].selectedIndex == 1 ? true:false;";
			html = html + "var name = myswitch.data('arg-a');";
			html = html + "var url = '/philipshue/setState/' + name + '/' + show;";
			html = html + "console.log(url);";
			html = html + "window.CallWS(url);";
			html = html + "});";
			html = html + '</script>';
			
			$('#lightgrid').empty();
			$('#lightgrid').append(html).trigger('create');
		}
	}
	
	//this will poll our jsonp function starting once the page is ready and then again every 10 seconds, unless the page is out of focus
	(function poll() {
		//console.log("poll focused=" + focused);
		if (focused) {
		//setTimeout(function() {
			$.ajax({
			   type: 'GET',
				url: location.protocol + '//' + location.host + ':8080/state/',
				async: false,
				jsonpCallback: 'c'+Math.floor((Math.random()*100000000)+1),
				contentType: "application/json",
				dataType: 'jsonp',
				success: updateWithJsonState,
				error: function(e) {
				   console.log(e.message);
				},
				complete: setTimeout(function() {poll()}, 10000), //poll,
				timeout: 2000
			});
		//}, 5000);
		}
		else {
			//window not in focus, wait a longer period before trying again
			//not sure if this will cause issues with the javascript function call stack in the long run..
			setTimeout(function() {poll()}, 20000);
		}
	})();
	
	function manualPoll() {
		$.ajax({
		   type: 'GET',
			url: location.protocol + '//' + location.host + ':8080/state/',
			async: false,
			jsonpCallback: 'c'+Math.floor((Math.random()*100000000)+1),
			contentType: "application/json",
			dataType: 'jsonp',
			success: updateWithJsonState,
			error: function(e) {
			   console.log(e.message);
			},
			timeout: 2000
		});
	}
	
	function CallWS(URL) {
		$.ajax({
		   type: 'GET',
			url: location.protocol + '//' + location.host + ':8080' + URL,
			async: false,
			jsonpCallback: 'c'+Math.floor((Math.random()*100000000)+1),
			contentType: "application/json",
			dataType: 'jsonp',
			success: updateWithJsonState,
			error: function(e) {
			   console.log(e.message);
			},
			timeout: 2000
		});
	}
	window.CallWS = CallWS;
	
	function loadSchema() {
		$.ajax({
		   type: 'GET',
			url: location.protocol + '//' + location.host + ':8080/schema/',
			async: false,
			jsonpCallback: 'c'+Math.floor((Math.random()*100000000)+1),
			contentType: "application/json",
			dataType: 'jsonp',
			success: function(json) {
				for(var i=0; i < json.Schema.length; i++)
				{
					var wsdi = json.Schema[i];
					var availablecontrols = $('#AvailableControls');
					if (wsdi.Enums.hasOwnProperty('key'))
					{
						window.wsdi = wsdi; //only for testing.. global var
					}
					
					if (//$('.' + wsdi.Name).length == 0 
						typeof $('#AvailableControls').prop('id') !== 'undefined'
						//&& wsdi.Enums.length != 0
						)
					{
						//this control is not in the DOM right now, lets add it to the AvailableControls collection
						/*$.each(wsdi.Enums, function (key, value) {
							console.log('key=' + key + ' value=' + value);
							console.log(value);
							$.each(value, function (innerkey, innervalue) {
								console.log('innerkey=' + innerkey + ' innervalue=' + innervalue);
							});
						});*/
						var availablecontrols_updated = false;
						for (var key in wsdi.Enums) {
							if (wsdi.Enums.hasOwnProperty(key)) {
								for (var valuekey in wsdi.Enums[key]) {
									if (wsdi.Enums[key].hasOwnProperty(valuekey)) {
										var currentEnumValue = wsdi.Enums[key][valuekey];
										var controlExists = false;
										$('.' + wsdi.Name).each(function() {
											var dataArgA = $(this).data('arg-a');
											if (typeof dataArgA !== 'undefined' && dataArgA == valuekey)
												controlExists = true;
										});
										//console.log(wsdi.Name + " " + valuekey + " - " + currentEnumValue + " exists? " + controlExists);
										if (controlExists == false)
										{
											var controlhtml = '<div class="citem"><a href="#" class="' + wsdi.Name + ' myButton" data-arg-a="' + valuekey + '"><span style="font-size: 8px">(' + wsdi.Name + ')</span> ' + currentEnumValue + '</a></div>';
											availablecontrols.append(controlhtml);
											availablecontrols_updated = true;
										}
									}
								}
							}
						}
						
						if (availablecontrols_updated) {
							$('.container').shapeshift();
						}
					}
					
					$('.' + wsdi.Name).prop('data-url', wsdi.URL)
					$('.' + wsdi.Name).click(function() {
						var url = $(this).prop('data-url');
						var argValue = '';
						var letters = 'abcdefghijklmnopqrstuvwxyz';
						var argLetterUsed = false;
						for(var j=0; j < letters.length; j++)
						{
							argValue = $(this).data('arg-' + letters[j]);
							if (typeof argValue !== "undefined")
							{
								if (j == 0) {
									url = url + argValue;
									argLetterUsed = true;
								}
								else
								{
									url = url + '/' + argValue;
									argLetterUsed = true;
								}
							}
							else {
								break;
							}
						}

						var inputname = $(this).data('arg-related-input');
						var selectname = $(this).data('arg-related-select');
						var functionname = $(this).data('arg-related-function');
						if (typeof inputname !== 'undefined')
						{
							argValue = $('#'+inputname).val();
							//console.log('fetched data from input element ' + inputname + ' value ' + argValue);
							if (url.slice(-1) != '/') url = url + '/';
							url = url + argValue;
						}
						if (typeof selectname !== 'undefined')
						{
							argValue = $('#'+selectname).val();
							//console.log('fetched data from select element ' + selectname + ' value ' + argValue);
							if (url.slice(-1) != '/') url = url + '/';
							url = url + argValue;
						}
						if (typeof functionname !== 'undefined')
						{
							jQuery.globalEval( 'var retVal = ' + functionname + ';' );
							//console.log('fetched data from function ' + functionname + ' value ' + retVal);
							if (url.slice(-1) != '/') url = url + '/';
							url = url + retVal;
						}

						//console.log('CallWS(' + url + ')');
						CallWS(url);
						return false;
					});
				}
			},
			//success: updateWithJsonState,
			error: function(e) {
			   console.log(e.message);
			},
			timeout: 2000
		});
	}
	loadSchema(); //load them on document.ready
	
});
