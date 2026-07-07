from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from langchain_groq import ChatGroq
from twilio.rest import Client
import os
from dotenv import load_dotenv
from virtual_tellecaller import generate_output
from flask_cors import CORS
from fetch_call_details import fetch_call_logs

from flask import jsonify
import requests
from helper_functions.pinecone_helper import upload_business_data_to_pinecone
from helper_functions.mongodata import save_call_conversation

# from helper_functions.chat_render import send_text_to_frontend
from flask_socketio import SocketIO, emit

# Initialize the Flask app
load_dotenv()
app = Flask(__name__)
# CORS(app ,origins= "*")  # Allow all origins for CORS
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")
userdata = {}

global call_text  # Global variable to store the call conversation text
global curr_sid  # Global variable to store the current call SID
call_text = ""  # Initialize call_text to an empty string
curr_sid = None  # Initialize curr_sid to None


# def get_ngrok_url():
#     try:
#         tunnels = requests.get("http://localhost:4040/api/tunnels").json()["tunnels"]
#         print(tunnels[0]["public_url"])
#         return tunnels[0]["public_url"]  # Corrected line
#     except Exception as e:
#         print(f"Error fetching ngrok URL: {e}")
#         return None


# ngrok_url = get_ngrok_url()

hosted_url_call = "https://virtual-telecaller.onrender.com/voice"
hosted_url_call_status = "https://virtual-telecaller.onrender.com/voice/call_status"


def send_text_to_frontend(label, text):
    socketio.emit("chat_message", {"label": label, "text": text})


# ai_response = generate_output("", "")


TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TO_PHONE_NUMBER = os.getenv("TO_PHONE_NUMBER")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"), model_name="llama-3.3-70b-versatile"
)

exit_words = [
    "bye",
    "goodbye",
    "see you later",
    "thank you",
    "byebye",
    "thank you for your time",
    "thanks",
    "thank you for having a conversation with me",
    "thank you for your help",
    "thank you for your assistance",
    "thank you for your support",
    "thank you for your time and assistance",
    "thank you for your time and support",
]

messages = [
    {
        "role": "system",
        "content": """
        You are a helpful AI assistant named NirmaBot who loves to help you with your queries.You can ask me anything and I will try my best to help you.""",
    }
]


# Define the list of phone numbers to call


call_queue = []


@app.route("/", methods=["GET"])
def home():
    """Handles home page UI"""
    return "Welcome to the Nirma bot your AI-powered Tellecaller"


@app.route("/information", methods=["POST"])
def information():
    # give correct host url to frontend

    try:
        data = request.get_json(force=True)  # Get JSON data from the request
        # print(data)
        print("DEBUG Received data:", data)


        business_name = data.get("businessName")
        business_data = data.get("businessInfo")
        system_prompt = data.get("systemPrompt")
        source_Number = data.get("sourceNumber")
        destination_Number = data.get("destinationNumber")
        # first create empty file and then write to it

        with open("data/rag_data.txt", "w", encoding="utf-8", errors="ignore") as f:
            f.write(business_data)
            f.flush()
            os.fsync(f.fileno())
            f.close()

        with open(
            "data/system_prompt.txt", "w", encoding="utf-8", errors="ignore"
        ) as f:
            f.write(system_prompt)
            f.flush()
            os.fsync(f.fileno())
            f.close()

        # Upload the business data to Pinecone
        upload_business_data_to_pinecone(business_name)
        # Wait for the data to be uploaded

        if destination_Number:

            destination_Number = (
                destination_Number.strip()
            )  # Remove leading and trailing spaces
            destination_Number = destination_Number.split(" ")
            call_queue.extend(destination_Number)
            print(call_queue)

        userdata["businessName"] = business_name
        userdata["businessInfo"] = business_data
        userdata["systemPrompt"] = system_prompt
        userdata["sourceNumber"] = source_Number

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/voice", methods=["POST"])
def voice():
    global call_text

    response = VoiceResponse()
    response.pause(length=2)

    with open("data/rag_data.txt", "r", encoding="utf-8", errors="ignore") as f:
        business_data = f.read()

    intro = llm.invoke(
        f"""
                       
    You are an AI advertiser who generate a catchy introduction for a business based on the   and business data is {business_data}.The introduction should be in detail and catchy should describe the business and its all services which it provides.At last just ask the user for specific query related to the business. Answer in a friendly tone and make it sound like a real person. Length of the introduction should be 6-7 lines.




    """
    )

    intro = intro.content

    print("intro ", intro)

    # send_text_to_frontend("intro",intro)

    call_text += f"AI Bot:{intro}\n\n"
    send_text_to_frontend("AI Bot", intro)

    """Handles incoming voice calls from Twilio."""

    response.say(
        intro,
        language="en-US",
        voice="Polly.Matthew",
    )
    gather = Gather(
        input="speech",
        action="/process_voice",
        method="POST",
        language="en-US",
        speechTimeout="auto",
        speechModel="deepgram_nova-2",
        actionOnEmptyResult=True,
        timeout=5,
    )
    response.pause(length=2)
    response.append(gather)
    # response.say("Please wait while I process your query.", language="en-US", voice="Polly.Matthew")
    response.pause(length=8)

    return Response(str(response), content_type="text/xml")


