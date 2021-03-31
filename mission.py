import logging
import json
import structure
from unit import Unit as unit_structure
import re
import sys

class Mission(object):
    """docstring for Mission."""

    def __init__(self, arg):
        super(Mission, self).__init__()
        self.params = arg
        self.id = arg['id']
        self.name = arg['caption']
        self.alliance_id = arg['alliance_id']
        self.address = arg['address']
        self.type_id = arg['mtid']
        self.missing_text = arg['missing_text']
        self.patients_count = arg['patients_count']
        self.prisoners_count = arg['prisoners_count']
        self.assigned_units = {}
        self.latitude = arg['latitude']
        self.longitude = arg['longitude']
        self.unit_updated = False
        self.user_id = arg['user_id']
        self.patients = {}
        self.cpatients = None
        logging.info('New incident {} - {}: {}'.format(self.name, self.id, self.address))

    def update(self, arg):
        self.params = arg
        self.id = arg['id']
        self.name = arg['caption']
        self.alliance_id = arg['alliance_id']
        self.address = arg['address']
        self.type_id = arg['mtid']
        self.missing_text = arg['missing_text']
        self.patients_count = arg['patients_count']
        self.prisoners_count = arg['prisoners_count']
        self.latitude = arg['latitude']
        self.longitude = arg['longitude']
        self.unit_updated = False
        self.user_id = arg['user_id']

    def get_required_units(self, web):

        if (self.missing_text):
            # Look through units on scene mark them as required then pull off rest
            regex = r"(\d+)\s([A-Za-z\s]+)"
            matches = re.finditer(regex, self.missing_text, re.MULTILINE)
            required_units = {}
            for matchNum, match in enumerate(matches):
                required_units[match.group(2)] = int(match.group(1))
        else:
            result = web.mission_get_required_units(self.type_id)
            required_units = result

        #     for matchNum, match in enumerate(matches):
        #         required_units[match.group(2)] = int(match.group(1))
        # Sort out who is already there
        required_units['hems'] = 0
        required_units['ambulance'] = 0
        required_units['app'] = 0
        if (self.cpatients is None):
            for id, patient in self.patients.items():
                if ('missing_text' in patient and patient['missing_text'] is not None and 'hems' in patient['missing_text'].lower()):
                    required_units['hems'] = required_units['hems'] + 1
                if ('missing_text' in patient and patient['missing_text'] is not None and 'critical care' in patient['missing_text'].lower()):
                    required_units['app'] = required_units['app'] + 1
                required_units['ambulance'] = required_units['ambulance'] + 1
        else:
            required_units['ambulance'] = self.cpatients['count']
            for crequirement, ccount in self.cpatients['errors'].items():
                if ('critical care' in crequirement.lower()):
                    required_units['app'] = required_units['app'] + ccount
                if ('hems' in crequirement.lower()):
                    required_units['hems'] = required_units['hems'] + ccount

        fresh = {}
        for type, quantity in required_units.items():
            if (type.endswith('s') and not type == 'hems'):
                type = type[:-1]
            if (' or ' in type):
                type = type.split(' or ', 1)[0]
            lower_type = type.lower()
            if (lower_type == 'rescue support vehicle'):
                type = 'rescue support unit'
            if (lower_type == 'armed response personnel'):
                type = 'armed response vehicle (arv)'
                quantity = quantity / 2  # Two personal in every ARV
            if (lower_type == 'prv'):
                type = 'primary response vehicle'
            if (lower_type == 'srv'):
                type = 'secondary response vehicle'
            fresh[type.lower()] = quantity

        # Fresh is units we need
        for type, quantity in fresh.items():
            for key, unit in self.assigned_units.items():  # For each assigned unit
                if (
                    structure.DISPATCH_TYPES[unit.type] == type
                    or ( type == 'app' and unit.type == 10 and unit.name.startswith('AP') )
                ):  # If unit type is the type we are looking for
                    # if (self.missing_text is not None and not self.unit_updated and str(unit.state) == str(3)): # If the missing text is present and the unit is on route
                    #     quantity = quantity - 1
                    # elif (self.missing_text is None):
                    quantity = quantity - 1
            fresh[type] = quantity

        if (self.params['user_id'] is None and len(self.assigned_units) < 1):
            fresh['rapid response vehicle'] = 1

        fresh = {k: v for k, v in fresh.items() if v > 0}

        debug = {}
        for key,unit in self.assigned_units.items():
            if (structure.DISPATCH_TYPES[unit.type] not in debug):
                debug[structure.DISPATCH_TYPES[unit.type]] = 0
            debug[structure.DISPATCH_TYPES[unit.type]] = debug[structure.DISPATCH_TYPES[unit.type]] + 1


        # logging.info([
        #     self.id, self.name, self.missing_text,
        #     debug,
        #     fresh,
        #     self.patients,
        #     self.cpatients
        # ])
        return fresh

    def clear_units(self):
        for unit in self.assigned_units.items():
            if isinstance(unit, unit_structure):
                unit.clear_mission()
        self.assigned_units = {}

    def assign_unit(self, unit):
        unit.set_mission(self)
        if (unit.id not in self.assigned_units):
            self.assigned_units[unit.id] = unit
            self.unit_updated = True # To trigger a manual update (to update the missing text present)
            logging.info('Unit {} - {} assigned to {} - {}'.format(unit.id, unit.name, self.id, self.name))
