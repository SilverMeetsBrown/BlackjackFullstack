from appConfig import *
from database import *
from tempData import *
from sockets import *

# ___LOGIN_START___

@login_manager.user_loader
def load_user(uid):
    user = User.query.get(uid)
    return user

@login_manager.unauthorized_handler
def unauthorized():
    print('ERROR: Unauthorized request. \nRedirecting...')
    return redirect('/login')

def login(formUsername, formPassword):
    try:
        user = User.query.filter_by(username=formUsername, password=formPassword).first()
        login_user(user)
        return user
    except:
        print("ERROR: Login failed.")
        return False

def signup(username, password):
    newUser = User(username, password)
    db.session.add(newUser)
    db.session.commit()
    return login(username, password)

# ___LOGIN_END___

# ___ROUTE_START___

@app.route('/')
def routeNone():
    return redirect('/login')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def routeLogin():
    if (request.method == 'POST'):
        formUsername = request.form.get('username')
        formPassword = request.form.get('password')
        
        if (request.form.get('action') == "Sign Up"):
            loginAttempt = signup(formUsername, formPassword)
        else:
            loginAttempt = login(formUsername, formPassword)
            
        if (loginAttempt):
            return redirect('/blackjack')
    return render_template('login.html')

@app.route('/blackjack', methods=['POST','GET'])
@login_required
def routeBlackjack():
    dict = getBlackjackJSON(current_user.id)
    if request.method=='POST':
        num = request.form.get('roomNum')
        if (num == 'new'):
            rooms.append(Room(len(rooms)))
            num = dict['rooms']
            dict['rooms'] += 1
        dict['currentRoom'] = num
        dict['previousRoom'] = request.form.get('previousRoom')
    return render_template('blackjack.html', json=dict)


def getBlackjackJSON(id):
    user = getUser(id)
    money = user.money
    dict = json.loads('{}')
    
    dict['money'] = str(money)
    dict['rooms'] = len(rooms)
    dict['currentRoom'] = -1
    dict['prevRoom'] = -1
    dict['players'] = []
    dict['username'] = user.username
    dict['userID'] = user.id
    
    return dict

# ___ROUTE_END___

# ___MAIN___
    
if __name__ == '__main__':
    if RESET:
        with app.app_context():
            loadDatabase()
    socketio.run(app)
    
# ___MAIN___