from appConfig import *
from appConfig import db, app

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(50))
    money = db.Column(db.Integer)
    roomID = db.Column(db.Integer)
    tempID = db.Column(db.Integer)
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.money = 1000
        
    def addMoney(self, amount):
        self.money += int(amount)
        db.session.commit()
        return self.money


class Card(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rank = db.Column(db.String(10))
    suite = db.Column(db.String(10))
    value = db.Column(db.Integer)
    name = db.Column(db.String(25))
    img = db.Column(db.String(25))
        
    def __init__(self, rank, suite, value, name, img):
        self.rank = rank
        self.suite = suite
        self.value = value
        self.name = name
        self.img = img
    
def createCards():
    for i in range(4):
        if (i==0):
            suite = "Spades"
        elif (i==1):
            suite = "Diamonds"
        elif (i==2):
            suite = "Clubs"
        elif (i==3):
            suite = "Hearts"
        
        for x in range(1,14):
            value = 10
            if (x==1):
                rank = "Ace"
                value = 1
            elif (x==11):
                rank = "Jack"
            elif (x==12):
                rank = "Queen"
            elif (x==13):
                rank = "King"
            else:
                rank = str(x)
                value = x
            name = rank + " of " + suite
            img = rank.lower() + "_of_" + suite.lower()
            card = Card(rank, suite, value, name, img)
            db.session.add(card)

def findAndAddMoney(userID, amount):
    user = User.query.filter_by(id=userID).first()
    user.addMoney(amount)
    return user.money

def getUser(userID):
    return User.query.filter_by(id=userID).first()

def loadDatabase():    
    try:
        db.drop_all()
        db.create_all()
        createCards()
        db.session.commit()
    except Exception as e:
        print("ERROR: Database Startup Failed")
        print(e)
        pass