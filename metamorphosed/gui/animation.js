/*
 This library is under the 3-Clause BSD License

 Copyright (c) 2025,  Orange
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

// Set up the SVG container
var svg = null;

function highlight_pm(amr) {
    var output = amr.replace(/("[^\"]+")/g, '<span class="literal">$1</span> '); // " // hightlight strings
    output = output.replace(/(:quant|:value|:op[0-9]) ([a-z0-9\.]+)/g, '$1 <span class="literal">$2</span> '); // highlight non-string literals
    output = output.replace(/([a-z]+[a-z0-9]*) \//g, ' <span class="conceptslash">$1</span> <b>/</b>'); // highlight variables
    //output = output.replace(/:([ARGa-z0-9-]+[0-9]?)/g, ' <span class="$1text">:$1</span>'); //  highlight relations
    output = output.replace(/:([ARGa-z0-9-]+[0-9]?)/g, function (match, p1) { return ' <span class="' + p1.replace("-of", "") + 'text">:' + p1 + '</span>' }); //  highlight relations

    return output;
}

function showme() {
    if (svg != null) {
        svg.selectAll("*").remove();
    }
    //svg = d3.select("svg"),
    //width = +svg.attr("width"),
    //height = +svg.attr("height");

    const width = window.innerWidth - 200;
    const height = window.innerHeight;
    svg = d3.select("svg")
        .attr("width", width)
        .attr("height", height);

    // Define arrow markers for graph links
    svg.append("defs").append("marker")
        .attr("id", "arrowhead")
        //.attr("id", function(d,i) { console.log("eee" + i); return "arrowhead" + 1;  }) 
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 10)  // position from node
        .attr("refY", 0)
        .attr("orient", "auto")
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("xoverflow", "visible")
        .append("path")
        .attr("d", "M 0,-5 L 10,0 L 0,5")
        .attr("class", "arrowhead")

    // Create a force simulation
    const simulation = d3.forceSimulation(graph.nodes)
        .force("link", d3.forceLink(graph.links).id(d => d.id).distance(100)) // default distance of nodes
        .force("charge", d3.forceManyBody().strength(-50))
        .force("center", d3.forceCenter(width / 2, height / 2)) // center force to image center
        .force("collide", d3.forceCollide().radius(80)); // prevents overlapping of nodes

    // Create the links
    const link = svg.append("g")
        .data(graph.links)
        .attr("class", "links")
        .selectAll("line")
        .data(graph.links)
        .enter().append("line")
        .attr("stroke-width", 2)
        .attr("class", d => `links ${d.label}d3`) // Add class from data
        .attr("marker-end", "url(#arrowhead)");

    // Create node groups to hold both rectangle and text
    const nodeGroup = svg.append("g")
        .attr("class", "nodes")
        .selectAll("g")
        .data(graph.nodes)
        .enter()
        .append("g")
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));

    // Add text first (to measure it for rectangle sizing)
    const nodeLabels = nodeGroup.append("text")
        .attr("class", "node-labels")
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "central")
        // .attr("fill", "white")
        //    .attr("font-size", "12px")
        .attr("pointer-events", "none")
        .text(d => d.name);

    // Calculate text dimensions and store them in the data
    nodeGroup.each(function (d) {
        const bbox = this.querySelector("text").getBBox();
        d.width = bbox.width + 20;  // Add padding
        d.height = bbox.height + 10;  // Add padding
    });

    // Add rectangles to each node group with dimensions based on text size
    const rectangles = nodeGroup.insert("rect", "text")  // Insert before text (so text is on top)
        .attr("width", d => d.width)
        .attr("height", d => d.height)
        .attr("class", d => d.typ)
        .attr("x", d => -d.width / 2)  // Center rectangle on origin.pen
        .attr("y", d => -d.height / 2)  // Center rectangle on origin
        //.attr("rx", 5)  // Rounded corners
        //.attr("ry", 5)  // Rounded corners
        //.attr("fill", d => d3.schemeCategory10[d.id % 10])
        .attr("stroke", "#ff0")
        .attr("fill", "white")
        .attr("stroke-width", 1.5);

    // Add edge labels
    const edgeLabels = svg.append("g")
        .selectAll("text")
        .data(graph.links) // needed to be able to access to "d"
        .enter().append("text")
        .attr("text-anchor", "middle")
        .attr("class", d => `edge-labels ${d.label}textd3`) // Add class from data
        .text(d => d.label);

    // Update positions on each tick of the simulation
    simulation.on("tick", () => {
        // Update link positions
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => {
                // Calculate the point where the link meets the rectangle
                const dx = d.target.x - d.source.x;
                const dy = d.target.y - d.source.y;
                const angle = Math.atan2(dy, dx);

                // Half width and height of target rectangle
                const w = d.target.width / 2;
                const h = d.target.height / 2;

                // Determine intersection point with rectangle
                let x;
                if (Math.abs(Math.tan(angle) * w) <= h) {
                    // Intersects with left or right side
                    x = d.target.x - Math.sign(dx) * w;
                } else {
                    // Intersects with top or bottom side
                    x = d.target.x - Math.sign(dx) * h / Math.tan(angle);
                }
                return x;
            })
            .attr("y2", d => {
                // Calculate the point where the link meets the rectangle
                const dx = d.target.x - d.source.x;
                const dy = d.target.y - d.source.y;
                const angle = Math.atan2(dy, dx);

                // Half width and height of target rectangle
                const w = d.target.width / 2;
                const h = d.target.height / 2;

                // Determine intersection point with rectangle
                let y;
                if (Math.abs(Math.tan(angle) * w) <= h) {
                    // Intersects with left or right side
                    y = d.target.y - Math.tan(angle) * Math.sign(dx) * w;
                } else {
                    // Intersects with top or bottom side
                    y = d.target.y - Math.sign(dy) * h;
                }
                return y;
            });

        // Update the position of the entire node group
        nodeGroup
            .attr("transform", d => `translate(${d.x}, ${d.y})`);

        edgeLabels
            .attr("x", d => (d.source.x + d.target.x) / 2)
            .attr("y", d => (d.source.y + d.target.y) / 2);
    });

    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

function runcommand(params) {
    //URL_BASE = 'http://' + window.location.host + '/read';
    URL_BASE = '/js';
    //$("#resultat").empty(); // vider le div

    $.ajax({
        url: URL_BASE, // + "json", //+'/foo/fii?fuu=...',
        type: 'GET',
        data: params, //{ "num": sentnum,  },
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
            console.log("BEFORE ", graph);
            console.log("SUCCESS ", data);

            graph = data.graph;
            $("#cursentence").text(data.sentence);
            //graph["nodes"] = 
            //graph["links"] = 
            $("#pmgraph").empty();
            // need append to see formatting
            $("#pmgraph").append(highlight_pm(data.penman));
            $("#sentnum").val(data.num);
            showme();
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

$(".walk").click(function () {
    //console.log("EEE", this.id);
    if (this.id === "next") {
        var n = parseInt($("#sentnum").val(), 10) + 1;
        console.log("NN", n);
        $("#sentnum").val(n);
        params = { "num": n };
    }
    else if (this.id === "preceding") {
        var n = parseInt($("#sentnum").val(), 10) - 1;
        if (n == 0) {
            n = 1;
        }
        $("#sentnum").val(n);
        params = { "num": n };
    }
    else if (this.id === "first") {
        params = {
            "direction": this.id,
            "num": $("#sentnum").val()
        };
    }
    else if (this.id === "last") {
        params = {
            "direction": this.id,
            "num": $("#sentnum").val()
        };
    }
    else if (this.id === "lire") {
        params = { "num": $("#sentnum").val() };
    }
    runcommand(params);
});

$("#sentnum").keyup(function (event) {
    if (event.keyCode === 13) {
        runcommand({ "num": $("#sentnum").val() });
    }
});

$(document).ready(function () {
    // start animation once page is loaded
    runcommand({ "num": $("#sentnum").val() });
})