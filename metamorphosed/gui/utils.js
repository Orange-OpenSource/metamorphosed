
var visible_divselectors = {};

function ToggleDiv(selector, togglebutton) {
	if ($(selector).is(":visible")) {
		$(selector).hide();
		$(togglebutton).empty();
		$(togglebutton).append("+");
		visible_divselectors[selector] = false;
	} else {
		$(selector).show();
		$(togglebutton).empty();
		$(togglebutton).append("&#8210;");
		//"&ndash;");
		visible_divselectors[selector] = true;
	}
}

function downloadSVG(svgelem, ident, sentnum) {
	// download the generated svg to use elsewhere (e.G. transform to pdf with inkscape)
	var svg = document.getElementById(svgelem);
	/* TODO add here in to svg/defs:
	 <style type="text/css"><![CDATA[
	 ... content onf current css ...
	 ]]></style>
	 */
	var data = new Blob([svg.innerHTML]);
	var a2 = document.getElementById(ident);
	a2.href = URL.createObjectURL(data);
	a2.download = "graph_" + sentnum + ".svg";
}

function ToggleSVGExport() {
	if ($("#svgexport").is(":visible")) {
		$("#svgexport").hide();
	} else {
		$("#svgexport").show();
		$("#svgexport").draggable();
		$("#cancelsvgexport").click(function () {
			$("#svgexport").hide();
		});
	}
}

/*
function ToggleHelp() {
	if ($("#helptext").is(":visible")) {
		$("#helptext").hide();
	} else {
		$("#helptext").show();
	}
}*/

function highlight_pm(amr) {
    var output = amr.replace(/("[^\"]+")/g, '<span class="literal">$1</span> '); // " // hightlight strings
    output = output.replace(/(:quant|:value|:op[0-9]) ([a-z0-9\.]+)/g, '$1 <span class="literal">$2</span> '); // highlight non-string literals
    output = output.replace(/([a-z]+[a-z0-9]*) \//g, ' <span class="conceptslash">$1</span> <b>/</b>'); // highlight variables
    output = output.replace(/:([ARGa-z0-9-]+[0-9]?)/g, ' <span class="$1text">:$1</span>'); //  highlight relations

    return output;
}


function updateExportFormat() {
	// check also here to improve download mechanism: https://codepen.io/chrisdpratt/pen/RKxJNo
	//$("#exporthref")[0].href="/graphs/amrgraphs.zip?format=" + obj.value;
	$("#exporthref")[0].href = "/graphs/amrgraphs.zip?format=" + $('input:radio[name=graphformat]:checked').val()
		+ "&sentences=" + $("#sentnumlist").val().trim();

	var conceptlist = $("#conceptlist").val().trim();
	if (conceptlist) {
		$("#exporthref")[0].href += "&concepts=" + conceptlist;
	}
}

function ShowSentences() {
	if ($("#sentmodal").is(":visible")) {
		$("#sentmodal").hide();
	} else {
		$("#sentmodal").show();
		$("#cancelsentlist").click(function () {
			//$("#conceptsetmodal").fadeOut();
			$("#sentmodal").hide();
		});
	}
}

function ToggleDirection() {
	if ($("#gresultat").css("flexDirection") == "row") {
		$("#gresultat").css("flexDirection", "column");
	} else {
		$("#gresultat").css("flexDirection", "row");
	}
}

function unhighlight() {
	// delete boxhighlight class from all word rectangles
	$("polygon").each(function (index) {
		// get all node rectangles, and delete highlighting (boxhighlight) class
		var currentclasses = $(this).attr("class");
		$(this).attr("class", null);
	});
}

function getAncestor(element) {
	//console.log("element id:", element.id, "class:", element.getAttribute("class"));
	if (element.nodeName == "svg"
		|| element.getAttribute("class") === "node"
		|| element.getAttribute("class") === "edge") {
		return element;
	} else {
		return getAncestor(element.parentNode);
	}
}
