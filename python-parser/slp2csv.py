import io
import shutil
import os
import zipfile
import csv
import glob
from slippi import Game

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

game_csv_fields = list(game_nodes_datamap.keys())

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

player_csv_fields = list(player_nodes_datamap.keys())

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

port_rels_datamap = {
    ':TYPE': None,
    ':START_ID': None,
    ':END_ID': None
}

upload_path = "/zips/"
slps_path = "/tmp_slp_files/"
import_path = "/import/"
games_path  = "/import/nodes/games/"
players_path = "/import/nodes/players/"
ports_path = "/import/nodes/ports/"
rels_path = "/import/rels/"
game_count = 0

port_csv_fields = list(port_nodes_datamap.keys())
port_rel_csv_fields = list(port_rels_datamap.keys())

# accepts an object to apply a data map against, returning the mapped data
def applyDataMap(o, m):
    out_map = {}
    for item in m.items():
        out_map[item[0]] = item[1][1](o)
    return out_map

def applyPortDataMap(frame, game_id, player_idx, frame_idx): 
    port_row = applyDataMap(frame.ports[player_idx], port_nodes_datamap)
    port_row['frame']  = frame_idx
    port_row['portId'] = "port-" + str(game_id) + "-" + str(player_idx) + "-" + str(frame_idx)

    return port_row 

def buildPortRels(port_nodes, rel_type):
    return [{':TYPE': rel_type, ':START_ID': port_nodes[i]['portId'], ':END_ID': port_nodes[i + 1]['portId'] } for i in range(len(port_nodes) - 2)]

def buildPortNodes(frames, game_id, player_idx):
    return [applyPortDataMap(frame, game_id, player_idx, frame_idx) for frame_idx, frame in enumerate(frames)]

def makeGameCSV(slp, game_id):
    with open(games_path + "games.csv",'a', newline='') as c:
        game_writer = csv.DictWriter(c, fieldnames=game_csv_fields)

        game_row = applyDataMap(slp, game_nodes_datamap)
        game_row['gameId'] = "game-" + str(game_id)

        game_writer.writerow(game_row) 

def makePortCSV(slp, game_id, player_idx):
    port_nodes = buildPortNodes(slp.frames, game_id, player_idx)

    with open(ports_path + str(game_id) + "_" + str(player_idx) + ".csv", "w", newline='') as c:
        port_writer = csv.DictWriter(c, fieldnames=port_csv_fields)
        port_writer.writerows(port_nodes)

    # Creating edges between ports
    with open(rels_path + str(game_id) + "_" + str(player_idx) + ".csv", "w", newline='') as c:
        port_writer = csv.DictWriter(c, fieldnames=port_rel_csv_fields)
        port_writer.writerows(buildPortRels(port_nodes, "precedes"))
        port_writer.writerows(buildPortRels(list(reversed(port_nodes)), "follows"))
    
def makePlayerCSV( slp, game_id, player, player_idx): 
    with open(players_path + "players.csv", "a", newline='') as c:
        player_writer = csv.DictWriter(c, fieldnames=player_csv_fields)
        
        player_row = applyDataMap(player, player_nodes_datamap)
        player_row['portNum']  = player_idx
        player_row['playerId'] = "player-" + str(game_id) + "-" + str(player_idx)

        player_writer.writerow(player_row)
    
    # Data modeling, create edges between player and frames
    with open(players_path)

# def makeCSVHeaders(node_type):
#     if(headers arent found):
#         with open(import_path + node_type + "_header.csv", "a", newline='') as c:
#             csv_fields = [str(i[0])+i[1][0] for i in eval('node_type'+"_nodes_datamap"].items())].
#             h_writer = csv.DictWriter(c, fieldnames=cav_fields)
#             h_writer.writerow(csv_fields)

def csvify(slp, game_id):
    makeGameCSV(slp,game_id)
    for player_idx, player in enumerate(slp.start.players):
        if player is None:
            continue
        makePlayerCSV( slp, game_id, player, player_idx)
        makePortCSV( slp, game_id, player_idx)

def clear_dir(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))

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

# Looks in /zips for zipped directories of slp files
# unzips each zipped directory into a same-named subdirectory within /zips/slp_files
# Loops through each subdirectory within /zips/slp_files/
#   Loops through each slp file within the subdirectory
#       creates csv files of graph representations for slp file
# Clears subdirectories within uploads/slp_files
# Clears zipped directories from /zips
print("from slp2csv, checking import directory status")
# hc = 
# import_contents = os.scandir(import_path)
# for ic in import_contents:

# for node_check in ["game", "player", "port"]:
#     if os.path.is_file(node_check+"_header.csv"):
#         print(node_check+ " header file found")
#     else:
#         print("Creating header: "+node_check)
#         makeCSVHeader(node_check)


print("From slp2csv, checking uploaded files")

for zd in os.scandir(upload_path):
    print("parsing directories:")
    zipfile.is_zipfile(zd):
        print(zd.path)
        slp_extract(zd.path)

