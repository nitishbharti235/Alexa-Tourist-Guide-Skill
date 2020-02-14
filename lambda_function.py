from __future__ import print_function
from botocore.vendored import requests
import googlemaps
import json
import requests
from os import environ
from datetime import datetime

# messages
# {
#  welcome= "Welcome to Kitkat Guide! Are you feeling hungry or ready to go? If you need help please say help."
#  suggestion= "You can say NLHC IITISM, Penmen Auditorium, "
#  recommend= "Say I want to go Library or get me to the Hostel"
 
# }


visa = {
      "America" : "Visas must be granted by the Indian Embassy or consulate prior to travel, and cannot be secured upon arrival. The Indian Embassy currently outsources its 								 visa services to Cox and Kings Global Services. A tourist visa allows a U.S. citizen to stay in India for six months.Those traveling solely for tourism 								 purposes and planning on staying no more than 30 days may apply for an electronic travel authorizaton (ETA) in lieu of a tourist visa at least 4 days 								 prior to arrival in India",
      "Australia": "Australian citizens have an automatic right of entry to Australia, and do not require a visa. Australian citizens need only to present the following 		            documents to officers in immigration clearance a valid Australian passport or other acceptable travel document a completed and signed Incoming Passenger 								card. Australians who hold dual or multiple nationalities should hold an Australian passport and use it to enter or leave Australia, even when using a 								foreign passport overseas."
    }

#myloc = '32.2190, 76.3234'
myloc = '19.0760, 72.8777'

# --------------- Main handler ------------------

def lambda_handler(event, context):
    if event['request']['type'] == "LaunchRequest":
        return get_welcome()
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event)

def on_intent(event):
    intent = event['request']['intent']
    intent_name = event['request']['intent']['name']
    print("on_intent, session: ")
    print(event['session'])
    # Dispatch to your skill's intent handlers
    if intent_name == "GetDirectionsTo":
        return get_directions(event)
    elif intent_name == "VisaIntent":
        return visa_info(event)
    elif intent_name == "YesIntent":
        return yes_intent()
    elif intent_name == "NoIntent":
        return no_intent()
    elif intent_name == "ReviewIntent":
        return get_review(event)
    elif intent_name == "AfterReadyIntent":
        return recommend(event)
    elif intent_name == "IamhungryIntent":
        return food_guide(event)
    elif intent_name == "AfterHelpIntent":
        return get_afterhelp(event)
    elif intent_name == "AMAZON.HelpIntent":
        return get_help()
    elif intent_name == "AMAZON.CancelIntent":
        return do_nothing()
    elif intent_name == "AMAZON.StopIntent":
        return do_nothing()
    else:
        raise ValueError("Invalid intent")


# def display_image(steps):
#     mx=10
#     if(len(steps) <mx)mx=len(steps)
#     url= "https://maps.googleapis.com/maps/api/staticmap?zoom=19&"
#     path="path=color:0x0000ff|weight:5"
#     i=0
#     while(i<mx):
#         lat=steps[i]['start_location']['lat']
#         lng=steps[i]['start_location']['lng']
#         path=path+"|"+str(lat)+","+str(lng)
#         i=i+1
#     i=i-1
#     lat=steps[i]['end_location']['lat']
#     lng=steps[i]['end_location']['lng']
#     path=path+"|"+str(lat)+","+str(lng)
    
#     path=path+"&size=1000x1000&key=API_KEY"

def get_review(event):
    place = event['request']['intent']['slots']['place']['value']
    place.replace(" ", "+")
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input="+place+"&inputtype=textquery&key=API_KEY"
    res = requests.get(url)
    place_id = res.json()['candidates'][0]['place_id']
    # place_id="ChIJbf8C1yFxdDkR3n12P4DkKt0"
    url="https://maps.googleapis.com/maps/api/place/details/json?place_id="+place_id+"&fields=reviews&key=API_KEY"
    response= requests.get(url)
    response_json = response.json()
    reviews = response_json['result']['reviews']
    return say_duration( reviews[0]['text'] )
    
def visa_info(event):
    country= event['request']['intent']['slots']['country']['value']
    return say_duration(visa[country])

def recommend(event):
    gmaps = googlemaps.Client(key=environ['API_KEY'])
    try:
        response = gmaps.places_nearby(keyword = str("tourist attraction"), location=myloc, radius=2000)
    except:
        response=[]
    say = "I found these tourist attractions "
    r=min(5, int(len(response['results'])))
    for i in range(r):
        name = response['results'][i]['name']
        address = response['results'][i]['vicinity']
        say=say+name+" at "+address
        if(i!=r-1):
            say=say+" and "
        else:
            say=say+"."
    
    return say_duration(say)    

