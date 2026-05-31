import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'atulya_secret_9988'
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/receiver/<room_code>')
def receiver(room_code):
    return render_template('receiver.html', room_code=room_code)

@app.route('/camera/<room_code>')
def camera(room_code):
    return render_template('camera.html', room_code=room_code)

@app.route('/create-room', methods=['POST'])
def create_room():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    rooms[code] = {'cameras': {}}
    return jsonify({'room_code': code})

@socketio.on('join_room')
def on_join(data):
    room = data.get('room')
    role = data.get('role')
    join_room(room)
    
    if role == 'camera':
        cam_name = data.get('cam_name', 'Node')
        is_heist = cam_name.strip().lower() == 'heist'
        emit('camera_connected', {'id': request.sid, 'name': cam_name, 'is_heist': is_heist}, to=room)

@socketio.on('ping_test')
def on_ping_test(cb):
    if cb: cb()

@socketio.on('signal')
def on_signal(data):
    target = data.get('target')
    if target:
        emit('signal', {'sender': request.sid, 'signal': data['signal']}, to=target)

@socketio.on('heist_alarm')
def on_heist_alarm(data):
    room = data.get('room')
    emit('trigger_alarm', {'cam_id': request.sid}, to=room, include_self=False)


    if __name__ == '__main__':
        from gevent import monkey
        monkey.patch_all()
        port = int(os.environ.get('PORT', 5000))
        socketio.run(app, host='0.0.0.0', port=port, debug=False)

