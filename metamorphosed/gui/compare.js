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


//var URL_BASE = 'http://' + window.location.hostname + ':6543/';

//console.log("AAA", window.location.hostname)

var readonly = false;
var sentenceloaded = false;
var relationlist = [];
var conceptlist = [];
var sentencelist = []

/** get information from relation extraction server */
function getServerInfo() {
	//var urlbase = 'http://' + window.location.host + ':' + $("#port").val() + '/';
	//URL_BASE = 'http://' + window.location.hostname + ':' + $("#port").val() + '/info';
	//URL_BASE = 'http://' + window.location.host + '/info';
	URL_BASE = 'info';


	$.ajax({
		url: URL_BASE,
		type: 'GET',
		data: { "withdata": true },
		headers: {
			'Content-type': 'text/plain'

		},
		statusCode: {
			400: function () {
				alert('Mauvaise requête');
			},
			500: function () {
				alert('Server not ready yet');
			}
		},
		success: function (data) {
			/** afficher comment le serveur a été lancé */
			//$('#serverinfo').empty();
			//$('#serverinfo').append('<table id="sitable">');
			//$.each(data,
			//	function (key, value) {
			//		//console.log("eee ", key, value);
			//		$('#sitable').appreferredpend('<tr id="tr_' + key + '">');
			//		$('#tr_' + key).append('<td id="td_k_' + key + '">');
			//		$('#tr_' + key).append('<td id="td_v_' + key + '">');
			//		$('#td_k_' + key).append(key);
			//		$('#td_v_' + key).append(value);
			//	});
			readonly = data.readonly;
			if (readonly) {
				$("#editing").hide();
				$("#save").hide();
				$("#mainheader").html($("#mainheader").html() + " (read-only)");
			}
			//$("#numberofsent").html(data.numsent);

			//console.log("BBB", data);
			if (data.otherfilenames.length > 0) {
				$('#compvars').empty();
				data.otherfilenames.splice(0, 0, data.filename);
				//console.log("BBB", data.comparisons);
				$.each(data.comparisons,
					function (key, value) {
						$('#compvars').append('<option value="' + value + '">' + data.otherfilenames[value[0] - 1] + " / " + data.otherfilenames[value[1] - 1]);
					});

				$.each(data.otherfilenames,
						function (key, value) {
							$('#preferred').append('<option value="' + value + '">' + value);
						});

				//$(".onlytwo").hide();
				//$(".several").show();
			/*} else {
				$("#leftfn").html(data.filename);
				$("#rightfn").html(data.otherfilenames[0]);
				$(".onlytwo").show();
				$(".several").hide();
				$('.comparisons').append('<option value="1,2">1,2'); */
			}

			//console.log("AAA", $('.comparisons').val());
			$("#version").empty();
			$("#version").append(data.version);
			$("#version2").empty();
			$("#version2").append(data.version);
			$("#apiversion").empty();
			$("#apiversion").append(data.apiversion);

			$("#hostname").empty();
			$("#hostname").append(data.hostname);
			$("#dir").empty();
			$("#dir").append(data.pwd);
			$("#cmdl").empty();
			$("#cmdl").append(data.cmdline.replaceAll("<", "&lt;").replaceAll(">", "&gt;"));

			if (data.preferred_file) {
			    $('#choosepreferred_row').show();
			    $("#preferredfile").append(data.preferred_file)
			}
			if (data.sentences) {
				sentencelist = data.sentences;
				for (var i = 0; i < data.sentences.length; ++i) {
					var optionstring = data.sentences[i][0] + ": " + data.sentences[i][1];
					if (optionstring.length > 150) {
						optionstring = optionstring.substring(optionstring, 150) + "...";
					}
					$('#sentencelist').append('<option value="' + (i + 1) + '">' + optionstring);
				}

				$("#sentencelist").change(function () {
					$("#sentnum").val($(this).val());
					$("#lire").click();
					$("#sentmodal").hide();
				});
			}
		},
		
		error: function (data) {
			// do something else
			if (data.status >= 500) {
				$('#serverinfo').empty();
				$('#serverinfo').append('Server not ready');
			} else {
				console.log("ERREUR " + data);
				alert("Server problem '" + URL_BASE + "'?");
			}
		}
	});
}

function downloadSVG(svgelem, ident, filename) {
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
	a2.download = filename;
}



