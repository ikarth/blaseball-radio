import pyttsx3
import json
import glob
import datetime
import time
import os
import pdb
import pprint
import requests
import random
import tracery
import decimal
from pathlib import Path
from modernblaseball.modern_blaseball import blaseball_api

import gtts
from playsound import playsound


speech_engine = pyttsx3.init()

voices = speech_engine.getProperty("voices")
print(voices)
speech_engine.setProperty("voice", voices[1].id)

#    tts = gtts.gTTS(msg)
#    tts.save("blaseball_message.mp3")
#    playsound("blaseball_message.mp3")



blaseball = blaseball_api()

def announceText(message):
    print(message)
    speech_speed = random.choice(list(range(150, 250)))
    speech_volume = (random.random() * 0.3) + 0.7
    speech_engine.setProperty("rate", speech_speed)
    speech_engine.setProperty('volume', speech_volume)

    blaseball_name = random.choice(["blaseball", "blaze ball", "blace ball", "blace ball","blace ball","blace ball","blace ball","blace ball","blace ball","blace ball","blace ball", "blace ball"])
    message = message.replace(" US ", " us ")
    message = message.replace("BLASEBALL", blaseball_name)
    message = message.replace("blaseball", blaseball_name)

    speech_engine.say(message)


def mungeFuncName(name):
    name = name.replace(" ", "_")
    name = name.replace("(", "")
    name = name.replace(")", "")
    name = name.replace(",", "")
    return name


def storeData(data, id):
    if data == []:
        return data
    id = mungeFuncName(id)
    Path("data").mkdir(parents=True, exist_ok=True)
    now_timestamp = str(datetime.datetime.now().timestamp())
    with open(f'data/data_{id}_{now_timestamp}.json', 'w') as f:
        json.dump(data, f)
    return data

def retrieveData(id, args=None):
    if args != None:
        id = id + "_" + str(args)
    id = mungeFuncName(id)
    files_found = glob.glob(f"data/data_{id}_*")
    most_recent_file = max(files_found, key=os.path.getctime)
    data = None
    with open(most_recent_file) as f:
        data = json.load(f)
    return data

def getGlobalTicker():
    result_request_global_events = blaseball.get_global_events()
    if result_request_global_events.status_code == 200:
        global_ticker_raw = [x.decode("UTF-8") for x in result_request_global_events]
        global_ticker_string = "".join(global_ticker_raw)
        global_ticker_data = json.loads(global_ticker_string)
        print(global_ticker_data)
        return global_ticker_data
    print(result_request_global_events)
    return None

def speakGlobalTicker(global_ticker_data):
    if global_ticker_data == None:
        return
    for ticker_entry in global_ticker_data:
        msg = ticker_entry["msg"]
        announceText(msg)
        break

#gticker = storeData(getGlobalTicker(), "global_ticker")
#ngticker = retrieveData("global_ticker")
#speakGlobalTicker(ngticker)

# get_global_events()
# get_all_divisions()
# get_league(league_id)
# get_sub_league(sub_league_ids)
# get_game(game_id)
# get_offseason_setup()
# get_offseason_recap(season_num)
# get_offseason_bonus_results(bonus_id)
# get_offseason_decree_results(decree_ids)
# get_playoff_details(playoff_num)
# get_team(team_id)
# get_all_teams()
# get_player_stats(player_list)
# get_season(season_num)
# get_simulation_data()





def getMainData():
    funcs = [blaseball.get_all_divisions,
            blaseball.get_offseason_setup,
            blaseball.get_all_teams,
            blaseball.get_simulation_data]
    for func in funcs:
        func_name = str(func.__name__)[4:]
        print(func_name)
        request_result = func()
        print(request_result.status_code)
        if request_result.status_code == 200:
            print(request_result)
            print(request_result.text)
            data = json.loads(request_result.text)
            storeData(data, func_name)

def getSpecificData(func, args=None):
    func_name = str(func.__name__)[4:]
    request_result = None
    if args != None:
        func_name = func_name + "_" + str(args)
    func_name = mungeFuncName(func_name)
    request_result = blaseball.failover_500(func, args)
    #request_result = func(args)

    #print(request_result.status_code)
    data = None
    if request_result.status_code == 200:
        #print(request_result)
        if request_result.text == "":
            print("\t* * * EMPTY RESULT * * *")
            return data
        #print(request_result.text)
        data = json.loads(request_result.text)
        storeData(data, func_name)
    return data

