from web import Web
import json
import logging
import splinter
import time
from unit import Unit
import structure
from mission import Mission
import queue
from console import Console
from building import Building
import datetime
import jsonpickle


class Manager(object):
    """docstring for Manager."""

    def __del__(self):
        self.browser.quit()

    def __init__(self, username, password):
        super(Manager, self).__init__()
        self.base_url = 'https://www.missionchief.co.uk'
        self.browser = splinter.Browser('firefox', headless=True)
        self.username = username
        self.password = password

        self.units = {}
        self.buildings = {}
        self.missions = {}
        self.cookies = None
        self.get_login_cookies()
        self.console = Console()
        self.mission_updates = []

    def refresh_units(self):
        logging.info("Refreshing units")
        for building in self.web.get_buildings():
            if building['id']:
                self.buildings[building['id']] = Building(building)
        for id, building in self.buildings.items():
            units = self.web.get_units_from_building(building.id)
            for unit in units:
                # if (unit['id'] not in self.units):
                    # logging.info('Found unit {} - {} stationed at {} - {}'.format(unit['id'], unit['c'], building.id, building.name))
                self.units[unit['id']] = Unit(unit, building)
                if (unit['fms_real'] == 5):
                    self.web.medical_transport(unit['id'])

    def refresh_missions(self):
        results = self.web.get_started()
        for mission in results['missions']:
            if (mission['user_id'] != 2091):
                logging.info('mission of id {} is not owned by 2091 - {}'.format(mission['id'], mission['user_id']))
                continue
            if str(mission['id']) not in self.missions:
                self.missions[str(mission['id'])] = Mission(mission)
            else:
                self.missions[str(mission['id'])].update(mission)
        for drive in results['drive']:
            self.queue.put({
                'type': 'unit_update',
                'data': {
                    'id': drive['id'],
                    'fms_real': drive['fms_real'],
                    'mission_id': drive['mid']
                }
            })
        for patient in results['combined_patients']:
            self.queue.put({'type':'patientcombined_add','data':patient})
        for patient in results['patients']:
            self.queue.put({'type':'patient_add','data':patient})

    def update_single(self, data):
        item = data['data']
        if data['type'] == 'mission_add' or data['type'] == 'mission_update' or data['type'] == 'mission_delete':
            self.mission_updates.append(item)
        elif data['type'] == 'unit_update':
            if (item['id'] not in self.units):
                # logging.info('Radio message for {} but could not find in units'.format(item['id']))
                # logging.info(data)
                return
            self.units[item['id']].set_state(item['fms_real'])
            if (item['fms_real'] == 5):
                self.web.medical_transport(item['id'])
            if (str(item['mission_id']) in self.missions):
                # logging.info('unit id in mission {} {}'.format(item['id'], item['mission_id']))
                self.missions[str(item['mission_id'])].assign_unit(self.units[item['id']])
            else:
                # Clearly not on a mission
                # logging.info('unit id NOT on mission {} {}'.format(item['id'], item['mission_id']))
                self.units[item['id']].clear_mission()
        elif data['type'] == 'patient_add':
            if (str(item['mission_id']) in self.missions):
                self.missions[str(item['mission_id'])].patients[str(item['id'])] = item
            else:
                if ('loop' not in item):
                    item['loop'] = 0
                item['loop'] = item['loop'] + 1
                if (item['loop'] < 5):
                    self.queue.put({'type':'patient_add','data':item})
        elif data['type'] == 'patientcombined_add':
            if (str(item['mission_id']) in self.missions):
                self.missions[str(item['mission_id'])].cpatients = item
            else:
                if ('loop' not in item):
                    item['loop'] = 0
                item['loop'] = item['loop'] + 1
                if (item['loop'] < 5):
                    self.queue.put({'type':'patientcombined_add','data':item})
        else:
            logging.info('cannot deal with below')
            logging.info(data)

    def update_data(self):
        size = self.queue.qsize()
        loop = 1
        while loop < (size + 1):
            try:
                item = self.queue.get(False)
                self.update_single(item)
                loop = loop + 1
            except queue.Empty:
                break

        with open('web/public/missionchief.json', 'w') as outfile:
            data={
                'missions': self.missions,
                'units': self.units,
                'updated_at': '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
            }
            data = jsonpickle.encode(data, unpicklable=False)
            outfile.write(data)
            print("--end loop--")

    def run(self):

        while True:
            try:
                item = self.queue.get(False)
                if (item['type'] == 'ws_start'):
                    break
            except queue.Empty:
                time.sleep(1)
                continue

        self.web = Web(self.base_url, self.cookies)
        self.refresh_units()
        self.refresh_missions()
        self.update_data()
        self.console.update(self.units, self.missions)
        while True:
            try:
                reserved_units = {}
                units_already_sent = []

                mission_updates = self.mission_updates
                self.mission_updates = []

                for update in mission_updates:
                    if str(update['id']) not in self.missions:
                        if ('type' in update and update['type'] == 'delete'):
                            logging.info('Just tried to delete a mission which we never had? {}'.format(update['id']))
                            continue
                        if (update['user_id'] != 2091):
                            logging.info('mission of id {} is now owned by 2091 - {}'.format(update['id'], update['user_id']))
                            continue
                        self.missions[str(update['id'])] = Mission(update)
                    elif 'type' in update and update['type'] == 'delete':
                        del self.missions[str(update['id'])]
                    else:
                        self.missions[str(update['id'])].update(update)

                self.update_data() # Run the process queue (not related to mission)

                available_units_at_start = self.get_available_units([])
                for key, mission in self.missions.items():
                    if (not self.web.mission_active(mission.id)):
                        self.queue.put({
                            'type': 'mission_delete',
                            'data': {'id': mission.id, 'type': 'delete'}
                        })
                        mission.clear_units()
                        logging.info("Mission ended: {}, {}".format(mission.id, mission.name))
                        continue
                    self.console.update(self.units, self.missions)
                    available_units = self.get_available_units(units_already_sent, available_units_at_start)
                    required_units = mission.get_required_units(self.web)
                    # logging.info('Required units: {}'.format(required_units))
                    sending_ids = []
                    for type, quantity in required_units.items():
                        # Does available units check each time
                        type_sending_ids = []
                        if (type not in reserved_units):
                            type_sending_ids = self.get_closest_units(mission.latitude, mission.longitude, type, quantity, available_units)
                            sending_ids = sending_ids + type_sending_ids
                            units_already_sent = units_already_sent + type_sending_ids
                        if (len(type_sending_ids) < quantity):
                            if (type not in reserved_units):
                                reserved_units[type] = 0
                            reserved_units[type] = reserved_units[type] + (quantity - len(type_sending_ids))
                    if (len(sending_ids) > 0):
                        logging.info('Dispatching units to {} - {} : {}'.format(mission.id, mission.name, sending_ids))
                        self.web.dispatch(mission.id, sending_ids)
                        time.sleep(1)
                if (len(reserved_units) > 0):
                    logging.info("Required to complete stack: {}".format(reserved_units))

                time.sleep(1)
            except Exception as instance:
                logging.exception(instance)
                time.sleep(5)
                self.get_login_cookies()
                self.web = Web(self.base_url, self.cookies)
                self.refresh_missions()
                self.update_data()
                logging.info('Needed to relogin')

    def get_closest_units(self, latitude, longitude, word_type, quantity, available_units):
        unit_distances = {}
        word_type = word_type.lower()
        for unit_id, unit in available_units.items():
            if (word_type == 'app' and unit.type == 10 and unit.name.startswith('AP')):
                # If we are getting critical care and unit type is an RRV
                pass  # ie continue into the block
            elif (word_type != structure.DISPATCH_TYPES[unit.type]):
                continue
            distance = structure.get_distance([longitude, latitude], unit.get_location())
            while True:
                # Deal with two or more units at the same station
                if (distance in unit_distances):
                    distance = distance + 0.0000001
                else:
                    break
            unit_distances[distance] = unit.id

        keys = sorted(unit_distances.keys())
        closest_units = []
        count = 0
        for distance in keys:
            count += 1
            closest_units.append(unit_distances.pop(distance))
            if (count >= quantity):
                break

        return closest_units

    def get_available_units(self, units_already_sent, units_to_pick_from=None):
        available_units = {}
        if (units_to_pick_from):
            units = units_to_pick_from.items()
        else:
            units = self.units.items()
        for key, unit in units:
            if (units_already_sent and unit.id in units_already_sent):
                continue
            if (unit.state in [1, 2] and unit.mission is None):
                available_units[unit.id] = unit
        return available_units

    def get_login_cookies(self):
        # Visit URL
        try:
            logging.info("Logging in")
            url = "https://www.missionchief.co.uk/users/sign_in"
            self.browser.visit(url)
            time.sleep(2)
            # Filling in login information
            self.browser.fill("user[email]", self.username)
            self.browser.fill("user[password]", self.password)
            # Submitting login
            self.browser.find_by_name('commit').click()
            self.browser.visit('https://www.missionchief.co.uk')
            self.cookies = self.browser.cookies.all()
            logging.info('logged in')
        except splinter.exceptions.ElementDoesNotExist:
            self.cookies = self.browser.cookies.all()
            logging.info('logged in')
