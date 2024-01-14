var userID = null, room = -1, bet = 0, total = 0, dealerTotal = 0, handID = -1;
var socket = io.connect({closeOnBeforeunload: false})

window.addEventListener('DOMContentLoaded', function(){
	room = parseInt(document.getElementById('roomNum').innerHTML);
	userID = parseInt(document.getElementById('userID').innerHTML);
	username = document.getElementById('username').innerHTML;
	previousRoom = document.getElementById('previousRoom').innerHTML;
	if (room != -1) {
		socket.emit('joinRoom', userID, room, username, previousRoom);
	} else {
		button = document.getElementById('roomDiv');
		button.setAttribute('style', 'border-style: dashed; border-color: #ffff33; border-width: 5px;');
	}
});

window.onbeforeunload = function() {
	socket.emit('unload', room, userID);
};

socket.on('playerList', function(json) {
	info = JSON.parse(json);
	if (info['roomNum']!=room) return false;
	info = JSON.parse(info['roomJSON']);
	setPlayers(info['allPlayers'])
});

socket.on('money', function(json) {
	info = JSON.parse(json);
	if (info['userID'] == userID) {
		p = document.getElementById('money');
		document.getElementById('betAmount').setAttribute('max', info['money']);
		p.innerHTML = "$" + info['money'].toString();
	}
});

socket.on('joinSuccess', function(gameInProgress) {
	if (!gameInProgress) readyForCountdown();
	else hideElement('message', true);
});

socket.on('countdownStarted', function(roomNum) {
	if (roomNum != room) return false;
	hideElement('startCountdown', true);
	hideElement('placeBet', false);
	reset();
	return true;
});

socket.on('starting', function(roomNum) {
	if (roomNum = room) return false;
	hideElement('message', true);
	return true;
});


socket.on('end', function(json) {
	info = JSON.parse(json)
	if (info['roomNum'] != room) return false;
	setCards(info, true, true);
	dealerTotal = info['dealer']['total'];
	readyForCountdown();

	if (info['blackjack']) {
		socket.emit('insurancePayout', userID, room);
	}

	userHands = info['users'][userID];
	for (i = 0; i < Object.keys(userHands).length; i++) {
		userTotal = userHands[i];
		if ((dealerTotal > 21 || userTotal > dealerTotal)){
			socket.emit('endStatus', userID, i, room, true);
		} else if (dealerTotal == userTotal) {
			socket.emit('endStatus', userID, i, room, false);
		}
	}
	return true;
});

socket.on('cards',function(json) {
	info = JSON.parse(json);
	if (info['roomNum'] != room) return false;

	hideElement('message', true);
	hideElement('placeBet', true);
	hideElement('actions', true);
	hideElement('specialActions', true);
	setCards(info, true, false);
	setCards(info, false, false);
	setPlayers(info['allPlayers']);
	handID = info['handID'];

	if (info['userID'] == userID) {
		userTotal = info['hand']['total'];
		userCards = info['hand']['cards'];
		dealerTotal = info['dealer']['total'];
		if (info['firstRound']) {					
			if (userTotal == 21) {
				socket.emit('blackjack', userID, handID, room);
				endTurn();
			}
			else {
				hideElement('specialActions', false);
				disableElements(["doubleButton", "surrenderButton"], false);
				if (dealerTotal == 11) {
					disableElements(['insuranceButton'], false);
				}
				if (info['canSplit']) {
					disableElements(['splitButton'], false);	
				}
			}
		} else {
			hideElement('actions', false);
		}
		if (userTotal == 21) {
			socket.emit('stand', userID, room);
		} else if (userTotal > 21) {
			socket.emit('bust', userID, handID, room, true);
		}
	}
	return true;
});

