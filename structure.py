import math
STATES = {
    1: 'Available',
    2: "Available at station",
    3: "On route",
    4: 'On scene',
    5: 'Waiting/with pt?',
    7: 'Transporting pt'
}

STATE_COLOURS = {
    1: 3,
    2: 3,
    3: 4,
    4: 5,
    5: 5,
    7: 1
}

DISPATCH_TYPES = {
    0: 'fire engine',
    1: 'fire engine',
    2: 'aerial appliance truck',
    3: 'fire officer',
    4: 'rescue support unit',
    5: 'ambulance',
    6: 'water carrier',
    7: 'hazmat unit',
    8: 'police car',
    9: 'hems',
    10: 'rapid response vehicle',
    11: 'dunno 11',
    12: 'dog support units (dsus)',
    13: 'armed response vehicle (arv)',
    14: 'breathing apparatus support unit',
    15: 'incident command and control unit',
    16: 'dunno 16',
    17: 'dunno 17',
    18: 'dunno 18',
    19: 'jru',
    20: 'operational team leader',
    21: 'dunno 21',
    22: 'dunno 22',
    23: 'dunno 23',
    24: 'traffic car'
}


def get_distance(point1, point2):
    return math.sqrt(((point1[0]-point2[0])**2)+((point1[1]-point2[1])**2))
