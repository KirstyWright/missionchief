import structure

class Building(object):
    """docstring for Building."""

    def __init__(self, arg):
        super(Building, self).__init__()
        self.params = arg
        self.id = arg['id']
        self.building_type_id = arg['building_type']
        self.name = arg['name']
        self.latitude = arg['latitude']
        self.longitude = arg['longitude']