function setPlayers(info) {
	playersDiv = document.getElementById('players')
	clearChildren(playersDiv);
	for (i = 0; i < Object.keys(info).length; i++) {
		player = info[i]

		if (player['highlight'] == 'OUT' || player['highlight'] == null) color = '#aaaaaa';
		else if (player['highlight'] == 'FOCUS') color = '#9999ee';
		else color = '#eeeeee';

		div = document.createElement('div');
		div.setAttribute('class', 'item table');
		div.setAttribute('id', 'playerItem');

		nameDiv = document.createElement('div');
		nameDiv.setAttribute('class', 'sideColumn item');
		nameDiv.innerHTML = player['username'];
		div.appendChild(nameDiv);

		subDiv = document.createElement('div');
		subDiv.setAttribute('class', 'mainColumn item');
		div.appendChild(subDiv);

		allHands = player['allHands'];
		handCount = Object.keys(allHands).length;
		div.setAttribute('style', 'max-height: ' + handCount*15 + '%;');
		for (x = 0; x < handCount; x++) {
			hand = allHands[x];
			handDiv = document.createElement('div')
			handDiv.setAttribute('style', 'max-height: ' + Math.floor(100/handCount) + '%;');
			handDiv.setAttribute('class', 'table');

			cardsDiv = document.createElement('div');
			cardsDiv.setAttribute('class', 'cell miniCards');
			displayCards(hand['cards'], cardsDiv, false);
			handDiv.appendChild(cardsDiv);

			totalDiv = document.createElement('div');
			totalDiv.setAttribute('class', 'total cell');
			totalP = document.createElement('p');
			totalP.innerHTML = hand['total'];
			totalDiv.appendChild(totalP);
			handDiv.appendChild(totalDiv);
			subDiv.appendChild(handDiv);

			handDiv.setAttribute('style', handDiv.getAttribute('style')+'background-color: ' + color +';');
			cardsDiv.setAttribute('style', 'background-color: ' + color +';');
		}

		subDiv.setAttribute('style', 'background-color: ' + color +';');
		nameDiv.setAttribute('style', 'background-color: ' + color +';');
		div.setAttribute('style', div.getAttribute('style')+'background-color: ' + color +';');

		playersDiv.appendChild(div);
	}
}


function setCards(info, isDealer, isEnd) {
	if (isDealer) {
		hideElement('dealerScore', false);
		cards = info['dealer']['cards'];
		total = info['dealer']['total'];
		cardDisplay = document.getElementById('dealerCards');
		scoreDisplay = document.getElementById('dealerScore');
		hideFirst = !isEnd
	} else {
		hideElement('userScore', false);
		cards = info['hand']['cards'];
		total = info['hand']['total'];
		cardDisplay = document.getElementById('userCards');
		scoreDisplay = document.getElementById('userScore');
		hideFirst = false;
	}

	clearChildren(cardDisplay);
	displayCards(cards, cardDisplay, hideFirst);
	scoreDisplay.innerHTML = total;
}

function displayCards(cards, div, hideFirst){
	for (j = 0; j < Object.keys(cards).length; j++) {
		if (hideFirst && j == 0) {
			imgSrc = 'static/hidden.png';
		} else imgSrc = "static/"+cards[j]+".png";
		img = document.createElement('img');
		img.setAttribute('src', imgSrc);
		img.setAttribute('class', 'card');
		div.appendChild(img);
	}
}

function clearChildren(div) {
	while(div.firstChild) {
		div.firstChild.remove();
	}
}

socket.on('bust', function(dict) {
	if (dict.userID == userID){
		document.getElementById('userScore').innerHTML += dict.trueBust ? "<br> Bust!" :  "<br> Surrendered.";
		endTurn();
	}
});

function readyForCountdown() {
	hideElement('startCountdown', false);
	hideElement('message', true);
	hideElement('actions', true);
	hideElement('specialActions', true);
}

function hideElement(id, bool) {
	element = document.getElementById(id);
	style = bool ? 'display:none;' : 'display:flex;';
	element.setAttribute('style', style);
}

function disableElements(elementIDs, bool) {
	for (i in elementIDs) {
		document.getElementById(elementIDs[i]).disabled = bool
	}
}

function joinGame() {
	bet = document.getElementById('betAmount').value;
	socket.emit('bet', userID, room, bet)
	hideElement('placeBet', true);
	hideElement('message', false);
	setMessage('Waiting...')
	return false;
}

function beginCountdown() {
	socket.emit('beginCountdown', room);
	return false;
}

function double() {
	disableElements(["surrenderButton", "doubleButton", "insuranceButton"], true);
	socket.emit('doubleDown', userID, handID, room);
	return false;
}

function hit() {
	socket.emit('hit', userID, room);
}

function endTurn() {
	disableElements(["surrenderButton", "doubleButton", "insuranceButton", 'splitButton'], true);
	hideElement('specialActions', true);
	hideElement('actions', true);
	socket.emit('endTurn', room);
}

function surrender() {
	socket.emit('bust', userID, handID, room, false)
}

function setInsurance(){
	disableElements(["insuranceButton", 'splitButton', 'doubleButton', 'surrenderButton'], true);
	socket.emit('insuranceCost', userID, handID, room);

}

function split(){
	disableElements(["splitButton"], true);
	socket.emit('split', userID, bet, room)
	socket.emit('endTurn', room);
}

function setMessage(message) {
	document.getElementById('message').innerHTML = message;
}

function reset() {
	clearChildren(document.getElementById('dealerCards'));
	clearChildren(document.getElementById('userCards'));
	disableElements(["hitButton", "standButton"], false);
	disableElements(['insuranceButton', 'surrenderButton'], true)
	hideElement('dealerScore', true);
	hideElement('userScore', true);
}