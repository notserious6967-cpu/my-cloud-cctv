from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO, emit, join_room
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cctv-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

def generate_room():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/create", methods=["POST"])
def create_room():
    room_id = generate_room()
    rooms[room_id] = {"cameras": [], "receivers": []}
    return redirect(f"/room/{room_id}")

@app.route("/join", methods=["POST"])
def join_existing():
    room_id = request.form.get("room_id", "").upper()
    if room_id not in rooms:
        return "Room not found. Go back and try again."
    return redirect(f"/room/{room_id}")

@app.route("/room/<room_id>")
def room(room_id):
    if room_id not in rooms:
        return "Room not found"
    return render_template("room.html", room_id=room_id)

@app.route("/camera/<room_id>")
def camera(room_id):
    return render_template("camera.html", room_id=room_id)

@app.route("/receiver/<room_id>")
def receiver(room_id):
    return render_template("receiver.html", room_id=room_id)

@socketio.on("camera_join")
def camera_join(data):
    room_id = data["room"]
    camera_name = data["name"]
    join_room(room_id)
    if room_id in rooms:
        rooms[room_id]["cameras"].append({"id": request.sid, "name": camera_name})
        emit("new_camera_online", {"id": request.sid, "name": camera_name}, room=room_id, include_self=False)

@socketio.on("receiver_join")
def receiver_join(data):
    room_id = data["room"]
    join_room(room_id)
    if room_id in rooms:
        for camera in rooms[room_id]["cameras"]:
            emit("new_camera_online", {"id": camera["id"], "name": camera["name"]}, room=request.sid)

@socketio.on("signal")
def handle_signal(data):
    destination = data["to"]
    emit("signal", data, room=destination)

@socketio.on("disconnect")
def handle_disconnect():
    for room_id, room_data in rooms.items():
        for camera in room_data["cameras"]:
            if camera["id"] == request.sid:
                room_data["cameras"].remove(camera)
                emit("camera_disconnected", request.sid, room=room_id)
                break

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

