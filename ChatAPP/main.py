# First, we need to install the next:
# pip install flask
# pip install flask-socketio

#Then, we must import the next modules:
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
from string import ascii_uppercase
import random

#Each Function Imported

#Flask: What allow us to create the app (object)

#render_template: Render means to couse something to become something else. This method allow us to integrate Python with HTML, CSS, and other web APIs
#All you have to do is provide the name of the template and the variables you want to pass to the template engine as keyword arguments" 

#request: We use it when we handle with GET & POST requests

#session: Allow us to remember each user when they log in or log out. It stores the data

#redirect: Is used for redirecting to other routes on the same application and external websites.

#join_room: https://flask-socketio.readthedocs.io/en/latest/
#This function puts the user in a room, under the current namespace. The user and the namespace are obtained from the event context. This is a function that can only be called from a SocketIO event handler. 

#leave_room: https://flask-socketio.readthedocs.io/en/latest/
#This function removes the user from a room, under the current namespace. The user and the namespace are obtained from the event context.

#send: https://flask-socketio.readthedocs.io/en/latest/
#This function sends a simple SocketIO message to one or more connected clients. The message can be a string or a JSON blob. This is a simpler version of emit(), which should be preferred. This is a function that can only be called from a SocketIO event handler.

#SocketIO: Create a Flask-SocketIO server

#ascci_uppercase: It will give the uppercase letters ‘ABCDEFGHIJKLMNOPQRSTUVWXYZ’.

#random: A method that generates ramdom numbers

#Initialize de server and the App
app = Flask(__name__)
app.config["SECRET_KEY"] = "SecretKey"
#app.config['SESSION_TYPE'] = 'SessionType'
socketio = SocketIO(app)

#Functions

rooms = {} #A dictionary of the codes as key and the values will be the messages and the people inside each code room
def GenerateUniqueCode(len):
    while True:
        code = ""
        for _ in range(len):
            code += random.choice(ascii_uppercase) #This generates the code
        if code not in rooms:
            #If the code does not exist, returns the generated code. If it exists, it is not going to break, it
            #will generates another code.
            break
    return code


#Creating the route in Flask 
@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()#This clears the session(delate everithing inside it), so it does not allow the user to
    #navegate. It forces the user to go to the home page, then to a chat room, and then leave the chat room
    #and join another one.

    #When I press any button (POST action), a GET action is recieved with the name and code values.
    #We put join and create with False, cuz POST and GET is a dictionary. In the name and code cases, the key
    #associated with each one is what I typed. But join and create are buttons, so they dont have a key associated.
    #We put False in order to avoid an error (the method will return False instead of that error).
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name: #if name is empty, will display an error (see the section below button tag in home doc)
            #We pass the values error, name and code, cuz the post action refreshes the window, so all the user has
            #typed is gonna be lost.Passing the values allow us to use it in the home render template in order to
            #not asking the name and code again.
            return render_template("home.html", error="You need to type a name.", code = code, name = name)

        if join != False and not code:
            return render_template("home.html", error="You need to type a code.", code = code, name = name)

        #Lets check if the room exists
        room = code
        if create != False:
            #Generating or creating the room
            room = GenerateUniqueCode(4)
            rooms[room] = {"members":0 , "messages":[]}
        elif code not in rooms:
            #When the user is not creating, but joining and the room doesn't exist
            return render_template("home.html", error="The room doesn't exist.", code = code, name = name)

        #Session stores data temporarily. It allows the user to mantain the session actived without any kind of
        #autentication.  
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")#We dont include the erros, code and name values cuz this return is gonna
    #happen when the action is not a POST

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home")) # We do this cuz we dont want to allow the user to enter directly to
                                         # the /room route. We want the user to register or create a room first. 
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")#This means the server will send a message, because of the socketio.emit("message") in room.html
def message(data):#data has the message
    room = session.get("room")
    
    if room not in rooms:
        return
    
    #If room is in rooms, then continue
    #Here we are creating the content (dict)
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    #print(rooms[room]["messages"])
    #print(data)

    send(content, to=room) #Here te message is sent to all room
    rooms[room]["messages"].append(content)#Here is stored the message in de dict messages
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")#this means that the server has been connected, and we will put the user into a specific room
#socketio cuz that is how we called the app in line 43
def connect(auth):
    room = session.get("room")#We need this in order to determine what the actual room to put the user in is
    name = session.get("name")#The same here, the name to put in the room
    if not room or not name: #In the case that somebody tries to get into a room before going to home page, that user could not
        return
    if room not in rooms:#Room does not exist
        leave_room(room)
        return

    join_room(room)
    send({"name": name, "message": "has entered to the room"}, to=room)
    #This is a json message. to:room means that the message will be sent to all people inside that specific room

    rooms[room]["members"] += 1 #this allow us to track how many user are in the chat room
    print(f"{name} has joined to the room {room}")
    #print(room)
    #print(rooms)
    #print(type(rooms))
    #print(type(rooms[room]))

@socketio.on("disconnect")#this means the server has been disconnected.
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)
    #print(rooms)
    if room in rooms:
        rooms[room]["members"] -= 1 #This decrease the amount of rooms in dict rooms
        #print(rooms)
        if rooms[room]["members"] <= 0: #Enter to the if in order to deleate the room , if there is just one person in the room
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")
    #print(rooms)

if __name__ == "__main__":
    socketio.run(app, debug=True) #Run method: Run the SocketIO web server.