def food_guide(event):
    gmaps = googlemaps.Client(key=environ['API_KEY'])
    try:
        food_result = gmaps.places_nearby(keyword = str("restaurant"), location=myloc, radius=2000)
    except:
        food_result=[]
    
    if(len(food_result) == 0):
        return say_duration("Sorry I am unable to find right now.")
    
    first_result = food_result['results'][0]
    name = first_result['name']
    rating = first_result['rating']
    
    s_result = food_result['results'][1]
    s_name=s_result['name']
    s_rating = s_result['rating']
    
    say = "I found these Results "+name+" with rating "+str(rating)+" and "+s_name+" raring "+str(s_rating)
    say=say+" Do you want reviews?"
    return say_duration(say)

def get_afterhelp(event):
    place = event['request']['intent']['slots']['type']['value']
    if not place:
        return say_duration("please speak again")
    gmaps = googlemaps.Client(key=environ['API_KEY'])
    try:
        place_result = gmaps.places_nearby(keyword = str(place), location=myloc, radius=3000)
    except:
        place_result=[]
    
    if(len(place_result) == 0):
        return say_duration("Sorry I am unable to find right now.")
    
    first_result = place_result['results'][0]
    name=first_result['name']
    address = first_result['vicinity']
    
    say = "You Nearest "+place+ " is "+name+" and its address is "+address
    
    return say_duration(say)

def get_directions(event):
    destination = event['request']['intent']['slots']['tocity']['value']
    # if 'tocity' in event['request']['intent']['slots']:
    #     destination = event['request']['intent']['slots']['tocity']['value']
    # if(len(destination) == 0):
    #      return say_duration("Where do you want to go? or should I recommend you?")
    
    start_address = get_my_address(event)
    if not start_address:
        return permissions_error()
    print('start: '+start_address+'; destination: '+destination)
    return get_duration(start_address, destination)
   

def get_my_address(event):
    return '23.6101808, 85.2799354'
    try:
        deviceId = event['context']['System']['device']['deviceId']
        print("deviceId is "+deviceId)
        apiAccessToken = event['context']['System']['apiAccessToken']
        print("apiAccessToken is "+apiAccessToken)
        apiEndpoint = event['context']['System']['apiEndpoint']
        print("apiEndpoint is "+apiEndpoint)
        headers = {'Authorization': 'Bearer '+apiAccessToken}
        url = apiEndpoint + '/v1/devices/'+deviceId+'/settings/address'
        r = requests.get(url, headers=headers)
        print(r.json())
        return r.json()['addressLine1'], r.json()['postalCode']
    except:
        try:
            return environ['HOME'], environ['HOME']
        except:
            return False, False

def get_work_address():
    return environ['WORK']

def get_duration(start_address, end ):
    gmaps = googlemaps.Client(key=environ['API_KEY'])
    try:
        start_address = myloc
        # end = '23.8144, 86.4412'
        directions_result = gmaps.directions(start_address, end, mode="driving", departure_time=datetime.now())
    except:
        directions_result = []
    if (len(directions_result) == 0):
        return say_duration("direction result size 0")
    
    leg = directions_result[0]['legs'][0]
    duration=leg['duration']['text']
    summary = directions_result[0]['summary']
    to_say="Right now, it takes "+duration+" to get to "+end+", via "+summary
    #return say_duration( json.dumps(directions_result) )
    # display_image(leg['steps'])
    return say_duration(to_say)

def ask_for_repeat(end):
    speech_output = "I'm sorry, I couldn't find "+end+", could you be more specific?"
    card_title = 'Google Maps Help'
    should_end_session = False
    return build_response(build_speechlet_response(card_title, speech_output, None, should_end_session))

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }
    
def build_short_speechlet_response(output, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'shouldEndSession': should_end_session
    }

def build_response(speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': {},
        'response': speechlet_response
    }

# --------------- Functions that control the skill's behavior ------------------

def say_duration(duration):
    speech_output = duration
    card_title = 'Google Maps'
    should_end_session = False
    return build_response(build_speechlet_response(card_title, speech_output, None, should_end_session))

def get_help():
    speech_output = "What can I help you with? You can say Nearest Police station or Hospital"
    card_title = 'Google Maps'
    should_end_session = False
    return build_response(build_speechlet_response(card_title, speech_output, None, should_end_session))

def get_welcome():
    speech_output="Welcome to Kitkat Guide! Are you feeling hungry or ready to go to somewhere? I can also recommend you a place. You can ask reviews for a place. and If you need help please say help. "
    card_title = 'Kitkat'
    should_end_session= False
    return build_response(build_speechlet_response(card_title, speech_output, None, should_end_session))

def permissions_error():
    speech_output = 'Sorry, I do not know your address. Please check the settings in the Alexa app.'
    card_title = 'Google Maps error'
    should_end_session = True
    return build_response(build_speechlet_response(card_title, speech_output, None, should_end_session))

def do_nothing():
    return build_response({})