test_data = retrieveData("all_divisions")
print(test_data)

# blaseball.get_league(league_id)
# blaseball.get_sub_league(sub_league_ids)
# blaseball.get_game(game_id)

# blaseball.get_offseason_recap(season_num)
# blaseball.get_offseason_bonus_results(bonus_id)
# blaseball.get_offseason_decree_results(decree_ids)

# blaseball.get_playoff_details(playoff_num)
# blaseball.get_team(team_id)
# blaseball.get_player_stats(player_list)
# blaseball.get_season(season_num)

def get_GamesOnDay(which_game):
    game_day, game_season = which_game
    URL_BASE = 'https://blaseball.com'
    #print("get_GamesOnDay", game_day, game_season)
    res = requests.get(URL_BASE + '/database/games', params={'day': game_day, 'season': game_season})
    if res.text[:9] == "<!doctype":
        print ("NOT FOUND")
    return res

def getSecondaryData():
    all_divisions = retrieveData("all_divisions")
    offseason_setup = retrieveData("offseason_setup")
    offseason_recap = retrieveData("offseason_recap")
    all_teams = retrieveData("all_teams")
    simulation_data = retrieveData("simulation_data")

    if False:
        for n in range(2):
            getSpecificData(blaseball.get_season, n)
            getSpecificData(blaseball.get_offseason_recap, n)
            getSpecificData(blaseball.get_playoff_details, n)

    if False:
        print(all_teams)
        for t in all_teams:
            pprint.pprint(t)
            #team_data = getSpecificData(blaseball.get_team, t["_id"])
            pprint.pprint(t["fullName"])
            player_groups = ["bench", "bullpen", "rotation", "lineup"]
            for g in player_groups:
                print(g)
                print(t[g])
                for p in t[g]:
                    getSpecificData(blaseball.get_player_stats, p)
                    time.sleep(0.4)

    if False:
        game_season = 1
        game_day = 9
        for game_day in range(85, 111):
            print(game_day)
            getSpecificData(get_GamesOnDay, (game_day, game_season))


getSecondaryData()

stat_translation = {
'anticapitalism': 'anticapitalism',
  'baseThirst': 'base Thirst',
  'buoyancy': 'buoyancy',
  'chasiness': 'chasiness',
  'coldness': 'coldness',
  'continuation': 'continuation',
  'deceased': False,
  'divinity': 'divinity',
  'groundFriction': 0.007046953371369291,
  'indulgence': 0.27470613374348973,
  'laserlikeness': 0.7408366881185251,
  'martyrdom': 0.26784996287468266,
  'moxie': 0.2600073866861561,
  'musclitude': 0.29257367474564067,
  'name': 'Ronan Jaylee',
  'omniscience': 0.9314783293677276,
  'overpowerment': 0.09283593051574157,
  'patheticism': 0.3849112979945193,
  'pressurization': 0.8019224362991275,
  'ruthlessness': 0.4120166833220451,
  'shakespearianism': 0.9684260531553017,
  'soul': 3,
  'suppression': 0.16804658197756606,
  'tenaciousness': 0.5616753142185644,
  'thwackability': 0.3988667251495792,
  'totalFingers': 10,
  'tragicness': 0,
  'unthwackability': 0.1323305354742057,
  'watchfulness': 0.23464612554628728}

print("-----------------------------------------------------------------")



