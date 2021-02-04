#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  5 16:35:55 2020

@author: garyli
"""

import requests
import os
import sys

def mainloop():
    # no arguments - fetch key from os

    key = os.environ['PFF_API_KEY']

    team = sys.argv[1]

    params = get_params(key)

    games = get_games(team, params)
    
    plays = get_plays(games, team, params)
    
    output = suddenChange(plays)
    print(output)
    save_to_txt(output, team)
    
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
        if game['season'] >= 2020:
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
        if play['drive_play'] == 1 and play['drive_start_event'] in ['FUMBLE', 'DOWNS', 'INTERCEPTION', 'FG - MISSED']:
            play_ids.append(str(play['play_id']))
    return play_ids

def save_to_txt(output, team):
    filename = "{}_Sudden_Change.txt".format(team)
    txt_string = ','.join(output)

    with open(filename, 'w', newline ='') as f:
        f.write(txt_string)

mainloop()
    
