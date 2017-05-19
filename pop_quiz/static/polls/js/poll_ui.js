// the js within uses d3v4.js

// resolve the appropriate websocket protocol and create a connection
var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
var ws_path = ws_scheme + '://' + window.location.host;
socket = new ReconnectingWebSocket(ws_path);
poll_status = null;

// render a poll from scratch
function render_poll(data) {
	
	width = 420;
	barHeight = 50;

    // make refence to the chart svg and set the size parameters
	chart = d3.select(".chart");
	chart.attr("viewBox", "0 0 " + width + " " + ((barHeight + 25 + 5) * data.length - 5));
	
	x = d3.scaleLinear()
		.domain([0, vote_limit]) # overall vote range
		.range([12, width]); # bar range starts at 12 to fill space bihind a 0

	// create a bar graphic for each choice
	bar = chart.selectAll("g")
		.data(data)
	  .enter().append("g")
		.attr("id", function(d) { return d.id; })
		.attr("transform", function(d, i) {
			if(i > 0) { return "translate(0," + ((i * barHeight) + ((i+1) * 25) + (i * 5)) + ")"; }
			else { return "translate(0," + 25 + ")"; }
		})
		.on("click", function(d) {
			if((has_voted == false || one_vote_only == false) && poll_status == true){
				socket.send(JSON.stringify({
					"vote": true,
					"question_id": question_id,
					"choice_id": parseInt(d3.select(this).attr("id"))
				}));
			}
		});

    // choice bar background
	bar.append("rect")
		.attr("width", width)
		.attr("height", barHeight - 1)
		.attr("fill", "lightskyblue");

    // choice vote tally bar
	bar.append("rect")
		.attr("class", "votes_bar")
		.attr("width", function(d) { return x(d.votes); })
		.attr("height", barHeight - 1)
		.attr("fill", "steelblue");

    // choice vote tally text
	bar.append("text")
		.attr("class", "votes_text")
		.attr("x", function(d) { return x(d.votes) - 3; })
		.attr("y", barHeight / 2)
		.attr("dy", ".35em")
		.text(function(d) { return d.votes; });

    // create a label graphic for each choice label
	labels = chart.append("g")
	  .selectAll("text")
		.data(data)
	  .enter().append("text")
		.attr("class", "label_text")
		.attr("transform", function(d, i) {
			if(i > 0) { return "translate(2," + ((i * barHeight) + ((i+1) * 25) + (i * 5)  - 6) + ")"; }
			else { return "translate(2," + 19 + ")"; }
		})
		.text(function(d) { return d.choice_text; });
}
// initialise undo button
function button() {
	undo_button = d3.select(".btn");
	undo_button.on("click", function() {
		if(undo_button.classed("disabled") == false) {
			socket.send(JSON.stringify({"undo": true, "question_id": question_id}));
		}
	});
}
// update the statas of the poll display
function update_poll(data) {
	bar.data(data)
	bar.select(".votes_bar")
		.attr("width", function(d) { return x(d.votes); });
	bar.select("text")
		.attr("x", function(d) { return x(d.votes) - 3; })
		.text(function(d) { return d.votes; });

}
// clear poll display
function refresh_poll() {
	chart.selectAll("g").remove();
	if(typeof(undo_button) !== 'undefined') {
		undo_button.classed('active', true);
		undo_button.classed('disabled', true);
		undo_button.classed('hidden', true);
	}
}
// when a particular key is recieved via websocket
// alter the poll view accordingly
socket.onmessage = function(message) {
	json_data = JSON.parse(message.data);
	console.log(json_data);
	// update the poll to show vote changes
	if("poll_update" in json_data) {
		data = json_data['poll_update']
		update_poll(data);
	}
	// vote confirm is used in one vote only mode
	else if("vote_confirm" in json_data) {
		has_voted = true;
		d3.select(".panel-body").text("your vote has been tallied.");
		if(typeof(undo_button) !== 'undefined') {
			undo_button.classed('active', false);
			undo_button.classed('disabled', false);
		}
	}
	// undo confirm is used in one vote only mode
	else if("undo_confirm" in json_data) {
		has_voted = false;
		d3.select(".panel-body").text("spend your vote wisely before the poll closes.");
		if(typeof(undo_button) !== 'undefined') {
			undo_button.classed('active', true);
			undo_button.classed('disabled', true);
		}
	}
	// poll is closed for voting but still visible
	else if("poll_closed" in json_data) {
		poll_status = false;
		d3.select(".panel-title").text("voting has closed");
		d3.select(".panel-body").html("voting has closed for the current poll.<br/>a fresh poll will open soon.");
		if(typeof(undo_button) !== 'undefined') {
			undo_button.classed('active', true);
			undo_button.classed('disabled', true);
			undo_button.classed('hidden', true);
		}
	}
	// poll has completely expired
	else if("poll_ended" in json_data) {
		poll_status = null;
		d3.select("h2").text("Pop Quiz");
		d3.select(".panel-title").text("the polls have closed");
		d3.select(".panel-body").html("There isn't a poll running at the moment!");
		refresh_poll();
	}
	// a new poll is beginning
	else if("poll_opening" in json_data) {
		poll = json_data.poll_opening;

		data = poll['choices'];
		one_vote_only = poll['one_vote_only'];
		has_voted = poll['has_voted'];
		vote_limit = poll['vote_limit'];
		question_text = poll['question_text'];
		question_id = poll['question_id'];

		d3.select("h2").text(question_text);
		if(one_vote_only) {
			d3.select(".panel-title").text("one vote only");
			d3.select(".panel-body").html("votes are limited to one per person.");
		}
		else {
			d3.select(".panel-title").text("the polls are open");
			d3.select(".panel-body").html("vote as many times as you like.");
		}
		if(poll_status == false) {
			refresh_poll();
		}
		render_poll(data);
		if(one_vote_only == true) {
			if(typeof(undo_button) == 'undefined') {
				button();
			}
			undo_button.classed('hidden', false);
			if(has_voted !== true) {
				undo_button.classed('active', true);
				undo_button.classed('disabled', true);
			}
		}
		poll_status = true;
	}
}
