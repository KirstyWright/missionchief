import logging
import structure

class Unit(object):
    """docstring for Unit."""

    def __init__(self, arg, building):
        super(Unit, self).__init__()
        self.params = arg
        self.mission = None
        self.state = arg['fms_real']
        self.id = arg['id']
        self.name = arg['c']
        self.type = arg['t']
        self.latitude = None
        self.longitude = None
        self.building = building

    def set_state(self, fms_real):
        self.state = fms_real
        logging.info('Unit {} - {} state {} - {}'.format(self.id, self.name, self.state, structure.STATES[fms_real]))

    def set_mission(self, mission):
        self.mission = mission

    def clear_mission(self):
        self.mission = None

    # TODO:
    def get_location(self):
        # if (self.state == '2'):
        if (True):
            return [self.building.longitude, self.building.latitude]
        else:
            return [self.longitude, self.latitude]
