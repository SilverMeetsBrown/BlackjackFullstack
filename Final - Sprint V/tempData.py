from appConfig import *
from database import *

class Hand():
    def __init__(self, bet=0):
        self.active = False
        self.firstRoundActive = False
        self.cards = []
        self.total = 0
        self.dealerTotal = 0
        self.bet = bet
        self.insurance = False
    
    def addCard(self, card):
        self.cards.append(card)
        self.total = self.getTotal(0)
        self.dealerTotal = self.getTotal(1)
        
    def getTotal(self, start):
        total = 0
        aces = 0
        for i in range(start, len(self.cards)):
            card = self.cards[i]
            total += card.value
            aces += 1 if (card.value) == 1 else 0
        total += 10 if (aces != 0) and (total+10 <= 21) else 0
        return total
    
    def getCards (self, start):
        dict = {}
        dict['total'] = self.getTotal(start)
        dict['size'] = len(self.cards)
        cards = {}
        for i in range(len(self.cards)):
            card = self.cards[i]
            cards[i] = card.img
        dict['cards'] = cards
        return dict
            
class Player():
    def __init__(self, userID, username):
        self.userID = userID
        self.username = username
        self.hands = [Hand()]
        
    def getJSON(self, currentHand):
        playerDict = {}
        playerDict['username'] = self.username
        highlight = 'OUT' if len(self.hands[0].cards) == 0 else 'IN'
        allHands = {}
        for x, hand in enumerate(self.hands):
            highlight = 'FOCUS' if hand == currentHand else highlight
            allHands[x] = hand.getCards(0)
        playerDict['allHands'] = allHands
        playerDict['highlight'] = highlight
        return playerDict


class Room():      
    def __init__(self, index):
        self.index = index
        self.players = []
        self.shoe = []
        self.noCurrentPlayer()
        self.cardCount = 1
        self.gameInProgress = False
        self.firstRound = True
        self.addPlayer(-1)
        self.shuffle()
        
    def noCurrentPlayer(self):
        self.currentHand = Hand()
        self.currentUserID = None
        self.currentUsername = None
        self.handID = -1;
        
    
    def getNextHand(self):
        for i in range(1,len(self.players)):
            player = self.players[i]
            for x in range(len(player.hands)):
                hand = player.hands[x]
                active = hand.firstRoundActive if self.firstRound else hand.active
                if (active):
                    self.currentHand = hand
                    self.handID = x
                    self.currentUserID = player.userID
                    self.currentUsername = player.username
                    if (self.firstRound):
                        hand.firstRoundActive = False
                    else:
                        hand.active = False
                    return hand
        self.noCurrentPlayer()
        return None
        
    def getJSON(self):
        dict = {}
        dict['dealer'] = self.players[0].hands[0].getCards(1)
        dict['hand'] = self.currentHand.getCards(0)
        dict['handID'] = self.handID
        dict['canSplit'] = (len(self.currentHand.cards)==2 and
                            self.currentHand.cards[0].value == self.currentHand.cards[1].value)
        dict['userID'] = self.currentUserID
        dict['username'] = self.currentUsername
        dict['firstRound'] = self.firstRound
        dict['roomNum'] = self.index
        dict['allPlayers'] = self.getAllCardsJSON()
        dict['gameInProgress'] = self.gameInProgress
        return json.dumps(dict)
    
    def getAllCardsJSON(self):
        dict = {}
        for i, player in enumerate(self.players, -1):
            dict[i] = player.getJSON(self.currentHand)
        del dict[-1]
        return dict
    
    def getEndJSON(self):
        dict = {}
        dealer = self.players[0].hands[0]
        dict['dealer'] = dealer.getCards(0)
        dict['blackjack'] = (dealer.total == 21 and len(dealer.cards) == 2)
        dict['roomNum'] = self.index
        users = {}
        for player in self.players:
            hands = {}
            for i in range(len(player.hands)):
                hands[i] = player.hands[i].total
            users[player.userID] = hands
        dict['users'] = users
        return json.dumps(dict)
        
    def getPlayerIndex(self, userID):
        for i in range(len(self.players)):
            if self.players[i].userID == userID:
                return i
            
    def getPlayer(self, userID):
        return self.players[self.getPlayerIndex(userID)]
    
    def getUsernames(self):
        users = [player.username for player in self.players]
        del users[0]
        return users
    
    def shiftPlayers(self):
        shift = []
        shift.append(self.players[0])
        for i in range(1,len(self.players)):
            if (self.players[i].userID != None):
                shift.append(self.players[i])
        self.players = shift
    
    def addPlayer(self, userID, username='Dealer'):
        player = Player(userID, username)
        self.players.append(player)
        self.shiftPlayers()
        
    def removePlayer(self, userID):
        userIndex = self.getPlayerIndex(userID)
        if (userIndex != None):
            del self.players[userIndex]
            self.shiftPlayers()
        
    def shuffle(self):
        with app.app_context():
            self.cardCount = 1
            self.shoe = []
            cards = Card.query.all()
            for _ in range(DECKS_IN_SHOE):
                self.shoe +=cards
            random.shuffle(self.shoe)
        
    def dealCard(self, hand):
        card = self.shoe[self.cardCount]
        hand.addCard(card)
        self.cardCount += 1

    def dealAll(self):
        self.gameInProgress = True
        for player in self.players:
            card = self.shoe[self.cardCount]
            self.cardCount += 1
            player.hands[0].cards.append(card)
            
    def split(self, userID, betAmount):
        player = self.getPlayer(userID)
        originalHand = player.hands[0]
        newHand = Hand(betAmount)
        newHand.cards.append(None)
        newHand.cards.append(None)
        originalHand.firstRoundActive = True
        newHand.firstRoundActive = True
        newHand.active = True
        newHand.cards[0] = originalHand.cards[1]
        self.splitCardDeal(newHand)
        self.splitCardDeal(originalHand)
        player.hands.append(newHand)

    
    def splitCardDeal(self, hand):
        card = self.shoe[self.cardCount]
        self.cardCount += 1
        self.replaceCard(hand, 1, card)
    
    def replaceCard(self, hand, index, card):
        hand.cards[index] = card
        hand.total = hand.getTotal(0)
        hand.dealerTotal = hand.getTotal(1)
            
    def reset(self):
        for player in self.players:
            player.hands = [Hand()]
        self.shuffle()
        self.noCurrentPlayer()
        self.gameInProgress = False
        self.firstRound = True
        
rooms = [Room(0)]
