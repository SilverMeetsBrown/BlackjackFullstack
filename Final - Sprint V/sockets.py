from appConfig import *
from database import *
from tempData import *

def countdownThread(room):
    rooms[room].reset()
    time.sleep(COUNTDOWN_TIMER)
    socketio.emit('starting', to=room)
    time.sleep(START_WAIT)
    socketio.emit('startGame', to=room)
    with app.app_context():
        beginGame(room)
        
def beginGame(roomNum):
    room = rooms[roomNum]
    for i in range(2):
        room.dealAll()
    forcedScenarios(roomNum)
    playerTurn(roomNum)
    
def forcedScenarios(roomNum):
    try:
        room = rooms[roomNum]
        dealer = room.players[0].hands[0]
        player = room.players[1].hands[0]
        if (FORCE_DEALER_BLACKJACK):
            card = Card.query.filter_by(name='King of Hearts').first()
            room.replaceCard(dealer, 0, card)      
        if (FORCE_DEALER_ACE or FORCE_DEALER_BLACKJACK):
            card = Card.query.filter_by(name='Ace of Spades').first()
            room.replaceCard(dealer, 1, card)  
        if (FORCE_FIRST_PLAYER_BLACKJACK or FORCE_FIRST_PLAYER_SPLIT):
            card = Card.query.filter_by(name='King of Diamonds').first()
            room.replaceCard(player, 0, card)    
            if (FORCE_FIRST_PLAYER_BLACKJACK):
                card = Card.query.filter_by(name='Ace of Clubs').first()
                room.replaceCard(player, 1, card) 
            else:
                card = Card.query.filter_by(name='Queen of Hearts').first()
                room.replaceCard(player, 1, card)
    except Exception:
        pass


def playerTurn(roomNum):
    room = rooms[roomNum]
    room.getNextHand()
    hand = room.currentHand
    active = hand.active
    if (len(room.currentHand.cards) != 0):
        socketio.emit('cards', room.getJSON(), to=roomNum)
        time.sleep(TURN_COUNTDOWN)
        if (room.currentHand == hand and hand.active == active):
            hand.firstRoundActive = False
            hand.active = False
            hand.bet = 0
            hand.insurance = False
            playerTurn(roomNum)
    else:
        if (room.firstRound):
            room.firstRound = False
            playerTurn(roomNum)
        else:
            dealerTurn(roomNum)
        
def dealerTurn(roomNum):
    room = rooms[roomNum]
    dealer = room.players[0].hands[0]
    dealer.total = dealer.getTotal(0)
    while(dealer.total < 17):
        room.dealCard(dealer)
    socketio.emit('end', room.getEndJSON(), to=roomNum)
    
def emitMoney(userID, handID, roomNum, betMultiplier, sid):
    room = rooms[roomNum]
    hand = room.getPlayer(userID).hands[handID]
    dict = {}
    dict['userID'] = userID
    dict['money'] = findAndAddMoney(userID, math.floor(int(hand.bet) * betMultiplier))
    socketio.emit('money', json.dumps(dict), to=sid)
    
    

@socketio.on('beginCountdown')
def beginCountdown(roomNum):
    socketio.emit('countdownStarted', roomNum, to=roomNum)
    threading.Thread(target=countdownThread, args=(roomNum,)).start()

@socketio.on('joinRoom')
def joinRoom(userID, roomNum, username, previousRoom):
    if (previousRoom != '-1'):
        previousRoom = int(previousRoom)
        room = rooms[previousRoom]
        leave_room(previousRoom)
        room.removePlayer(userID)
        socketio.emit('playerList', json.dumps({'roomJSON':room.getJSON(), 'roomNum':previousRoom}), to=previousRoom)
    join_room(roomNum)
    room = rooms[roomNum]
    room.addPlayer(userID, username)
    socketio.emit('playerList', json.dumps({'roomJSON':room.getJSON(), 'roomNum':roomNum}), to=roomNum, namespace='/')
    socketio.emit('joinSuccess', room.gameInProgress, to=request.sid)
    
@socketio.on('bet')
def returnBet(userID, roomNum, bet):
    bet = int(bet)
    room = rooms[roomNum]
    hand = room.getPlayer(userID).hands[0]
    hand.bet = bet
    hand.active = True
    hand.firstRoundActive = True
    emitMoney(userID, 0, roomNum, -1, request.sid)

@socketio.on('hit')
def hit(userID, roomNum):
    room = rooms[roomNum]
    room.dealCard(room.currentHand)
    socketio.emit('cards', room.getJSON(), to=roomNum)
        
@socketio.on('endTurn')
def endTurn(roomNum):
    playerTurn(roomNum)
    
@socketio.on('doubleDown')
def doubleDown(userID, handID, roomNum):
    room = rooms[roomNum]
    hand = room.getPlayer(userID).hands[handID]
    bet = hand.bet
    emitMoney(userID, handID, roomNum, -1, request.sid)
    hand.bet = bet * 2
    
@socketio.on('split')
def split(userID, betAmount, roomNum):
    room = rooms[roomNum]
    room.split(userID, int(betAmount))
    dict = {}
    dict['money'] = findAndAddMoney(userID, int(betAmount)*-1)
    dict['userID'] = userID
    socketio.emit('money', json.dumps(dict), to=request.sid)
    
@socketio.on('insurancePayout')
def insurancePayout(userID, roomNum):
    room = rooms[roomNum]
    dealer = room.players[0].hands[0]
    player = room.getPlayer(userID)
    print('test1')
    if (dealer.total == 21 and len(dealer.cards)==2):
        print('test2')
        for i, hand in enumerate(player.hands):
            if (hand.insurance):
                print('test3')
                emitMoney(userID, i, roomNum, 2, request.sid)
    
@socketio.on('insuranceCost')
def insuranceCost(userID, handID, roomNum):
    rooms[roomNum].getPlayer(userID).hands[handID].insurance = True
    emitMoney(userID, handID, roomNum, -1, request.sid)
    
@socketio.on('blackjack')
def blackjack(userID, handID, roomNum):
    room = rooms[roomNum]
    hand = room.getPlayer(userID).hands[handID]
    hand.bet = math.floor(hand.bet * 1.5)
    hand.firstRoundActive = False
    hand.active = False
    
@socketio.on('bust')
def bust(userID, handID, roomNum, trueBust):
    room = rooms[roomNum]
    player = room.getPlayer(userID)
    hand = player.hands[handID]
    hand.firstRoundActive = False
    hand.active = False
    if (not trueBust):
        emitMoney(userID, handID, roomNum, 0.5, request.sid)
    hand.bet = 0
    socketio.emit('bust', {'trueBust':trueBust, 'userID':userID}, to=request.sid)
        
@socketio.on('endStatus')
def endStatus(userID, handID, roomNum, win):
    emitMoney(userID, handID, roomNum, 2 if win else 1, request.sid)
    
@socketio.on('unload')
def unload(roomNum, userID):
    room = rooms[roomNum]
    room.removePlayer(userID)
    socketio.emit('cards', room.getJSON(), to=roomNum)
    
    

