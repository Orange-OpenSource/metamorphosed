/*
 This library is under the 3-Clause BSD License

 Copyright (c) 2022-2025,  Orange
 All rights reserved.

 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions are met:
	* Redistributions of source code must retain the above copyright
	  notice, this list of conditions and the following disclaimer.

	* Redistributions in binary form must reproduce the above copyright
	  notice, this list of conditions and the following disclaimer in the
	  documentation and/or other materials provided with the distribution.

	* Neither the name of Orange nor the
	  names of its contributors may be used to endorse or promote products
	  derived from this software without specific prior written permission.

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 DISCLAIMED. IN NO EVENT SHALL ORANGE BE LIABLE FOR ANY
 DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

 SPDX-License-Identifier: BSD-3-Clause
 Software Name: MetAMoRphosED AMR-Editor
 Author: Johannes Heinecke
*/

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
    //output = output.replace(/:([ARGa-z0-9-]+[0-9]?)/g, ' <span class="$1text">:$1</span>'); //  highlight relations
	output = output.replace(/:([ARGa-z0-9-]+[0-9]?)/g, function(match, p1) { return ' <span class="' + p1.replace("-of", "") + 'text">:'+ p1 + '</span>'}); //  highlight relations

    return output;
}


function updateExportFormat() {
	// check also here to improve download mechanism: https://codepen.io/chrisdpratt/pen/RKxJNo
	//$("#exporthref")[0].href="/graphs/amrgraphs.zip?format=" + obj.value;
	$("#exporthref")[0].href = "/graphs/amrgraphs.zip?format=" + $('input:radio[name=graphformat]:checked').val()
		+ "&sentences=" + $("#sentnumlist").val().trim()
		+ "&withalignments=" + $('input[name=alsoalign]').is(':checked');

	//console.log("GGGGG", $('input[name=alsoalign]').is(':checked'));
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
