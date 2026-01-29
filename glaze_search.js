/*
Scripting for the browser UI for the glaze search software-
	implements the transmission of search strings and variables, display of recipe cards,
	and entry of new recipes for submission to the database
*/

//Timer variables - Mostly to ensure it's not crashing
let clock;
d = new Date();
i_time = d.getTime();

//Start supervisor on 100Hz rate
setInterval(tickTock,10)

//websockets message string
let WSmessage;
WSmessage = "";

//Open the websocket- 8080 on localhost
sock = new WebSocket('ws://127.0.0.1:8080');

//Attach event handlers for websocket
sock.onmessage = function(event){onReply(event);}; //The main one to handle connections

//List of ingredients entered in a new recipe, and the count of added ingredients
ingrs = [];
ingr_ct = 0;

//Object URL for the image object
let objectURL;
objectURL = null; //local URL of image
loadImage = null; //Loaded image itself

//Supervisor routine
function tickTock(){
	//Update time
	d = new Date();
	clock = d.getTime()-i_time;
	document.getElementById('clock').innerHTML=(clock/1000.0)+"s";

	updateCard(); //Update the card if necessary

}

//Handle a reply from the server
function onReply(event){

	//Grab data from the event
	WSmessage=event.data;

	//Starting with & is a search results list
	if (WSmessage.charAt(0) == "&"){
		i=0; //Loop over message, entries delimited with | between number of results and list HTML
		while (WSmessage.charAt(i) != "|"){
			i=i+1;
		}
		//Put the number into its box and the results into the result list
		document.getElementById("numResults").innerHTML = WSmessage.substring(1,i);
		document.getElementById("listResults").innerHTML = WSmessage.substring(i+1,WSmessage.length);
	}
	
	//Starting with % is a specific card
	else if (WSmessage.charAt(0) == "%"){
		//Put the card into the result box
		document.getElementById("resultCard").innerHTML = WSmessage.substring(1,WSmessage.length);	
	}

	//Starting with a # is an image
	else if (WSmessage.charAt(0) == "#"){
		sendImage(); //Call the function to send a base64 image to the server
	}

}


//Function to fetch an image
function getIm(){
	//Grab the file handler from the image element
	files = document.getElementById("theImage").files;

	//If there's some files available
	if (files.length > 0){
		file = files[0] //Grab only the first one
		loadImage = file;
		//alert(file.name);
		if (objectURL!=null){URL.revokeObjectURL(objectURL);} //Remove the previous objectURL if there is one
		objectURL = window.URL.createObjectURL(file); //Make a new objectURL for the new image
		document.getElementById('img').src = objectURL; //Put it into the image variable in the DOM
		setTimeout(()=>{isReady = true;},200); //A 200ms delay before marking the file as ready, for load-in time
		prevData = [];
	}
	else{alert("NO FILE!!!");} //If there's not a file loaded, let the user know!
}

//Function to download an image directly - I feel like this is kludgy
function downloadImage(name) {
    const imageUrl = objectURL; //Grab the image from the local URL
    const link = document.createElement('a'); //Make a link object
    link.download = name+'.jpg'; //Create a download title
    link.href = imageUrl; //Set the link object to point to the image URL
    document.body.appendChild(link); //Stick the object in invisibly
    link.click(); //'click' it, runs the download directly
    document.body.removeChild(link); //Take it back out
}

//Function to send a new recipe card made in the UI back to the server
function sendCard(){
	//Grab the name, type, and other card info directly
	type = document.getElementById('{type}').value;
	name = document.getElementById('{name}').value;
	cone = document.getElementById('{cone}').value;
	surface = document.getElementById('{surface}').value;
	transparency = document.getElementById('{transparency}').value;	

	//Two ways to get image- currently sending base64
	imglk = loadImage.name
	//downloadImage(name) //Can also download direct

	//Base string for ingredient list
	ingrs = ""

	//loop over the ingredient div elements
	i = 0;
	while (i < ingr_ct){ //loop over the tracked number of ingredients
		if (document.getElementById("ing"+i+"I")){ //If there is an ith element (to support deletion later)
			ingrs = ingrs + document.getElementById("ing"+i+"I").innerHTML + ","; //Grab the ingredient name
			ingrs = ingrs + document.getElementById("ing"+i+"A").innerHTML + ","; //Grab the ingredient amount
		}
		i = i + 1; //Step to next ingredient
	}
	ingrs = ingrs.substring(0,ingrs.length-1); //Take off the last trailing comma

	//Construct the full data message
	msg = "#"+name+","+type+","+cone+","+surface+","+transparency+","+imglk+","+ingrs;

	//alert(msg); //Debug
	sock.send(msg) //Send the whole message to the server
}