@app.route("/process_voice", methods=["POST"])
def process_voice():
    global call_text
    business_name = userdata.get("businessName")
    response = VoiceResponse()
    response.pause(length=2)
    speech_text = request.form.get("SpeechResult", "").strip()

    if not speech_text:
        response.say(
            "I'm sorry, I didn't catch that. Please try again.",
            language="en-US",
            voice="Polly.Matthew",
        )
        gather = Gather(
            input="speech",
            action="/process_voice",
            method="POST",
            language="en-US",
            speechTimeout="auto",
            actionOnEmptyResult=True,
            speechModel="deepgram_nova-2",
            timeout=5,
        )
        response.pause(length=2)
        response.append(gather)
        response.pause(length=6)
        return Response(str(response), content_type="text/xml")

    print(f"User said: {speech_text}")
    send_text_to_frontend("user", speech_text)
    call_text += f"User:{speech_text}\n\n"

    if any(word in speech_text.lower() for word in exit_words):
        send_text_to_frontend("AI Bot", "Thank you for having a conversation with me.")
        call_text += "AI Bot: Thank you for having a conversation with me.\n\n"
        response.say(
            "Thank you for having a conversation with me.",
            language="en-US",
            voice="Polly.Matthew",
        )
        response.hangup()
        return Response(str(response), content_type="text/xml")

    # Inform the user that their query is being processed.
    response.say(
        "Please wait while I process your query.",
        language="en-US",
        voice="Polly.Matthew",
    )

    # Increase pause to allow maximum time for LLM response.
    response.pause(
        length=3
    )  # Main processing time for LLM response.////////////////////////////////////////

    # Now call your LLM (this is still blocking, so ensure the pause covers your processing time).
    ai_response = generate_output(business_name, speech_text)

    if not ai_response or ai_response["response"] == "":
        response.say(
            "Thank you for having a conversation with me.",
            language="en-US",
            voice="Polly.Matthew",
        )
        response.hangup()
        return Response(str(response), content_type="text/xml")

    res = ai_response["response"]
    print(f"AI Response: {res}")
    send_text_to_frontend("AI Bot", res)
    call_text += f"AI Bot:{res}\n\n"
    response.pause(length=5)

    response.say(res, language="en-US", voice="Polly.Matthew")
    gather = Gather(
        input="speech",
        action="/process_voice",
        method="POST",
        language="en-US",
        speechTimeout="auto",
        actionOnEmptyResult=True,
        speechModel="deepgram_nova-2",
        timeout=5,
    )
    response.pause(length=2)
    response.append(gather)
    response.pause(length=5)

    return Response(str(response), content_type="text/xml")


@app.route("/make_call", methods=["POST", "GET"])
def make_call():

    # host = f"{ngrok_url}/voice"
    

    """Initiate a call to the user's phone number."""

    source_number = userdata.get("sourceNumber")

    print(f"Host URL: {hosted_url_call}")
    print(f"Source Number: {source_number}")

    try:
        call = client.calls.create(
            # url=f"{ngrok_url}/voice",
            url=hosted_url_call,
            from_=source_number,
            to=call_queue[0],
            # status_callback=f"{ngrok_url}/call_status",
            status_callback=hosted_url_call_status,
            status_callback_event=["completed"],
            status_callback_method="POST",
        )

        print(f"Call initiated: {call.sid}")
        global curr_sid
        curr_sid = call.sid  # Store the current call SID globally

        return "Call initiated successfully."

    except Exception as e:
        print(e)
        return "Failed to initiate the call."


@app.route("/call_status", methods=["POST"])
def call_status():

    global call_text
    global curr_sid
    if call_queue:
        call_queue.pop(
            0
        )  # Remove the first number from the queue as the call is complete
    save_call_conversation(curr_sid, call_text)

    call_text = ""  # Reset call_text for the next call

    print("Call Complete checking next call in queue")
    send_text_to_frontend("SYSTEM", "Call completed. Checking next call in queue.")

    if call_queue:

        next_number = call_queue.pop(0)

        # custom function which save call conversation mapped to the current call SID

        client.calls.create(
            # url=f"{ngrok_url}/voice",
            url=hosted_url_call,
            to=next_number,
            from_=TWILIO_PHONE_NUMBER,
            # status_callback=f"{ngrok_url}/call_status",
            status_callback=hosted_url_call_status,
            status_callback_event=["completed"],
            status_callback_method="POST",
        )
        print(f"Next call initiated to: {next_number}")
    else:
        print("No more numbers in the queue.")

        send_text_to_frontend(
            "SYSTEM", "All calls completed. Thank you for using Virtual Telecaller."
        )
        # clear the socketio session
        curr_sid = None
        call_text = ""

        call_queue.clear()

    return ("All calls completed", 200)


@app.route("/call_details", methods=["GET"])
def call_logs():
    """Fetch call details"""

    try:
        call_details = fetch_call_logs()
        return jsonify(call_details), 200
    except Exception as e:
        print(f"Error fetching call details:{e}")
        return jsonify({"error": "Failed to fetch call details"}), 500


if __name__ == "__main__":

    # Start the Flask app with SocketIO
    host = "0.0.0.0"
    port = int(os.getenv("PORT", 5000))  # Use PORT from environment or default to 5000
    socketio.run(app, host=host, port=port, use_reloader=False, allow_unsafe_werkzeug=True)

    # app.run(port=5000, debug=False, use_reloader=False)
