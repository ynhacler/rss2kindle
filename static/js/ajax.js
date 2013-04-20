

jQuery.fn.formToDict = function() {
    //将字典的表单弄成json对象
    var fields = this.serializeArray()
    var json = {}
    for (var i = 0; i < fields.length; i++) {
        json[fields[i].name] = fields[i].value
    }

    return json
}

jQuery.fn.disable = function() {
    this.enable(false)
    return this
}

jQuery.fn.enable = function(opt_enable) {
    if (arguments.length && !opt_enable) {
        this.attr("disabled", "disabled")
    } else {
        this.removeAttr("disabled")
    }
    return this
}


function getHttpObject(){
	//判断浏览器支持的XMLHTTP对象，并返回。
	//不支持则放回false
	if(typeof XMLHttpRequest=="undefined"){
		try {return new ActiveXObject("Msxml2.XMLHTTP.6.0")}
		catch(e){}
		try {return new ActiveXObject("Msxml2.XMLHTTP.3.0")}
		catch(e){}
		try {return new ActiveXObject("Msxml2.XMLHTTP")}
		catch(e){}						
		return false
		}
	else{
		return new XMLHttpRequest()
		}
}
//__EOF__getHttpObject

function countClass(className){
	//ie8和更老的ie不支持getElementsByClassName
	return document.getElementsByClassName(className).length
}
//__EOF__countNote



function showNewContent(html, anchor){
    if(html){
	    document.getElementById(anchor).insertAdjacentHTML("beforebegin",html);
            $('#'+anchor).remove();
	}
}
//__EOF__showNewContent

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}
//__EOF__getCookie

function loadNewConten(url, eid){
	args=new Object()
	args.eid = eid
	args._xsrf=getCookie('_xsrf')
        anchor = 'load_' + eid
	$.post(url,
			$.param(args),
			function(data){showNewContent(data, anchor)},
			'json'				
	)
	//EOF__$.post
}
//__EOF__loadNewConten