var visible_divselectors = {};

function getcompval(obj) {
	// reload sentence when changing pair to be compared
	$("#lire").click();
}

function getpreferred(obj) {
	// send filename of best graph to server
	//$("#lire").click();
	URL_BASE = 'setpreferred';
	$("#resultat").empty(); // vider le div
	$.ajax({
		url: URL_BASE, // + "json", //+'/foo/fii?fuu=...',
		type: 'GET',
		data: {
			"num": $("#sentnum").val(),
			"preferred": $("#preferred").val(),
			"compare": $("#compvars").val()
		},
		//headers: {
		//    'Content-type': 'text/plain',
		//},
		statusCode: {
			204: function () {
				alert('No input text');
			},
		},

		success: function (data) {
			console.log("SUCCESS ", data);
			formatAMR(data);
			currentsentnum = data.num;
		},
		error: function (data) {
			// do something else
			//console.log("ERREUR ", data);
			$("#resultat").append('<div class="error" id="error">');
			//$('#error').append(data.responseJSON.error);
			if (data.responseJSON == undefined) {
				$('#error').append("serveur not responding");
			} else {
				$('#error').append(data.responseJSON.error);
			}
		}
	});

}


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


function ToggleComments() {
	if ($("#commentmodal").is(":visible")) {
		$("#commentmodal").hide();
	} else {
		$("#commentmodal").show();
		$("#commentmodal").draggable();
		$("#cancelcomments").click(function () {
			//$("#conceptsetmodal").fadeOut();
			$("#commentmodal").hide();
		});

	}
}


