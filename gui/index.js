/*
 This library is under the 3-Clause BSD License

 Copyright (c) 2022-2023,  Orange
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
 	        data: {"withdata": true},
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
			//		$('#sitable').append('<tr id="tr_' + key + '">');
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
		    $("#filename").empty();
		    $("#filename").append(data.filename);

		    $("#numsent").empty();
		    $("#numsent").append(data.numsent);

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

		    if (data.relations) {
			relationlist = data.relations;
			// autocomplete for the fields where relations can be set
			$(function () {
			      $("#edgelabel").autocomplete({
				  source: relationlist,
					  // https://www.plus2net.com/jquery/msg-demo/autocomplete-position.php
					  position: {my: "left top", at: "left bottom"}
				  });
			  });

			$(function () {
			      $("#relationforliteral").autocomplete({
				  source: relationlist,
					  // https://www.plus2net.com/jquery/msg-demo/autocomplete-position.php
					  position: {my: "left top", at: "left bottom"}
				  });
			  });

			$(function () {
			      $("#modifiededge").autocomplete({
				  source: relationlist,
					  // https://www.plus2net.com/jquery/msg-demo/autocomplete-position.php
					  position: {my: "left top", at: "left bottom"},
					  appendTo: "#modedge" // needed to avoid modal covering completion list
				  });
			  });
			$(function () {
			      $("#relationforliteral2").autocomplete({
				  source: relationlist,
					  // https://www.plus2net.com/jquery/msg-demo/autocomplete-position.php
					  position: {my: "left top", at: "left bottom"},
				  appendTo: "#modconcept"
				  });
			  });
		    }

		    if (data.concepts) {
			conceptlist = data.concepts
			$(function () {
			      $("#concept").autocomplete({
				  source: conceptlist,
					  // https://www.plus2net.com/jquery/msg-demo/autocomplete-position.php
					  position: {my: "left top", at: "left bottom"}
				  });
			  });
			$(function () {
			      $("#modifiedconcept").autocomplete({
				  source: conceptlist,
					  // https://www.plus2net.com/jquery/msg-demo/autocomplete-position.php
					  position: {my: "left top", at: "left bottom"},
					  appendTo: "#modconcept" // needed to avoid modal covering completion list
				  });
			  });
		    }

		    if (data.sentences) {
			sentencelist = data.sentences;
			for (var i =0; i<data.sentences.length; ++i) {
			    var optionstring = data.sentences[i][0] + ": " + data.sentences[i][1];
			    if (optionstring.length > 150) {
				optionstring = optionstring.substring(optionstring, 150) + "...";
			    }
			    $('#sentencelist').append('<option value="' + (i+1) +'">' + optionstring);
			}

			$("#sentencelist").change(function() {
                           $("#sentnum").val($(this).val());
                           $("#lire").click();
                           $("#sentmodal").hide();
			});
		    }


		    if (data.reifications) {
			$.each(data.reifications,
			       function (key, value) {
				   //console.log("AAA", key, value);
				   $('#reifylist').append('<option value="' + value +'">' + value);
			       });
		    } else {
			$('#reifygroup').hide();
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

function downloadSVG(svgelem, ident) {
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
	a2.download = "graph.svg";
}



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

function ToggleHelp() {
	if ($("#helptext").is(":visible")) {
		$("#helptext").hide();
	} else {
		$("#helptext").show();
	}
}

function ShowSentences() {
	if ($("#sentmodal").is(":visible")) {
		$("#sentmodal").hide();
	} else {
		$("#sentmodal").show();
			$("#cancelsentlist").click(function(){
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


//const wdq = new RegExp('.*(Q[0-9]+).*');

// needed to modify nodes and edges
var modconceptvar = "";
var modedge_start = "";
var modedge_newstart = "";
var modedge_end = "";
var modedge = "";
var litid = "";
var litedge = "";

var lastclickededge = null;

function info(event) {
	//console.log("EEEE", event);
	//console.log("EEEF", event.target.parentNode.id);
	//console.log("EEEG", event.target.parentNode.children[1]);
	node = event.target.textContent;

	unhighlight();

	if (readonly) {
	    return;
	}
	if (event.target.parentNode.id.startsWith("node ")) {
		// edit node
		modconceptvar = event.target.parentNode.id.split(" ")[1];

		if (lastclickededge != null) {
			// we take the last clicked edge and connect to the now clicked instance
			$(".editmode").hide();
			$("#commands").show();
			console.log("RRR", lastclickededge);
			var edgestart = lastclickededge.split("#")[1];
			var edgeend = lastclickededge.split("#")[2];
			var edgename = lastclickededge.split("#")[3];
			var params = {
				"modedge_start": edgestart,
				"modedge_end": edgeend,
				"modedge_newstart": modconceptvar,
				"newedge": edgename
			}
			lastclickededge = null;
			runcommand(params);
		} else {
			// we modify an instance/class node
			$(".modal").hide();
			//$("#modconcept").show();
			const conceptname = event.target.parentNode.id.split(" ")[2];
			$("#modifiedconcept").val(conceptname);
			$("#conceptinstance").empty();
			$("#conceptinstance").append(modconceptvar);
			$("#relationforliteral2").val(modconceptvar);
			$("#newliteral2").val("");
			$("#name2").val("");

			// open edit modal
			//console.log("ffff", event.clientY, event.pageY, event.screenY);
			$("#conceptsetmodal").css("top", event.pageY + "px");
			$("#conceptsetmodal").css("left", event.pageX + "px");
			$("#conceptsetmodal").show();
			$("#conceptsetmodal").draggable();

			$("#cancelmc").click(function(){
				//$("#conceptsetmodal").fadeOut();
				$("#conceptsetmodal").hide();
			});			
	
		}
		

	} else if (event.target.parentNode.id.startsWith("edge#")) {
		// we modify an edge
		$(".modal").hide();
		//$("#modedge").show();
		const edgename = event.target.parentNode.id.split("#")[3];

		// get polygon child of current 
		var chosenrel = -1;
		for (var i = 0; i < event.target.parentNode.children.length; i++) {
			//console.log("TTTT", i, event.target.parentNode.children[i].tagName);
			if (event.target.parentNode.children[i].tagName == "polygon") {
				event.target.parentNode.children[i].setAttribute("class", "boxhighlight");
				lastclickededge = event.target.parentNode.id;
				chosenrel = i;
				//console.log("HIER");
			}
		};


		$("#modifiededge").val(edgename)
		modedge = edgename;
		modedge_start = event.target.parentNode.id.split("#")[1];
		modedge_end = event.target.parentNode.id.split("#")[2];
		$("#relationfrom").empty();
		$("#relationfrom").append(modedge_start);
		$("#relationto").empty();
		$("#relationto").append(modedge_end);
		$("#newsource").val("");

          	// open edit modal
		$("#edgesetmodal").css("top", event.pageY + "px");
		$("#edgesetmodal").css("left", event.pageX + "px");
		$("#edgesetmodal").show();
		$("#edgesetmodal").draggable();

		$("#cancelme").click(function(){
			lastclickededge = null;
			$("#edgesetmodal").hide();
			if (chosenrel > -1) {
				console.log("aaaaa", event.target.parentNode.children[chosenrel]);
				event.target.parentNode.children[chosenrel].setAttribute("class", "");
			}
		});			
	
	} else if (event.target.parentNode.id.startsWith("literal ")) {
		// edit literal
		$(".modal").hide();
		//$("#modlit").show();
		//console.log("ZZZZ", event.target.parentNode.id.split(" "));
                const elems = event.target.parentNode.id.split(" ");
		const toto = elems.slice(3);
		const literalname = toto.join(" ");
		//const literalname = event.target.parentNode.id.split(" ")[3];
		litid = event.target.parentNode.id.split(" ")[1];
		litedge = event.target.parentNode.id.split(" ")[2];
		$("#modifiedliteral").val(literalname.replaceAll('"', ''));

		// open edit modal
		$("#literalsetmodal").css("top", event.pageY + "px");
		$("#literalsetmodal").css("left", event.pageX + "px");
		$("#literalsetmodal").show();
		$("#literalsetmodal").draggable();
		
		$("#cancelml").click(function(){
			$("#literalsetmodal").hide();
		});	
	}
}

function runcommand(params) {
	params["num"] = currentsentnum;
	//URL_BASE = 'http://' + window.location.host + '/edit';
	URL_BASE = 'edit';
	$("#resultat").empty(); // vider le div
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
		},
		success: function (data) {
			//console.log("SUCCESS ", data);
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
}


var currentsentnum = 0;

function formatAMR(data) {
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
	
	$('.validvars').empty();

	$.each(data.variables,
	       function (key, value) {
		   //console.log("AAA", key, value);
		   $('.validvars').append('<option value="' + value +'">' + value);
	       });

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
	$('#innertext_' + currentsentnum).append("<h4>" + data.sentid +lastchanged);
        var escapedtext = data.text; //.replaceAll("<", "&lt;").replaceAll(">", "&gt;");
	$('#innertext_' + currentsentnum).append(escapedtext);

	if ('#innertext_' + currentsentnum in visible_divselectors && visible_divselectors['#innertext_' + currentsentnum] == false) {
		ToggleDiv('#innertext_' + currentsentnum, "#togglesentence");
	}


	// toggle button to hide/show comments
	$("#resultat").append('<button class="toggleresult" id="togglecomment" >&#8210;</button>');
	$("#togglecomment").click(function () {
		ToggleDiv('#innercomment_' + currentsentnum, "#togglecomment");
	});

	// comments (in an nested div to keep the outer div always displayed
	$("#resultat").append('<div class="text" id="comment_' + currentsentnum + '">');
	$('#comment_' + currentsentnum).append('<div id="innercomment_' + currentsentnum + '">');
	$('#innercomment_' + currentsentnum).append("<h4>comments");
	$('#innercomment_' + currentsentnum).append('<pre id="precomment_' + currentsentnum + '">');
	$('#precomment_' + currentsentnum).append(data.comments);

	if ('#innercomment_' + currentsentnum in visible_divselectors && visible_divselectors['#innercomment_' + currentsentnum] == false) {
		ToggleDiv('#innercomment_' + currentsentnum, "#togglesentence");
	}


	$("#comment_" + currentsentnum).click(function () {
		if (!readonly) {
		    $(".editmode").hide();
		    $("#modcomment").show();
		}
		$("#modifiedcomment").val($('#precomment_' + currentsentnum).html());
	});

	// container for penman and svg, either on top of one anothoer or next to each ther
	$("#resultat").append('<div id="gresultat">');
	$("#gresultat").append('<div id="g1resultat">');
	$("#gresultat").append('<div id="g2resultat">');

	// toggle button to hide/show the penman graph
	$("#g1resultat").append('<button class="toggleresult" id="togglepenman" >&#8210;</button>');
	$("#togglepenman").click(function () {
		//console.log("RRR", currentsentnum, this.id);
		ToggleDiv('#amr_' + currentsentnum, "#togglepenman");
	});


	// penman graph in an inner div
	$("#g1resultat").append('<div class="penman" id="penman_' + currentsentnum + '">');
	$('#penman_' + currentsentnum).append('<pre id="amr_' + currentsentnum + '">');
	$('#amr_' + currentsentnum).append(data.penman);

	if ('#amr_' + currentsentnum in visible_divselectors && visible_divselectors['#amr_' + currentsentnum] == false) {
		ToggleDiv('#amr_' + currentsentnum, "#togglepenman");
	}

	$("#penman_" + currentsentnum).click(function () {
		if (!readonly) {
		    $(".editmode").hide();
		    $("#modpenman").show();
		}
		$("#modifiedpenman").val($('#amr_' + currentsentnum).html());
	});


	// toggle button to hide/show the svg graph
	$("#g2resultat").append('<button class="toggleresult" id="togglesvggraph" >&#8210;</button>');
	$("#togglesvggraph").click(function () {
		//console.log("RRR", this.id);
		ToggleDiv('#innersvggraph_' + currentsentnum, "#togglesvggraph");
	});

	// svg graph in an inner div
	$('#g2resultat').append('<div class="svggraph" id="svggraph_' + currentsentnum + '">');
	$('#svggraph_' + currentsentnum).append('<div id="innersvggraph_' + currentsentnum + '">');
	$('#innersvggraph_' + currentsentnum).append(data.svg.replace(/<svg /, '<svg onmousedown="info(event);" '));

	if ('#innersvggraph_' + currentsentnum in visible_divselectors && visible_divselectors['#innersvggraph_' + currentsentnum] == false) {
		ToggleDiv('#innersvggraph_' + currentsentnum, "#togglesvggraph");
	}

	if (data.framedoc) {
		$("#resultat").append('<div class="text" id="framedoc_' + currentsentnum + '">');
		$('#framedoc_' + currentsentnum).append(data.framedoc);
	}

	if (data.undos > 0) {
		$("#undo").prop("disabled", false);
	} else {
		$("#undo").prop("disabled", true);
	}
	if (data.redos > 0) {
		$("#redo").prop("disabled", false);
	} else {
		$("#redo").prop("disabled", true);
	}

}


$(document).ready(function () {
	$('body').css("margin-top", "0");
	getServerInfo();
	sentenceloaded = false;

	// toggle the box with the search functions
	$("#togglesearch").click(function () {
		ToggleDiv('#searchfunctions', "#togglesearch");
	});


	$(".canceleditmode").click(function () {
		if (!readonly) {
		    $(".editmode").hide();
		    $("#commands").show();
		}
	});

	// use ENTER to emulate a click
	$("#concept").keyup(function (event) {
		//console.log("zzzz", event);
		if (event.keyCode === 13) {
			$("#addconcept").click();
		}
	});
	$("#topnode").keyup(function (event) {
		//console.log("zzzz", event);
		if (event.keyCode === 13) {
			$("#settop").click();
		}
	});
	$("#sentnum").keyup(function (event) {
		//console.log("zzzz", event);
		if (event.keyCode === 13) {
			$("#lire").click();
		}
	});

	$("#togglehelp").click(function () {
		ToggleHelp();
	});
	$("#choosesentence").click(function () {
		ShowSentences();
	});

	$("#toggledirection").click(function () {
		ToggleDirection();
	});




	$("#save").click(function () {
		if (!readonly) {
		    $(".editmode").hide();
		    $("#commands").show();
		}
		//URL_BASE = 'http://' + window.location.host + '/save';
		URL_BASE = 'save';
		$("#resultat").empty(); // vider le div

		$.ajax({
			url: URL_BASE, // + "json", //+'/foo/fii?fuu=...',
			type: 'GET',
			data: { "num": $("#sentnum").val() },
			//headers: {
			//    'Content-type': 'text/plain',
			//},
			statusCode: {
				204: function () {
					alert('No input text');
				},
				//400: function () {
				//alert('Bad query');
				//},
				//		500: function () {
				//		    alert("Error on '" + URL_BASE + "' " + data);
				//		}
			},

			success: function (data) {
				//console.log("SUCCESS ", data);
				formatAMR(data);

				$("#filename").empty();
				$("#filename").append(data.filename);

				$("#numsent").empty();
				$("#numsent").append(data.numsent);
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
			data: { "num": $("#sentnum").val() },
			//headers: {
			//    'Content-type': 'text/plain',
			//},
			statusCode: {
				204: function () {
					alert('No input text');
				},
				//400: function () {
				//alert('Bad query');
				//},
				//		500: function () {
				//		    alert("Error on '" + URL_BASE + "' " + data);
				//		}
			},

			success: function (data) {
				//console.log("SUCCESS ", data);
				formatAMR(data);

				$("#filename").empty();
				$("#filename").append(data.filename);

				$("#numsent").empty();
				$("#numsent").append(data.numsent);
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




	$(".history").click(function () {
		//URL_BASE = 'http://' + window.location.host + '/history';
		URL_BASE = 'history';
		$("#resultat").empty(); // vider le div
		//var command = "dog"; //$("#command").val();
		//console.log("EEEEE", this.id);
		var params = {};
		params = { "history": this.id }

		params["num"] = currentsentnum;
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
				//400: function () {
				//alert('Bad query');
				//},
				//		500: function () {
				//		    alert("Error on '" + URL_BASE + "' " + data);
				//		}
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
	});

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
		} else {
			return;
		}
		params["num"] = currentsentnum;
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




	/*    $("#vider").click(function () {
			  //$('#enhdeprelEdit').modal('hide');
			  $("#texte").val("");
			  //$("#frameinfo").empty();
			  $("#resultat").empty();
			  $(window).scrollTop(0);
			  }); */

});
