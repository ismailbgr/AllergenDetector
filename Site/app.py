from flask import Flask, render_template, request, redirect, url_for, flash,session
import pandas as pd
import pickle
import socket
import json

app = Flask(__name__)
# set the secret key.  keep this really secret:
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
client = None

isDebug = True

class User:
    def __init__(self,userid , personname,personsurname,username,telephoneno=None,height=None,weight=None):
        self.username = username
        self.personname = personname
        self.personsurname = personsurname
        self.telephoneno = telephoneno
        self.userid = userid
        self.weight = weight
        self.height = height

    def set_allergens(self,allergens):
        self.allergens = allergens

    def __repr__(self):
        return f"User('{self.userid}',{self.username}', '{self.personname}', '{self.personsurname}')"


@app.route("/", methods=['GET', 'POST'])
def home():
    global client
    if client is None:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((socket.gethostname(), 1214))
            print('Connected to server.')
        except Exception as e:
            print("Cannot connect to server.")
            flash('Connection Error.', category='error')
    return render_template('index.html')

@app.route("/search", methods=['POST'])
def search():
    if not isDebug:
        global client
        if request.method == 'POST':
            if client is None:
                flash('Connection Error.', category='error')
                print("Cannot connect to server.")
                return render_template("index.html")
            barkod = request.form['search']
            if not barkod.isdigit():
                flash('Barkod yalnızca sayı içerebilir.', category='error') 
                return render_template("index.html")
            message = "b"
            message += str(barkod)
            message = message.encode('utf-8')
            client.send(message)
            
            # TODO : add ERROR handling
            from_server = client.recv(4096)
            from_server = from_server.decode('utf-8')
            print("From server : ",from_server)

            if from_server == "ERROR":
                flash('Barkod bulunamadı.', category='error')
                return render_template("index.html")

            # return render_template('test.html', test=from_server)
            data = pd.read_json(from_server)
        return render_template('result.html', barcodeno=data['barcodeno'][0], foodname=data['foodname'][0], brand=data['brand'][0], weightvolume=data['weightvolume'][0], ingredients=data['ingredients'][0], fat=data['fat'][0], protein=data['protein'][0], carbs=data['carbs'][0], calorie=data['calorie'][0], allergennames=data['allergennames'][0])
    else:
        from_server = "[{\"barcodeno\":1,\"foodname\":\"ekmek\",\"brand\":\"firinci\",\"weightvolume\":200,\"ingredients\":\"un\",\"fat\":20,\"protein\":10,\"carbs\":75,\"calorie\":300,\"allergennames\":\"['gluten', 'findik']\"}]"
        data = pd.read_json(from_server)
        allergens = data["allergennames"][0].replace("'","\"")
        allergens = json.loads(allergens)
        return render_template('result.html', barcodeno=data['barcodeno'][0], foodname=data['foodname'][0], brand=data['brand'][0], weightvolume=data['weightvolume'][0], ingredients=data['ingredients'][0], fat=data['fat'][0], protein=data['protein'][0], carbs=data['carbs'][0], calorie=data['calorie'][0], allergens=allergens)

@app.route("/searchName", methods=['POST'])
def searchName():
    global isDebug
    if not isDebug:
        global client
        if request.method == 'POST':
            if client is None:
                flash('Connection Error.', category='error')
                print("Cannot connect to server.")
                return render_template("index.html")
            foodname = request.form['searchName']
            message = "s"
            message += foodname
            message = message.encode('utf-8')
            client.send(message)
            
            # TODO : add ERROR handling
            from_server = client.recv(4096)
            from_server = from_server.decode('utf-8')
            print("From server : ",from_server)

            if from_server == "ERROR":
                flash('Ürün adı bulunamadı.', category='error')
                return render_template("name_search.html")

            # return render_template('test.html', test=from_server)
            data = pd.read_json(from_server)
        return render_template('search_results.html', data=data)
    else:
        from_server = '[{\"barcodeno\":1,\"brand\":\"firinci\",\"foodname\":\"ekmek\"},{\"barcodeno\":2,\"brand\":\"Eti\",\"foodname\":\"kek\"}]'
        data = pd.read_json(from_server)
        return render_template('search_results.html', data=data)

@app.route("/name_search")
def searchbyname():
    return render_template('name_search.html')

@app.route("/signin", methods=['GET', 'POST'])
def signin():
    global client
    if request.method == 'POST':
        session.pop('username', None)
        if client is None:
            flash('Connection Error.', category='error')
            print("Cannot connect to server.")
            return render_template("index.html")
        # send username and password to server
        # if server returns true, redirect to profile page
        # else, show error message
        username = request.form['username']
        password = request.form['password'] 
        if username == "admin" and password == "admin":
            return render_template('admin.html')

        # create a json object to send to server
        data = {}
        data['username'] = username
        data['password'] = str(password)
        # send this as string to server
        message = "u"
        message += json.dumps(data)
        message = message.encode('utf-8')
        client.send(message)

        # TODO : add ERROR handling
        from_server = client.recv(4096)
        from_server = from_server.decode('utf-8')
        print("From server : ",from_server)

        

        

        if from_server == "ERROR":
            flash('Kullanıcı adı veya şifre hatalı.', category='error')
            return render_template("signin.html")

        user_data = pd.read_json(from_server)
        #  (self,userid , personname,personsurname,username,telephoneno=None,height=None,weight=None)
        user = User(user_data['userid'][0], user_data['personname'][0], user_data['personsurname'][0], user_data['e_mail'][0], user_data['telephoneno'][0], user_data['height'][0], user_data['weight'][0])
        
        session["user_id"] = str(user.userid)
        session["user_name"] = user.username

        return render_template('test.html', test=user)
        

    return render_template('signin.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route("/item/<int:barcodeno>")
def item(barcodeno):
    if not isDebug:
        global client
        if client is None:
            flash('Connection Error.', category='error')
            print("Cannot connect to server.")
            return render_template("index.html")
        barkod = barcodeno
        message = "b"
        message += str(barkod)
        message = message.encode('utf-8')
        client.send(message)
        
        # TODO : add ERROR handling
        from_server = client.recv(4096)
        from_server = from_server.decode('utf-8')
        print("From server : ",from_server)

        if from_server == "ERROR":
            flash('Barkod bulunamadı.', category='error')
            return render_template("index.html")

        # return render_template('test.html', test=from_server)
        data = pd.read_json(from_server)
        return render_template('result.html', barcodeno=data['barcodeno'][0], foodname=data['foodname'][0], brand=data['brand'][0], weightvolume=data['weightvolume'][0], ingredients=data['ingredients'][0], fat=data['fat'][0], protein=data['protein'][0], carbs=data['carbs'][0], calorie=data['calorie'][0], allergennames=data['allergennames'][0])
    else:
        from_server = "[{\"barcodeno\":1,\"foodname\":\"ekmek\",\"brand\":\"firinci\",\"weightvolume\":200,\"ingredients\":\"un\",\"fat\":20,\"protein\":10,\"carbs\":75,\"calorie\":300,\"allergennames\":\"['gluten', 'findik']\"}]"
        data = pd.read_json(from_server)
        return render_template('result.html', barcodeno=data['barcodeno'][0], foodname=data['foodname'][0], brand=data['brand'][0], weightvolume=data['weightvolume'][0], ingredients=data['ingredients'][0], fat=data['fat'][0], protein=data['protein'][0], carbs=data['carbs'][0], calorie=data['calorie'][0], allergennames=data['allergennames'][0])

if __name__ == "__main__":
    app.run(debug=True,port=8080)