function ShowSentences() {
	if ($("#sentmodal").is(":visible")) {
		$("#sentmodal").hide();
	} else {
		$("#sentmodal").show();
		$("#sentmodal").draggable();
		$("#cancelsentlist").click(function () {
			//$("#conceptsetmodal").fadeOut();
			$("#sentmodal").hide();
		});
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


//const wdq = new RegExp('.*(Q[0-9]+).*');

/*
// needed to modify nodes and edges
var modconceptvar = "";
var modedge_start = "";
var modedge_newstart = "";
var modedge_end = "";
var modedge = "";
var litid = "";
var litedge = "";

var lastclickededge = null;
var lastclickednode = null;
var lastclickedElement = null;
*/

function info(event) {
}


var currentsentnum = 0;

function formatOne(number, svg, penman, fn) {
	// container for penman and svg, on top of one another
	//$("#resultat").append('<div class="bothresults" id="doubleresultat_' + number + '">');
	$("#doubleresultat").append('<div id="gresultat_' + number + '">');

	$("#gresultat_" + number).append('<div id="svg_resultat_' + number + '">'); // svg
	$("#gresultat_" + number).append('<div id="penman_ultat_' + number + '">'); // penman
	$("#gresultat_" + number).css("flexDirection", "column");

	// toggle button to hide/show the svg graph
	$("#svg_resultat_" + number).append('<button class="toggleresult" id="togglesvggraph_' + number + '" >&#8210;</button>');
	$("#togglesvggraph_" + number).click(function () {
		//console.log("RRR", this.id);
		ToggleDiv('#innersvggraph_' + number + '_' + currentsentnum, "#togglesvggraph_" + number);
	});

	// svg graph in an inner div
	$('#svg_resultat_' + number).append('<div class="svggraph" id="svggraph_' + number + '_' + currentsentnum + '">');
	$('#svggraph_' + number + '_' + currentsentnum).append('<span class="info">' + fn + '</span>');
	$('#svggraph_' + number + '_' + currentsentnum).append('<div id="innersvggraph_' + number + '_' + currentsentnum + '">');

	$('#innersvggraph_' + number + '_' + currentsentnum).append(svg.replace(/<svg /, '<svg onmousedown="info(event);" '));

	if ('#innersvggraph_' + number + '_' + currentsentnum in visible_divselectors && visible_divselectors['#innersvggraph_' + number + '_' + currentsentnum] == false) {
		ToggleDiv('#innersvggraph_' + number + '_' + currentsentnum, "#togglesvggraph" + number);
	}

	$('#svggraph_' + number + '_' + currentsentnum).append('<a id="semgraph_' + number + '_' + currentsentnum + '" download="graph.svg" type="image/svg+xml"><button class="mybutton">download image</button></a>');
	downloadSVG('innersvggraph_' + number + '_' + currentsentnum, 'semgraph_' + number + '_' + currentsentnum, "graph_" + number + "_" + currentsentnum + ".svg");

	// toggle button to hide/show the penman graph
	$("#penman_ultat_" + number).append('<button class="toggleresult" id="togglepenman_' + number + '" >&#8210;</button>');
	$("#togglepenman_" + number).click(function () {
		//console.log("RRR", currentsentnum, this.id);
		ToggleDiv('#amr_' + number + '_' + currentsentnum, "#togglepenman_" + number);
	});

	// penman graph in an inner div
	$("#penman_ultat_" + number).append('<div class="penman" id="penman_' + number + '_' + currentsentnum + '">');
	$('#penman_' + number + '_' + currentsentnum).append('<pre id="amr_' + number + '_' + currentsentnum + '">');
	$('#amr_' + number + '_' + currentsentnum).append(penman);

	if ('#amr_' + number + '_' + currentsentnum in visible_divselectors && visible_divselectors['#amr_' + currentsentnum] == false) {
		ToggleDiv('#amr_' + number + '_' + currentsentnum, "#togglepenman");
	}
}


function formatAMR(data) {
	lastclickededge = null;
	lastclickednode = null;
	lastclickedElement = null;

	sentenceloaded = true;
	currentsentnum = $("#sentnum").val();
	if (data.warning) {
		// display warnings
		$("#resultat").append('<div class="error" id="errordiv">');
		$("#errordiv").append('<ul id="error">');
		$.each(data.warning,
			function (key, value) {
				$('#error').append('<li>' + value);
			});
	}

	readonly = data.readonly;
	if (readonly) {
		$("#editing").hide();
		$("#save").hide();
	}

	// set valid variables to <select> tags

	// toggle button to hide/show the sentence id and the sentence
	$("#resultat").append('<button class="toggleresult" id="togglesentence" >&#8210;</button>');
	$("#togglesentence").click(function () {
		ToggleDiv('#innertext_' + currentsentnum, "#togglesentence");
	});

	//console.log(data);
	// sentence id and the sentence (in an nested div to keep the outer div always displayed
	$("#resultat").append('<div class="text" id="text_' + currentsentnum + '">');
	$('#text_' + currentsentnum).append('<div id="innertext_' + currentsentnum + '">');

	var lastchanged = "";
	if (data.lastchanged) {
		lastchanged = " (" + data.lastchanged + ")";
	}
	$('#innertext_' + currentsentnum).append("<h4>" + data.sentid + lastchanged);
	var escapedtext = data.text; //.replaceAll("<", "&lt;").replaceAll(">", "&gt;");
	$('#innertext_' + currentsentnum).append(escapedtext);
	$('#smatch').html(data.smatch);

	if (data.smatch < 100) {
		$(".smatch").css("color", "red"); //"#ffb4e6");
	} else {
		$(".smatch").css("color", "#0a6e31");
	}

	//$('#nummatching').html(data.bestmatch);
	//$('#numleft').html(data.left_triplenum);
	//$('#numright').html(data.right_triplenum);

	$("#compres").empty();
	$('#compres').append('<table id="allcomparisons"><tr><th>first</th> <th>second</th> <th>Smatch</th> <th>matching</th> <th>triples first</th> <th>triples second</th></tr></table>');
	$.each(data.comp_results,
		function (key, value) {
			//console.log("CMP", value);
			var index = value.index;
			$('#allcomparisons').append('<tr class="cmprow" id="ctr_' + index + '">');

			var smatchF1 = value.F1;

			var tdclasses = [];

			if (smatchF1 < 100) tdclasses.push("smatchdifferent");
			else tdclasses.push("smatchok");
			$('#ctr_' + index).append('<td class="' + tdclasses.join(" ") + '">' + value.fn1);
			$('#ctr_' + index).append('<td>' + value.fn2);
			$('#ctr_' + index).append('<td class="cmpval ' + tdclasses.join(" ") + '">' + value.F1);
			$('#ctr_' + index).append('<td class="cmpval ' + tdclasses.join(" ") + '">' + value.gold_triples);
			$('#ctr_' + index).append('<td class="cmpval ' + tdclasses.join(" ") + '">' + value.sys_triples);
			$('#ctr_' + index).append('<td class="cmpval ' + tdclasses.join(" ") + '">' + value.best_match_triples);
		});

	$('#ctr_' + $('#compvars').val().replace(",", "_")).addClass("boldline")
	console.log("PPPPPP", data)
	if (data.preferred) {
             $('#preferred').val(data.preferred.source);
	} else {
             $('#preferred').val("not_chosen");
	}

	if ('#innertext_' + currentsentnum in visible_divselectors && visible_divselectors['#innertext_' + currentsentnum] == false) {
		ToggleDiv('#innertext_' + currentsentnum, "#togglesentence");
	}

	$('#showcomments').empty();
	$('#showcomments').append("<h4>comments 1");
	$('#showcomments').append('<pre id="precomment_A' + currentsentnum + '">');
	$('#precomment_A' + currentsentnum).append(data.comments);


	$("#resultat").append('<div id="doubleresultat">');
	formatOne("A", data.svg, data.penman, data.filename);

	for (let i = 0; i < data.others.length; i++) {
		//console.log(data.others[i]);
		formatOne("B" + i, data.others[i].svg, data.others[i].penman, data.others[i].filename);
		$('#showcomments').append("<h4>comments " + (2 + i));
		$('#showcomments').append('<pre id="precomment_B' + i + '_' + currentsentnum + '">');
		$('#precomment_B' + i + '_' + currentsentnum).append(data.others[i].comments);
	}

	if (data.framedoc) {
		$("#resultat").append('<div class="text" id="framedoc_' + currentsentnum + '">');
		$('#framedoc_' + currentsentnum).append(data.framedoc);
	}
}


$(document).ready(function () {
	$('body').css("margin-top", "0");
	getServerInfo();
	sentenceloaded = false;

	// use ENTER to emulate a click
	$("#sentnum").keyup(function (event) {
		//console.log("zzzz", event);
		if (event.keyCode === 13) {
			$("#lire").click();
		}
	});

	$("#togglecomments").click(function () {
		ToggleComments();
	});
	$("#choosesentence").click(function () {
		ShowSentences();
	});



	$("#lire").click(function () {
		if (!readonly) {
			$(".editmode").hide();
			$("#commands").show();
		}
		//URL_BASE = 'http://' + window.location.host + '/read';
		URL_BASE = 'read';
		$("#resultat").empty(); // vider le div
		$.ajax({
			url: URL_BASE, // + "json", //+'/foo/fii?fuu=...',
			type: 'GET',
			data: {
				"num": $("#sentnum").val(),
				"compare": $("#compvars").val()
			},
			//headers: {
			//    'Content-type': 'text/plain',
			//},
			statusCode: {
				204: function () {
					alert('No input text');
				},
			},

			success: function (data) {
				//console.log("SUCCESS ", data);
				formatAMR(data);
				currentsentnum = data.num;
			},
			error: function (data) {
				// do something else
				//console.log("ERREUR ", data);
				$("#resultat").append('<div class="error" id="error">');
				//$('#error').append(data.responseJSON.error);
				if (data.responseJSON == undefined) {
					$('#error').append("serveur not responding");
				} else {
					$('#error').append(data.responseJSON.error);
				}
			}
		});
	});


	$(".walk").click(function () {
		//URL_BASE = 'http://' + window.location.host + '/next';
		URL_BASE = 'next';
		$(".editmode").hide();
		$("#commands").show();

		$("#resultat").empty(); // vider le div
		var params = {};
		/*if (this.id == "next") {
			params = {"direction": "next"}
		}
		else if (this.id == "preceding") {
			params = {"direction": "preceding"}
		}
		*/
		params["direction"] = this.id;
		params["num"] = currentsentnum;
		//params["compare"] = true;
		params["compare"] = $("#compvars").val();
		$.ajax({
			url: URL_BASE,
			type: 'GET',
			data: params,
			//headers: {
			//    'Content-type': 'text/plain',
			//},
			statusCode: {
				204: function () {
					alert('No input text');
				},
			},

			success: function (data) {
				// console.log("SUCCESS ", data);
				$("#sentnum").val(data.num);
				currentsentnum = data.num;

				formatAMR(data);
			},
			error: function (data) {
				// do something else
				console.log("ERREUR ", data);
				$("#resultat").append('<div class="error" id="error">');
				if (data.responseJSON == undefined) {
					$('#error').append("serveur not responding");
				} else {
					$('#error').append(data.responseJSON.error);
				}
			}
		});
	});


	/* modify the AMR graph by clicking on buttons of the addbutton-class */
	/*
	$(".addbutton").click(function () {
		//URL_BASE = 'http://' + window.location.host + '/edit';
		URL_BASE = 'edit';
		$("#resultat").empty(); // vider le div
		//var command = "dog"; //$("#command").val();
		//console.log("EEEEE", this.id, $("#conceptinstance").text());
		var yscroll =  $(window).scrollTop();
		var params = {};
		if (this.id == "addconcept") {
			params = { "addconcept": $("#concept").val() }
		}
		else if (this.id == "addname") {
			params = {
				"addname": $("#name").val(),
				"nameof": $("#nameof").val()
			}
		}
		else if (this.id == "addname2") {
			$(".editmode").hide();
			$("#commands").show();
			params = {
				"addname": $("#name2").val(),
				"nameof": $("#conceptinstance").text()
			}
		}
		else if (this.id == "addedge") {
			params = {
				"start": $("#startvar").val(),
				"label": $("#edgelabel").val(),
				"end": $("#endvar").val()
			}
		}
		else if (this.id == "addliteral") {
			params = {
				"literalof": $("#literalof").val(),
				"relationforliteral": $("#relationforliteral").val(),
				"newliteral": $("#newliteral").val()
			}
		}
		else if (this.id == "addliteral2") {
			$(".editmode").hide();
			$("#commands").show();
			params = {
				"literalof": $("#conceptinstance").text(),
				"relationforliteral": $("#relationforliteral2").val(),
				"newliteral": $("#newliteral2").val()
			};
		}
		else if (this.id == "settop") {
			params = { "newtop": $("#topnode").val() }
		}
		else if (this.id == "delinstance") {
			$(".editmode").hide();
			$("#commands").show();
			params = { "delinstance": modconceptvar }
		}
		else if (this.id == "delliteral") {
			$(".editmode").hide();
			$("#commands").show();
			params = {
				"delliteral": $("#modifiedliteral").val(),
				"literalid": litid,
				"literaledge": litedge
			}
		}
		else if (this.id == "modifyconcept") {
			$(".editmode").hide();
			$("#commands").show();
			params = {
				"modconcept": modconceptvar,
				"newconcept": $("#modifiedconcept").val()
			}
		}
		else if (this.id == "modifyliteral") {
			$(".editmode").hide();
			$("#commands").show();
			params = {
				"literalid": litid,
				"literaledge": litedge,
				"newliteral": $("#modifiedliteral").val()
			}
		}
		else if (this.id == "deledge") {
			$(".editmode").hide();
			$("#commands").show();
			params = {
				"deledge_start": modedge_start,
				"deledge_end": modedge_end,
				"deledge": modedge
			}
		}
		else if (this.id == "modifyedge") {
			$(".editmode").hide();
			$("#commands").show();
			params = {
				"modedge_start": modedge_start,
				"modedge_end": modedge_end,
				"newedge": $("#modifiededge").val()
			}
		}
		else if (this.id == "moveedge") {
			$(".editmode").hide();
			$("#commands").show();
			params = {
				"modedge_start": modedge_start,
				"modedge_end": modedge_end,
				"modedge_newstart": $("#newsource").val(),
				"newedge": $("#modifiededge").val()
			}
		}
		else if (this.id == "modifypenman") {
			$(".editmode").hide();
			$("#commands").show();
			params = { "modpenman": $("#modifiedpenman").val() }
		}
		else if (this.id == "modifycomment") {
			$(".editmode").hide();
			$("#commands").show();
			params = { "modcomment": $("#modifiedcomment").val() }
		}
		else if (this.id == "reifygraph") {
			$(".editmode").hide();
			$("#commands").show();
			console.log("TTT", $("#reifylist").val());
			var relation_to_reify = $("#reifylist").val().split(" ")[0];
			params = { "reify": relation_to_reify }
		}
		else if (this.id == "dereifygraph") {
			$(".editmode").hide();
			$("#commands").show();
			var concept_to_dereify = $("#reifylist").val().split(" ")[2];
			params = { "dereify": concept_to_dereify }
		}
		else if (this.id == "modifysentencelist") {
			// apply sentence list filters
			$('#sentencelist').empty();
			for (var i = 0; i<sentencelist.length; ++i) {
			//if (i % 200 == 0) console.log("filtering", i);
			var idfilter = $('#sidfilter').val();
			var textfilter = $('#textfilter').val();
			//console.log("FILTER", idfilter, textfilter, sentencelist[i][0].search(idfilter));
			// use .search() instead of .indexOf() for regex (very slow for long sentence lists)
			if ((idfilter == "" || sentencelist[i][0].indexOf(idfilter) > -1)
				&& (textfilter == "" || sentencelist[i][1].indexOf(textfilter) > -1)) {
				//console.log("FILTER OK", sentencelist[i]);
				var optionstring = sentencelist[i][0] + ": " + sentencelist[i][1];
				if (optionstring.length > 150) {
				optionstring = optionstring.substring(optionstring, 150) + "...";
				}


				$('#sentencelist').append('<option value="' + (i+1) +'">' + optionstring);
			}
			}


		} else {
			return;
		}
		params["num"] = currentsentnum;
		if (sentenceloaded == true) {
		$.ajax({
			url: URL_BASE,
			type: 'POST',
			//data: {"cmd": command},
			data: params,
			//headers: {
			//    'Content-type': 'text/plain',
			//},
			statusCode: {
				204: function () {
					alert('No input text');
				},
				//400: function () {
				//                    alert('Bad query');
				//		},
				//		500: function () {
				//		    alert("Error on '" + URL_BASE + "' " + data);
				//		}
			},

			success: function (data) {
				//console.log("SUCCESS ", data);
				formatAMR(data);
				$(window).scrollTop(yscroll);
			},
			error: function (data) {
				// do something else
				console.log("ERREUR ", data);
				$("#resultat").append('<div class="error" id="error">');
				if (data.responseJSON == undefined) {
					$('#error').append("serveur not responding");
				} else {
					$('#error').append(data.responseJSON.error);
				}

			}
		});
		}
	});*/

	$(".cleanbutton").click(function () {
		if (this.id == "cleanfields") {
			$(".varfield").val("");
			$(".conceptfield").val("");
			$(".literalfield").val("");
			$(".edgefield").val("");
		}
	});

	$(".findbutton").click(function () {
		//URL_BASE = 'http://' + window.location.host + '/search';
		URL_BASE = 'search';
		$("#resultat").empty(); // vider le div
		//var command = "dog"; //$("#command").val();
		//console.log("EEEEE", this.id);
		var params = {};
		if (this.id == "findtextnext" || this.id == "findtextprec") {
			params = {
				"what": this.id,
				"regex": $("#textsearch").val()
			}
		} else if (this.id == "findidnext" || this.id == "findidprec") {
			params = {
				"what": this.id,
				"regex": $("#idsearch").val()
			}
		} else if (this.id == "findamrnext" || this.id == "findamrprec") {
			params = {
				"what": this.id,
				"regex": $("#amrsearch").val()
			}
		} else if (this.id == "findcommentnext" || this.id == "findcommentprec") {
			params = {
				"what": this.id,
				"regex": $("#commentsearch").val()
			}
		} else {
			return;
		}
		params["num"] = currentsentnum;
		//params["compare"] = true;
		params["compare"] = $(".comparisons").val();
		$.ajax({
			url: URL_BASE,
			type: 'GET',
			//data: {"cmd": command},
			data: params,
			//headers: {
			//    'Content-type': 'text/plain',
			//},
			statusCode: {
				204: function () {
					alert('No input text');
				},
				//400: function () {
				//                    alert('Bad query');
				//		},
				//		500: function () {
				//		    alert("Error on '" + URL_BASE + "' " + data);
				//		}
			},

			success: function (data) {
				//console.log("SUCCESS ", data);
				$("#sentnum").val(data.num);
				currentsentnum = data.num;

				formatAMR(data);
			},
			error: function (data) {
				// do something else
				console.log("ERREUR ", data);
				$("#resultat").append('<div class="error" id="error">');
				//$('#error').append(data.responseJSON.error);
				if (data.responseJSON == undefined) {
					$('#error').append("serveur not responding");
				} else {
					$('#error').append(data.responseJSON.error);
				}
			}
		});
	});



});
