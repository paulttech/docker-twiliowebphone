from flask import Flask, render_template, jsonify
from flask import request, Response, redirect, url_for

from flask_cors import CORS

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from twilio.twiml.voice_response import VoiceResponse, Dial
from twilio.rest import Client

from dotenv import load_dotenv
import os
import pprint as p

from flask_socketio import SocketIO, emit

load_dotenv()

account_sid = ""
api_key = ""
api_key_secret = ""
twiml_app_sid = ""
twilio_number = "+"
account_auth_token = ""

app = Flask(__name__)
socketio = SocketIO(app)

# CORS config
CORS(app, resources={r"/*": {"origins": "*"}})
socketio.init_app(app, cors_allowed_origins="*")

# Configure your SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///urlcollection.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Create the SQLAlchemy database object
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Define your database model (TestModel in this case)
class UrlModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recording_url = db.Column(db.String(255))
    recording_duration = db.Column(db.String(20))
    to_number = db.Column(db.String(20))


# Define a function to create the tables
def create_tables():
    with app.app_context():
        db.create_all()


# Create a database if it doesn't exist
create_tables()


# Render the home page when we take up the application
@app.route('/')
def home():
    return render_template(
        'home.html',
        # 'dial_modal.html',
        title="In browser calls",
    )


# Get the access token to actually use the phone feature
@app.route('/token', methods=['GET'])
def get_token():
    identity = twilio_number
    outgoing_application_sid = twiml_app_sid

    access_token = AccessToken(account_sid, api_key,
                               api_key_secret, identity=identity)

    voice_grant = VoiceGrant(
        outgoing_application_sid=outgoing_application_sid,
        incoming_allow=True,
    )
    access_token.add_grant(voice_grant)

    response = jsonify(
        {'token': access_token.to_jwt(), 'identity': identity})

    return response

to_number = None


# Websocket communication to talk to Django app

@socketio.on('connect')
def handle_connect():
    print('Client connected to Flask!')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected from Flask!')

@socketio.on('send_flag_to_django')
def send_flag(data):
    flask_flag = data['flask_flag']
    print(f"Sending flag to Django: {flask_flag}")
    emit('receive_flag_from_flask', {'flask_flag': flask_flag}, broadcast=True)


@app.route('/handle_calls', methods=['POST'])
def call():
    global to_number
    p.pprint(request.form)
    response = VoiceResponse()
    dial = Dial(
        callerId=twilio_number,
        # callerId="+916282543120",
        record='record-from-answer',
        recording_status_callback='/recording_callback'
    )


    if 'To' in request.form and request.form['To'] != twilio_number:
        print('outbound call')
        to_number = (request.form['To'])
        print("Inside the function", to_number)
        dial.number(request.form['To'])
        # Emit a socket event to notify Django frontend
        socketio.emit('call_made', {'message': 'Call made!'})
        print("Success")
        
    else:
        print('incoming call')
        caller = request.form['Caller']
        dial = Dial(callerId=caller)
        dial.client(twilio_number)

    return str(response.append(dial))


recording_url = None

@app.route('/recording_callback', methods=['GET', 'POST'])
def record():
    # Get the parameters from Twilio recording
    account_sid = request.form['AccountSid']
    call_sid = request.form['CallSid']
    recording_sid = request.form['RecordingSid']
    recording_url = request.form['RecordingUrl']
    recording_status = request.form['RecordingStatus']
    recording_duration = request.form['RecordingDuration']
    recording_channels = request.form['RecordingChannels']
    recording_start_time = request.form['RecordingStartTime']
    recording_source = request.form['RecordingSource']


    response_text = f"Account SID: {account_sid}\nCall SID: {call_sid}\nRecording SID: {recording_sid}\nRecording URL: {recording_url}\nRecording Status: {recording_status}\nRecording Duration: {recording_duration}\nRecording Channels: {recording_channels}\nRecording Start Time: {recording_start_time}\nRecording Source: {recording_source}"

    print("Inside record function", to_number)
    print(response_text)

    # recording_id = int(UrlModel(id=id))
    # url_list = UrlModel(recording_url=recording_url)
    # recording_duration = UrlModel(recording_duration=recording_duration)

    new_record = UrlModel(recording_url=recording_url, recording_duration=recording_duration, to_number=to_number)

    db.session.add(new_record)
    db.session.commit()

    return redirect('/urldata')


@app.route('/endpoint', methods = ['GET', 'POST'])
def retrieve_url_data():
    try:
        phone_number = request.form.get('phoneNumber')
        client = Client(account_sid, account_auth_token)
        
        # Process the phone number as needed
        print(f"Received phone number from DJANGO!!!. Hello: {phone_number}")

        response = VoiceResponse()
        dial = Dial(callerId=twilio_number)

        if phone_number and phone_number != twilio_number:
            print('outbound call')
            dial.number(phone_number)
            print("Number was dialed")
        else:
            print('incoming call')

        # call = client.calls.create(
        #         # twiml=f'<Response><Say>{custom_message}</Say></Response>',
        #         twiml=f'<Response><Dial>+917548826361</Dial></Response>',
        #         to=phone_number,
        #         from_=twilio_number
        #     )
        
        # callSid = call.sid

        # Return a response if needed
        return str(response.append(dial))
    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == "__main__":
    socketio.run(host='0.0.0.0', port=3000, debug=True)
