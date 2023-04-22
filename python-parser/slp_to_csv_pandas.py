import numpy
import pandas as pd 
import io
import shutil
import os
import zipfile
import csv
import glob


# Data Model:

#          (Player_1) (Player_2)
#                \      /
#                 (Game)
#                  ||||
#   (frame)------( frame )------(frame)
#      /\            /\            /\
# (port)(port)  (port)(port)  (port)(port)




#                                                                      Node Data maps

# all fields except id, port number, and label
# lambdas are executed from the context of Game.Player
player_nodes_datamap = {
    'team': (lambda p: p.team),
    'stocks': (lambda p: p.stocks),
    'costume': (lambda p: p.costume),
    'character': (lambda p: p.character),
    'consciousness': (lambda p: p.type),
    'ucf_dash_back': (lambda p: p.ucf.dash_back),
    'ucf_shield_drop': (lambda p: p.ucf.shield_drop),
    'portNum': (lambda _: None),
    'playerId': (lambda _: None),
    ':LABEL': (lambda _: "Player"),
}

# all fields except id and label
# lambdas are executed from the context of Game
# format is:
# 'header-field': [csv description of data type, lambda to find data from game]
game_nodes_datamap = {
    'pal':       (lambda g: g.start.is_pal),
    'stage':     (lambda g: g.start.stage),
    'teams':     (lambda g: g.start.is_teams),
    'frozenPS':  (lambda g: g.start.is_frozen_ps),
    'numFrames': (lambda g: len(g.frames)),
    'gameId':    (lambda _: None),
    ':LABEL':    (lambda _: "Game"),
}

# all fields except id, frame, and label
# lambdas are executed from the context of a Frame.Port
port_nodes_datamap = {
    'posX': (lambda p: p.leader.post.position.x),
    'posy': (lambda p: p.leader.post.position.y),
    'jumps': (lambda p: p.leader.post.jumps),
    'state': (lambda p: p.leader.post.state),
    'stocks': (lambda p: p.leader.post.stocks),
    'shield': (lambda p: p.leader.post.shield),
    'damage': (lambda p: p.leader.post.damage),
    'ground': (lambda p: p.leader.post.ground),
    'hitStun': (lambda p: p.leader.post.hit_stun),
    'lCancel': (lambda p: p.leader.post.l_cancel),
    'airborne': (lambda p: p.leader.post.airborne),
    'stateAge': (lambda p: p.leader.post.state_age),
    'direction': (lambda p: p.leader.post.direction),
    'lastHitBy': (lambda p: p.leader.post.last_hit_by),
    'comboCount': (lambda p: p.leader.post.combo_count),
    'lastAttackLanded': (lambda p: p.leader.post.last_attack_landed),
    'portId': (lambda _: None),
    'frame': (lambda _: None),
    ':LABEL': (lambda _: "Port"),
}


# Dictionary of all node types
node_types = {
    "player": {datamap: player_nodes_datamap},
    "Game":   {datamap: game_nodes_datamap  },
    "Frame":  {datamap: frame_nodes_datamap },
    "Port":   {datamap: port_nodes_datamap  }
}

#                                                                    Edge Datamaps

played_in_edges_datamap = {
    ':TYPE':             "played_in",
    ':START_ID(Player)': None,
    ':END_ID(Game)':     None
}

processed_in_edges_datamap = {
    ':TYPE':             "processed",
    ':START_ID(Game)':   None,
    ':END_ID(Frame)':    None
}

contained_in_edges_datamap = {
    ':TYPE':             "contained",
    ':START_ID(Frame)':  None,
    ':END_ID(Port)':     None
}

# Dictionary of all edge types
edge_types = {
    played_in: {datamap: played_in_edges_datamap},
    processed: {datamap: processed_in_edges_datamap},
    contained: {datamap: contained_in_edges_datamap}
}

#                                                 Filepaths

upload_path  = "/zips/"
slps_path    = "/tmp_slp_files/"

import_path  = "/import/"
nodes_path      = import_path + "nodes/"
game_n_path     = nodes_path + "games/"
ports_n_path    = nodes_path + "ports"
frames_n_path   = nodes_path + "frames"
player_n_path   = nodes_path + "players/"

rels_path    = import_path + "rels/"
played_in_e_path = rels_path + "played_in/"
processed_e_path = rels_path + "processed/"
contained_e_path = rels_path + "contained/"

game_count = 0

#                                                       Local Tables


#                                                       CSV Conversion Methods


# root method for csvifying a slippi directory
def csvify(slp, game_id):
    
    for player_idx, player in enumerate(slp.start.players):
        if player is None:
            continue

# Extracts one game at a time from the slippi zips found in the upload_path
def slp_extract(zd):
    try:
        with zipfile.ZipFile(zd, "r") as slp_dir:
            slps = [slp for slp in zipfile.ZipFile.namelist(slp_dir) if slp[-4:] == ".slp"]
            for slp in slps:
                global game_count
                slp_path = slp_dir.extract(slp, slps_path)
                g = Game(slp_path)
                csvify(g, game_count)
                game_count += 1
                print("Parsed game count: " + str(game_count))
            
    except zipfile.BadZipFile as error:
        print(error)