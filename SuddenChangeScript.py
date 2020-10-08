#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  5 16:35:55 2020

@author: garyli
"""

import requests
import os

def mainloop():
    # no arguments - fetch key from os

    key = os.environ['PFF_API_KEY']

    team = "MDUN"

    params = get_params(key)

    games = get_games(team, params)
    
    plays = get_plays(games, team, params)
    
    output = suddenChange(plays)
    print(output)
    
def get_params(key):
    params = {'x-api-key':key}
    r = requests.post('https://api.profootballfocus.com/auth/login', headers = params)
    jwt = r.json()['jwt']
    params = {'Authorization':'Bearer ' + jwt}
    return params

def get_games(team, params):
    r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games', headers=params)
    games = []
    for game in r.json()['games']:
        if game['season'] == 2019:
            if game['away_team'] == team or game['home_team'] == team:
                games.append(str(game['id']))
    return games

def get_plays(games, team, params):
    plays = []
    for game in games:
        r = requests.get('https://api.profootballfocus.com/v1/video/ncaa/games/'+game+'/plays', headers = params)
        for play in r.json()['plays']:
            if play['defense'] == team:
                plays.append(play)
    return plays

def suddenChange(plays):
    play_ids = []
    for play in plays:
        if play['drive_play'] == 1 and play['drive_start_event'] in ['FUMBLE', 'DOWNS', 'INTERCEPTION', 'MISSED FG', 'PUNT - BLOCKED', 'KICKOFF - RECOVERY']:
            play_ids.append(play['play_id'])
    return play_ids

mainloop()
    