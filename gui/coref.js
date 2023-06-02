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

/** get information from relation extraction server */
function getServerInfo() {
	//var urlbase = 'http://' + window.location.host + ':' + $("#port").val() + '/';
	//URL_BASE = 'http://' + window.location.hostname + ':' + $("#port").val() + '/info';
	//URL_BASE = 'http://' + window.location.host + '/info';
        URL_BASE = 'info';


	$.ajax({
		url: URL_BASE,
		type: 'GET',
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
		    /** show how the server was started */
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

var lastclickedinst = null;
//var lastchain = null;

/** clickin on a node in the graph */
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

		if (lastclickedinst != null) {
			// we take the last clicked instance and connect give it the same corefchain as the instance clicked now. If the current has no chain, we create a new one
			//console.log("RRR   ", lastclickedinst);
		        var nodelabelfields = event.target.parentNode.id.split(" ");
			clickedinst = nodelabelfields[1];
			//console.log("SECOND", clickedinst);
			var sentpos = clickedinst.split("_")[1];
			var inst = clickedinst.split("_")[2];

			var params = {
			    "num": $("#sentnum").val(), // xmlfile
			    "from": lastclickedinst,
			    "to": clickedinst,
			}
			lastclickedinst = null;
			//if (lastchain != "none")
			runcommand(params, "addtochain");
		} else {
			// we modify an instance/class node
			//$(".modal").hide();
		        // event.target.parentNode.id contains the id of the node,
		        // i.e. info on which sentence, which instance, which chain
		        var nodelabelfields = event.target.parentNode.id.split(" ");
			event.target.parentNode.setAttribute("class", "boxhighlight");
			//const conceptname = nodelabelfields[2]; //event.target.parentNode.id.split(" ")[2];
			lastclickedinst = nodelabelfields[1];
			//lastchain = nodelabelfields[3].split("_")[1];
			//console.log("FIRST ", lastclickedinst);
			/*
			// open edit modal
			//console.log("ffff", event.clientY, event.pageY, event.screenY);
			$("#conceptsetmodal").css("top", event.pageY + "px");
			$("#conceptsetmodal").css("left", event.pageX + "px");
			$("#conceptsetmodal").show();

			$("#cancelmc").click(function(){
				//$("#conceptsetmodal").fadeOut();
				$("#conceptsetmodal").hide();
			});			
			*/
		}
	}
}

function runcommand(params, path) {
	params["num"] = currentsentnum;
	params["showfrom"] = $("#firstamr").val();
	params["shownumber"] = $("#windowsize").val();
	params["scaling"] = $("#scaling").val();

	//URL_BASE = 'http://' + window.location.host + '/edit';
	URL_BASE = path;
	var yscroll =  $(window).scrollTop();
	//var xscroll =  $(window).scrollLeft();
	var xscroll =  $("#gresultat").scrollLeft();
	//console.log("XX", xscroll, yscroll);

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
			//console.log("to XX", xscroll);
			//$(window).scrollLeft(xscroll);
			$("#gresultat").scrollLeft(xscroll);
			$(window).scrollTop(yscroll);
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
	if (data.warnings) {
		// display warnings
		$("#resultat").append('<div class="error" id="errordiv">');
		$("#erroriv").append('Warnings:');
		$("#errordiv").append('<ul id="error">');
		$.each(data.warnings,
			function (key, value) {
				$('#error').append('<li>' + value);
		       });
	}
	if (data.messages) {
		// display warnings
		$("#resultat").append('<div class="message" id="messagediv">');
		$("#messagediv").append('Messages:');
		$("#messagediv").append('<ul id="message">');
		$.each(data.messages,
			function (key, value) {
				$('#message').append('<li>' + value);
		       });
	}

	readonly = data.readonly;
	if (readonly) {
	    $("#editing").hide();
	    $("#save").hide();
	}

	// set valid variables to <select> tags
	/*
	$('.validvars').empty();

	$.each(data.variables,
	       function (key, value) {
		   //console.log("AAA", key, value);
		   $('.validvars').append('<option value="' + value +'">' + value);
	       });
	*/
	// toggle button to hide/show the sentence id and the sentence
	//$("#resultat").append('<button class="toggleresult" id="togglesentence" >&#8210;</button>');
	//$("#togglesentence").click(function () {
	//	ToggleDiv('#innertext_' + currentsentnum, "#togglesentence");
	//});

	//console.log(data);
	// sentence id and the sentence (in an nested div to keep the outer div always displayed
	//$("#resultat").append('<div class="text" id="text_' + currentsentnum + '">');
	//$('#text_' + currentsentnum).append('<div id="innertext_' + currentsentnum + '">');

	$("#filename").empty();
	$("#filename").append(data.filename);


	/* var lastchanged = "";
	if (data.lastchanged) {
	    lastchanged = " (" + data.lastchanged + ")";
	}
	$('#innertext_' + currentsentnum).append("<h4>" + data.sentid +lastchanged);
        var escapedtext = data.text; //.replaceAll("<", "&lt;").replaceAll(">", "&gt;");
	$('#innertext_' + currentsentnum).append(escapedtext);

	if ('#innertext_' + currentsentnum in visible_divselectors && visible_divselectors['#innertext_' + currentsentnum] == false) {
		ToggleDiv('#innertext_' + currentsentnum, "#togglesentence");
	}
	*/

	
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
	$('#precomment_' + currentsentnum).append(data.comment);

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
	console.log(data);
	//$("#gresultat").append('<div id="g1resultat">');
	//$("#gresultat").append('<div id="g2resultat">');

	// toggle button to hide/show the penman graph
	//$("#g1resultat").append('<button class="toggleresult" id="togglepenman" >&#8210;</button>');
	//$("#togglepenman").click(function () {
	//	//console.log("RRR", currentsentnum, this.id);
	//	ToggleDiv('#amr_' + currentsentnum, "#togglepenman");
	//});


	// penman graph in an inner div
	/*
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
	*/

	// toggle button to hide/show the svg graph
	//$("#g2resultat").append('<button class="toggleresult" id="togglesvggraph" >&#8210;</button>');
	//$("#togglesvggraph").click(function () {
	//	//console.log("RRR", this.id);
	//	ToggleDiv('#innersvggraph_' + currentsentnum, "#togglesvggraph");
	//});

	if (false) {
	    // combined graph
	    // svg graph in an inner div
	    $('#gresultat').append('<div class="svggraph" id="svggraph_' + currentsentnum + '">');
	    $('#svggraph_' + currentsentnum).append('<div id="innersvggraph_' + currentsentnum + '">');
	    $('#innersvggraph_' + currentsentnum).append(data.svg.replace(/<svg /, '<svg onmousedown="info(event);" '));
	} else {
	    var sgroup = data.showfrom;
	    $.each(data.svgdict,
		   function (sid, obj) {
		       //console.log("EEE", sid, obj);
		       svg = obj.svg;
		       // make clickable
		       svgmod = svg.replace(/<svg /, '<svg onmousedown="info(event);" ');
		       // does not scale the width
		       //svgmod = svgmod.replace("scale(1 1)", 'scale(0.75 0.75)');
		       sentnum = sgroup+1;
		       $('#gresultat').append('<div class="svggraph" id="svggraph_' + sgroup + '">');
		       $('#svggraph_' + sgroup).append('<div class="sentenceid">' + sentnum + ": " + sid);
		       //$('#svggraph_' + sgroup).append('<div class="sentencetext">«' + obj.text + "»");
		       $('#svggraph_' + sgroup).append('<div class="sentencetext">' + obj.text);
		       $('#svggraph_' + sgroup).append('<div id="innersvggraph_' + sgroup + '">');
		       $('#innersvggraph_' + sgroup).append(svgmod);
		       sgroup++;
		   })
	}



	$('#resultat').append('<div class="svggraph" id="chainsdiv">');
	$("#chainsdiv").append('<h2>Coreference chains');
	$("#chainsdiv").append('<dl id="chains_dl">');
	$.each(data.chaintable,
		   function (cid, obj) {
		   //$("#chains").append('<li id="chain_' + cid + '">' + cid + ":");
		   $("#chains_dl").append('<dt id="chain_dt_' + cid + '"> rel-' + cid);
		   $("#chains_dl").append('<dd id="chain_dd_' + cid + '">');
		   for (var i = 0; i < obj.length; ++i) {
		       $('#chain_dd_' + cid).append(" " + obj[i]);
		   }
	       });

	if (data.bridgingtable) {
	    $('#resultat').append('<div class="svggraph" id="bridgingdiv">');
	    $("#bridgingdiv").append('<h2>Bridging');
	    $("#bridgingdiv").append('<dl id="bridging_dl">');
	    $.each(data.bridgingtable,
		   function (cid, obj) {
		       //$("#chains").append('<li id="chain_' + cid + '">' + cid + ":");
		       $("#bridging_dl").append('<dt id="bridging_dt_' + cid + '"> rel-' + cid);
		       $("#bridging_dl").append('<dd id="bridging_dd_' + cid + '">');
		       for (var i = 0; i < obj.length; ++i) {
			   $('#bridging_dd_' + cid).append(" " + obj[i]);
		       }
		   });
	    
	}

	//if ('#innersvggraph_' + currentsentnum in visible_divselectors && visible_divselectors['#innersvggraph_' + currentsentnum] == false) {
	//	ToggleDiv('#innersvggraph_' + currentsentnum, "#togglesvggraph");
	//}

	/*
	if (data.framedoc) {
		$("#resultat").append('<div class="text" id="framedoc_' + currentsentnum + '">');
		$('#framedoc_' + currentsentnum).append(data.framedoc);
		}*/

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

	$(".chain").click(function () {
			      console.log("CHAIN", $(this).attr("data"));
			      lastclickedinst = $(this).attr("data");
			  });

}


$(document).ready(function () {
	$('body').css("margin-top", "0");
	getServerInfo();
	sentenceloaded = false;

	/*
	// toggle the box with the search functions
	$("#togglesearch").click(function () {
		ToggleDiv('#searchfunctions', "#togglesearch");
	});
	*/

	$(".canceleditmode").click(function () {
		if (!readonly) {
		    $(".editmode").hide();
		    //$("#commands").show();
		}
	});
	/*
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
	*/

	$("#sentnum").keyup(function (event) {
		//console.log("zzzz", event);
		if (event.keyCode === 13) {
			$("#lire").click();
		}
	});

	$("#togglehelp").click(function () {
		ToggleHelp();
	});

	$("#toggledirection").click(function () {
		ToggleDirection();
	});


	$("#save").click(function () {
			     //if (!readonly) {
			     //$(".editmode").hide();
			     //$("#commands").show();
			     //		}

		URL_BASE = 'save';
		$("#resultat").empty(); // vider le div

		$.ajax({
			url: URL_BASE, // + "json", //+'/foo/fii?fuu=...',
			type: 'GET',
			    data: { "num": $("#sentnum").val(),
				"showfrom": $("#firstamr").val(),
			        "shownumber": $("#windowsize").val(),
				"scaling": $("#scaling").val()
                             },

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


	$("#modifycomment").click(function () {
		URL_BASE = 'modifycomment';
		$("#resultat").empty(); // vider le div

		$.ajax({
			url: URL_BASE, // + "json", //+'/foo/fii?fuu=...',
			type: 'GET',
			    data: { "num": $("#sentnum").val(),
				"showfrom": $("#firstamr").val(),
			        "shownumber": $("#windowsize").val(),
				"scaling": $("#scaling").val(),
				"comment": $("#modifiedcomment").val(),
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
		$(".editmode").hide();
	});


	$("#lire").click(function () {
			     //if (!readonly) {
			     //$(".editmode").hide();
			     //$("#commands").show();
			     //}

		URL_BASE = 'read';
		$("#resultat").empty(); // vider le div

		$.ajax({
			url: URL_BASE, // + "json", //+'/foo/fii?fuu=...',
			type: 'GET',
			    data: { "num": $("#sentnum").val(),
				"showfrom": $("#firstamr").val(),
				"shownumber": $("#windowsize").val(),
				"scaling": $("#scaling").val()
				    },
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
		params = { "history": this.id,
			   "showfrom": $("#firstamr").val(),
 			   "shownumber": $("#windowsize").val(),
			   "scaling": $("#scaling").val()
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
		params["showfrom"] = $("#firstamr").val();
		params["shownumber"] = $("#windowsize").val();
		params["scaling"] = $("#scaling").val();

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
			    //console.log("SUCCESS ", data);
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


	/*
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
		});*/





});