rd = retrieveData("GamesOnDay", (103, 1))
print(rd)
def makeCommentary(game_state):
    #pprint.pprint(game_state)

    commentary = []
    try:
        commentary.append("Check out twitch.tv/blaseball_radio for commentary by humans. ")
        commentary.append("Check out twitch.tv/blaseball_radio for human-driven commentary. ")
        commentary.append(f"The count is {game_state['atBatBalls']} and {game_state['atBatStrikes']}. ")
        commentary.append(f"There are {game_state['baserunnerCount']} runners on base. ")
        commentary.append(f"The count is {game_state['atBatBalls']} and {game_state['atBatStrikes']} with {game_state['halfInningOuts']} outs. ")
        commentary.append(f"You are listening to {game_state['awayTeamNickname']} at {game_state['homeTeamNickname']}. ")
        commentary.append(f"You are listening to {game_state['awayTeamNickname']} at {game_state['homeTeamNickname']}. ")
        commentary.append(f"You are listening to {game_state['awayTeamNickname']} at {game_state['homeTeamNickname']}. ")
        commentary.append(f"It is a beautiful solar eclipse here at the {game_state['awayTeamNickname']} vs. the {game_state['homeTeamNickname']}. ")
        commentary.append(f"You are listening to {game_state['awayTeamName']} vs. {game_state['homeTeamName']}. ")
        if game_state['topOfInning']:
            commentary.append(f"It is the top of the {game_state['inning'] + 1}th. ")
            commentary.append(f"{game_state['homePitcherName']} is pitching for the {game_state['homeTeamNickname']}. ")
            commentary.append(f"{game_state['awayBatterName']} is batting for the {game_state['awayTeamNickname']}. ")
            commentary.append(f"{game_state['homePitcherName']} is on the mound. ")
        else:
            commentary.append(f"It is the bottom of the {game_state['inning'] + 1}th. ")
            commentary.append(f"{game_state['awayPitcherName']} is pitching for the {game_state['awayTeamNickname']}. ")
            commentary.append(f"{game_state['homeBatterName']} is batting for the {game_state['homeTeamNickname']}. ")
            commentary.append(f"{game_state['awayPitcherName']} is on the mound. ")
        commentary.append("The floating shard is a blaseball fan.")
        commentary.append("Crying in Blaseball is ERROR SIGNAL LOST")
        if random.random() < 0.3:
            players = [game_state['homePitcher'], game_state['homeBatter'], game_state['awayPitcher'], game_state['awayBatter']]
            for p in players:
                if p != '':
                    p_data = retrieveData("player_stats", args=str(p))
                    #pprint.pprint(p_data)
                    for p_stat, p_val in p_data[0].items():
                        d_str = ""
                        if p_stat == "_id":
                            p_val = "_id"
                        if isinstance(p_val, str):
                            d_str = f"The {p_stat} of {p_data[0]['name']} is {p_val}. "
                        if isinstance(p_val, int):
                            d_str = f"{p_data[0]['name']} has {p_val} {p_stat}. "
                        if isinstance(p_val, float):
                            d_str = f"{p_data[0]['name']} has a {p_stat} of {round(decimal.Decimal(p_val), 2)}. "
                        commentary.append(d_str)
    except:
        commentary.append("The Shard is watching.")

    ticker_text = [x["msg"] for x in retrieveData("global_ticker")]
    commentary = commentary + ticker_text
    return commentary

running_commentary = makeCommentary(rd[0])
pprint.pprint(running_commentary)

current_game_day = 104

def getPlayoffTranscripts():
    global current_game_day
    game_season = 1

    game_day = current_game_day
    data = getSpecificData(get_GamesOnDay, (game_day, game_season))
    announce_text = data[0]["lastUpdate"]
    #pprint.pprint(data[0])
    commentary = makeCommentary(data[0])
    finished = False
    if (data[0]["gameComplete"] == True):
        finished = True
    if (data[0]["gameStart"] == False):
        time.sleep(5)
    return announce_text, commentary, finished

last_announce_text = ""
last_commentary = []
def getABunchOfTranscripts():
    global last_commentary
    global last_announce_text
    finished = False
    try:
        announce_text, commentary, finished = getPlayoffTranscripts()
        last_commentary = commentary
    except:
        commentary = last_commentary
        announce_text = last_announce_text
    if last_announce_text != announce_text:
        announceText(announce_text)
        speech_engine.runAndWait()
        last_announce_text = announce_text
    else:
        if not finished:
            if random.random() > 0.5:
                announceText( random.choice(commentary) )
                speech_engine.runAndWait()
    return finished

game_over = False
while current_game_day < 120:
    while not game_over:
        game_over = getABunchOfTranscripts()
        time.sleep(0.1)
        if game_over:
            getABunchOfTranscripts()
    current_game_day += 1
    time.sleep(5)