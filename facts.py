import json
import glob
import itertools
import datetime
import time
import dateutil.parser
import os
import requests
import logging
from pathlib import Path
from modernblaseball.modern_blaseball import blaseball_api

import pprint

KNOWN_NUMBER_OF_SEASONS = 2
GET_PLAYER_DATA = False
REPORT_DATA_RETREVIAL = True

blaseball = blaseball_api()

def mungeFuncName(name):
    name = name.replace(" ", "_")
    name = name.replace("(", "")
    name = name.replace(")", "")
    name = name.replace(",", "")
    return name

def storeData(data, id):
    now_timestamp = str(datetime.datetime.now().timestamp())
    if data == []:
        return data
    id = mungeFuncName(id)
    Path(f'data/{KNOWN_NUMBER_OF_SEASONS:05d}').mkdir(parents=True, exist_ok=True)
    with open(f'data/{KNOWN_NUMBER_OF_SEASONS:05d}/data_{id}_{now_timestamp}.json', 'w') as f:
        json.dump(data, f)
    return data

def retrieveData(id, args=None):
    if args != None:
        id = id + "_" + str(args)
    id = mungeFuncName(id)
    files_found = glob.glob(f"data/data_{id}_*")
    try:
        most_recent_file = max(files_found, key=os.path.getctime)
    except ValueError as err:
        # no files found
        logging.warning(err)
        return None
    data = None
    with open(most_recent_file) as f:
        data = json.load(f)
    return data

def getMainData():
    funcs = [blaseball.get_global_events,
            blaseball.get_all_divisions,
            blaseball.get_offseason_setup,
            blaseball.get_all_teams,
            blaseball.get_simulation_data]
    for func in funcs:
        func_name = str(func.__name__)[4:]
        if REPORT_DATA_RETREVIAL:
            print(func_name)
        request_result = func()
        if REPORT_DATA_RETREVIAL:
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
    if REPORT_DATA_RETREVIAL:
        print(func_name, args)
    request_result = blaseball.failover_500(func, args)
    #request_result = func(args)

    #print(request_result.status_code)
    data = None
    if request_result.status_code == 200:
        #print(request_result)
        if request_result.text == "":
            if REPORT_DATA_RETREVIAL:
                print("\t* * * EMPTY RESULT * * *")
            return data
        #print(request_result.text)
        data = json.loads(request_result.text)
        storeData(data, func_name)
    return data

def retrieveSpecificData(func, args=None):
    func_name = str(func.__name__)[4:]
    request_result = None
    if args != None:
        func_name = func_name + "_" + str(args)
    func_name = mungeFuncName(func_name)
    request_result = retrieveData(func_name)
    if request_result == None:
        return getSpecificData(func, args=args)
    return request_result

def get_GamesOnDay(which_game):
    game_season, game_day = which_game
    URL_BASE = 'https://blaseball.com'
    #print("get_GamesOnDay", game_day, game_season)
    res = requests.get(URL_BASE + '/database/games', params={'day': game_day, 'season': game_season})
    if res.text[:9] == "<!doctype":
        print ("NOT FOUND")
    return res

def getSeasonInfo():
    all_divisions = retrieveData("all_divisions")
    offseason_setup = retrieveData("offseason_setup")
    offseason_recap = retrieveData("offseason_recap")
    all_teams = retrieveData("all_teams")
    simulation_data = retrieveData("simulation_data")

    for n in range(KNOWN_NUMBER_OF_SEASONS):
        getSpecificData(blaseball.get_season, [n])
        getSpecificData(blaseball.get_offseason_recap, [n])
        getSpecificData(blaseball.get_playoff_details, [n])

def getAllPlayerData():
    all_teams = retrieveData("all_teams")
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
                print(".", end="", flush=True)
                getSpecificData(blaseball.get_player_stats, p)
                time.sleep(0.4)

def getTodaysGames(game_season, game_day, retrieve=False):
    if retrieve:
        return retrieveSpecificData(get_GamesOnDay, (game_season, game_day))
    return getSpecificData(get_GamesOnDay, (game_season, game_day))

book_of_facts = {}

def makeFact(key, val):
    book_of_facts.update({key: val})

def getFact(key):
    return book_of_facts[key]

def showAllFacts():
    for k,v in book_of_facts.items():
        print(f"{k}\t{v}")

def storeAllFacts():
    storeData(data, "book_of_facts")

def retrieveAllFacts():
    return retrieveData(data, "book_of_facts")

def reloadAllFactsFromDisk():
    book_of_facts = retrieveAllFacts()

def makeFacts():
    global_ticker = retrieveData("global_ticker")
    all_divisions = retrieveData("all_divisions")
    offseason_setup = retrieveData("offseason_setup")
    offseason_recap = retrieveData("offseason_recap")
    all_teams = retrieveData("all_teams")
    simulation_data = retrieveData("simulation_data")

    # Time
    now_time = datetime.datetime.now().timestamp()
    next_phase_time = dateutil.parser.parse(simulation_data["nextPhaseTime"]).timestamp()
    makeFact(("time", "now"), now_time)
    makeFact(("time", "nextPhaseTime"), next_phase_time)
    makeFact(("time", "TimeUntilNextPhase"), next_phase_time - now_time)

    if True:
        pprint.pprint(global_ticker)
        for msg in global_ticker:
            makeFact(("global_ticker", msg["_id"]), msg["msg"])
        pprint.pprint(all_divisions)
        for d in all_divisions:
            makeFact(("division", d["_id"], "name"), d["name"])
            makeFact(("division", d["_id"], "teams"), d["teams"])
            for t in d["teams"]:
                makeFact(("team", t, "division", "id"), d["_id"])
                makeFact(("team", t, "division", "name"), d["name"])
                # TODO: index facts by team name too
                # makeFact(["team", team_name, "division", "id"], d["_id"],)
                # makeFact(["team", team_name, "division", "name"], d["name"],)

        pprint.pprint(all_teams)
        for t in all_teams:
            pprint.pprint(t)
            for k,v in t.items():
                makeFact(("team", t["_id"], k), v)
                makeFact(("team", t["fullName"], k), v)
            player_roster_categories = ["bench", "bullpen", "rotation", "lineup"]
            player_list = list(itertools.chain.from_iterable([t[prc] for prc in player_roster_categories]))
            makeFact(("team", t["fullName"], "players"), player_list)
            makeFact(("team", t["_id"], "players"), player_list)

        for k,v in simulation_data.items():
            makeFact(("simulation_data", k), v)



    # get past seasons' games
    #for n_season in range(KNOWN_NUMBER_OF_SEASONS + 1):
    # get this season's games
    n_season = KNOWN_NUMBER_OF_SEASONS
    if True:
        for n_game_day in range(120):
            t_games = getTodaysGames(n_season, n_game_day, retrieve=True)
            pprint.pprint(t_games)
            today_game_ids = []
            if t_games != None:
                for game in t_games:
                    today_game_ids.append(game["_id"])
                    for k,v in game.items():
                        makeFact(("game", n_season, n_game_day, game["_id"], k), v)
                makeFact(("game", n_season, n_game_day, "games"), today_game_ids)
    storeAllFacts()
    showAllFacts()
    input()



#getSpecificData(blaseball.get_global_events)
#getMainData()
#getSeasonInfo()
if GET_PLAYER_DATA:
    getAllPlayerData()
#tgames = getTodaysGames(2,0)
#pprint.pprint(tgames)
makeFacts()
