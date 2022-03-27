import json
from aiocometd import Client, Extension
import re
import logging

class MyExtension(Extension):
    async def incoming(this, payload, headers=None):
        pass

    async def outgoing(this, payload, headers):
        for element in payload:
            if 'ext' not in payload:
                element['ext'] = {}

            # element['ext']["/private-user2091en_GB"] = "13afdb3a34974419a4aa410f761891ce1242b36a";
            # element['ext']["/private-alliance/52866bc4-a85d-4f89-8c0d-e3cb121513a9/en_GB"] = "aaec8ec969698829d871e1a8d79ea60837f53760";
            # element['ext']["/allen_GB"] = "c6aef8f1e52485d1d95cb5130b82efdbff4c0ff4";
            element['ext']["/allen_GB"] = "c6aef8f1e52485d1d95cb5130b82efdbff4c0ff4"
            element['ext']["/private-alliance/04a6631c-76c2-492f-9b98-15a6a33ecf13/en_GB"] = "e3182feaaae740d688c3904875600177a776348c"
            element['ext']["/private-user2091en_GB"] = "13afdb3a34974419a4aa410f761891ce1242b36a"


class Ws(object):
    """docstring for Ws."""

    async def run(self):
        # connect to the server
        while (True):
            logging.info('Starting WS')
            async with Client("https://www.missionchief.co.uk/faye", extensions=[MyExtension()]) as client:
                await client.subscribe("/allen_GB")
                await client.subscribe("/private-alliance/04a6631c-76c2-492f-9b98-15a6a33ecf13/en_GB")
                await client.subscribe("/private-user2091en_GB")
                logging.info("Subscribed to WS")
                self.queue.put({
                    'type': 'ws_start',
                })
                # listen for incoming messages
                async for message in client:
                    if ('data' not in message):
                        logging.warning('Issue found {}'.format(message))
                    else:
                        matches = re.finditer(r"([a-zA-Z]+)\(\s?([^;]+}?\s?)\);", message['data'], re.MULTILINE)
                        # if (matches.group(1))
                        for match in matches:
                            try:
                                data = json.loads(match.group(2))
                            except json.decoder.JSONDecodeError:
                                logging.info('JSON error reported {}'.format(match.group(2)))
                                data = match.group(2)
                            if match.group(1) == 'missionMarkerAdd':
                                self.add_mission(data)
                            elif match.group(1) == 'patientMarkerAdd':
                                self.queue.put({
                                    'type': 'patient_add',
                                    'data': data
                                })
                            elif match.group(1) == 'patientDelete':
                                self.queue.put({
                                    'type': 'patient_delete',
                                    'data': data
                                })
                                # patientMarkerAddCombined
                            elif match.group(1) == 'patientMarkerAddCombined':
                                self.queue.put({
                                    'type': 'patientcombined_add',
                                    'data': data
                                })
                            elif match.group(1) == 'prisonerMarkerAdd':
                                self.queue.put({
                                    'type': 'prisonermarker_add',
                                    'data': data
                                })
                            elif match.group(1) == 'radioMessage':
                                self.radio_message(data)
                            # elif match.group(1) == 'missionDelete':
                            #     self.del_mission(data)
                            elif match.group(1) == 'deleteMission':
                                self.del_mission(data)
                            elif match.group(1) == 'vehicleMarkerAdd':
                                # matches = re.finditer(r"([a-zA-Z]+)((\s?([^;]+}\s?)));", data, re.MULTILINE)
                                # for match in matches:
                                #     try:
                                #         specific = json.loads(match.group(2))
                                #         self.add_unit(specific)
                                #     except json.decoder.JSONDecodeError:
                                #         continue
                                pass
                            elif match.group(1) == 'vehicleDrive':
                                pass
                            else:
                                logging.info('Not handling {} {}'.format(match.group(1), match.group(2)))

    def del_mission(self, data):
        self.queue.put({
            'type': 'mission_delete',
            'data': data
        })

    def add_unit(self, data):
        self.queue.put({
            'type': 'unit_add',
            'data': data
        })

    def add_mission(self, data):
        # if data['id'] not in self.missions:
            # self.missions[data['id']] = Mission(data)
        self.queue.put({
            'type': 'mission_update',
            'data': data
        })
        # else:
        #     self.missions[data['id']].update(data)

    def radio_message(self, data):
        if (data['type'] == 'vehicle_fms'):
            self.queue.put({
                'type': 'unit_update',
                'data': data
            })
            # if (data['id'] not in self.units):
            #     logging.info('Radio message for {} but could not find in units'.format(data['id']))
            #     return
            # self.units[data['id']].set_state(data['fms_real'])
            # if (data['mission_id'] in self.missions):
            #     self.missions[data['mission_id']].assign_unit(self.units[data['id']])
            # else:
            #     # Clearly not on a mission
            #     self.units[data['id']].mission = None
        else:
            logging.warning('Not handing radioMessage: {}'.format(json.dumps(data)))
