/* http://developer.mozilla.org/en/docs/AJAX:Getting_Started */
function ajaxRequest(url, data, func, mimeType){
	let xhr = null;

	/* Create an XMLHTTP instance */
	if(window.XMLHttpRequest){ /* Mozilla, Safari, ... */
		xhr = new XMLHttpRequest();
		if(xhr.overrideMimeType)
			/* Some web servers return a non-standard mime type. */
			xhr.overrideMimeType(mimeType || 'text/html');
	}else
	if(window.ActiveXObject){ /* IE */
		try{
			xhr = new ActiveXObject('Msxml2.XMLHTTP');
		}
		catch(e){
		try{
			xhr = new ActiveXObject('Microsoft.XMLHTTP');
		}
		catch(e){}
		}
	}
	if(!xhr){
		alert('Cannot create an XMLHTTP instance.');
		return;
	}

	/* This function has no arguments. */
	xhr.onreadystatechange = function(){
		if(xhr.readyState != 4)
			return;
		if(func)
			func(xhr);
	}

	let method = data == null ? 'GET' : 'POST';

	/* xhr.open(method, url, asynchronous) */
	xhr.open(method, url, true);

	/* xhr.send(POST data) */
	/* required even if the method is not POST. */
	xhr.send(data);
}