//Wrapper to send an image
function sendImage(){
	sock.send(loadImage); //Build in function sends image files as encodings!
}

//Function to set up for adding a new card
function addNew(){
	ingrs = []; //Refresh ingredients list
	ingr_ct = 0; //Refresh ingredients counter
	sock.send("$"); //Send notice to the server
}

//Function to update the new card as we build it- polled update
function updateCard(){

	if (document.getElementById('#type')){ //If there's a type entry field, we're making a new card
		//Set all the display fields to their corresponding entry box!
		document.getElementById('#type').innerHTML = document.getElementById('{type}').value;
		document.getElementById('#type2').innerHTML = document.getElementById('{type}').value;
		document.getElementById('#name').innerHTML = document.getElementById('{name}').value;
		document.getElementById('#cone').innerHTML = document.getElementById('{cone}').value;
		document.getElementById('#surface').innerHTML = document.getElementById('{surface}').value;
		document.getElementById('#transparency').innerHTML = document.getElementById('{transparency}').value;
	}
}

//Function to add a new ingredient to the list of a new card
function addIngr(){
	//Get the current ingredient list
	ing_curr = document.getElementById('#ingredients').innerHTML
	
	//Get the new ingredient name and amount from the entry boxes
	ing_n = document.getElementById('{ingr}').value;
	ing_amt = document.getElementById('{amt}').value;

	//Append formatted HTML to the current ingredient display code
	ing_curr = ing_curr + "<div style=\"display:flex;\" id=\"ing"+ingr_ct+"\">" //New dive box for the line

		//New ingredient name span
		ing_curr = ing_curr + "<span style=\"width:50%;\" id=\"ing"+ingr_ct+"I\">" //Note we ID the lines by the ingredient count for later fetching
			ing_curr = ing_curr + ing_n
		ing_curr = ing_curr + "</span>"

		//New ingredient amount span
		ing_curr = ing_curr + "<span style=\"width:50%;text-align:right;\" id=\"ing"+ingr_ct+"A\">"
			ing_curr = ing_curr + ing_amt
		ing_curr = ing_curr + "</span>"

	//Close the dive for this line
	ing_curr = ing_curr + "</div>"

	ingr_ct = ingr_ct + 1; //Increment count of ingredients
	document.getElementById('#ingredients').innerHTML = ing_curr //Update the list in the document
}

//Wrapper to check if enter is pressed in the search box
function getEnter(e){
	if (e.keyCode == 13){
		sendSearch(); //Fire off a search for that
	}
}

//Wrapper to check if enter is pressed on the ingredients box
function keyAddIngr(e){
	if (e.keyCode == 13){
		addIngr(); //Add the ingredient if it is
	}
}

//Function to send a search category and string to the server
function sendSearch(){
	//Grab the category and text
	cat = document.getElementById("search").value;
	txt = document.getElementById("searchInput").value;

	//Diagnostic display of sent search
	//document.getElementById("vcheck").innerHTML = cat + "," + txt;

	//Send the search request
	sock.send("&"+cat + "," + txt);
}

//Function to request a specific recipe card from the server
function sendReq(n){
	sock.send("%"+n); //Send the request
	
	//Note the card is being fetched- lingers in the odd case where you have to download a new image
	document.getElementById("resultCard").innerHTML = "<div style=\"color:darkgreen;\">Fetching card...</div>"
}



