import requests
import re
import json
import logging
import sys


class Web(object):
    """docstring for Web."""

    def __init__(self, base_url, cookies):
        super(Web, self).__init__()
        self.cookies = cookies
        self.base_url = base_url

    def get_buildings(self):
        result = requests.get(self.base_url, cookies=self.cookies)
        matches = re.finditer(r"([a-zA-Z]+)\(\s?([^;]+}\s?)\);", result.text, re.MULTILINE)
        buildings = []
        for match in matches:
            try:
                data = json.loads(match.group(2))
            except json.decoder.JSONDecodeError:
                continue
            if match.group(1) == 'buildingMarkerAdd':
                if (data['user_id'] == 2091):
                    buildings.append(data)
        return buildings

    def get_started(self):
        result = requests.get(self.base_url, cookies=self.cookies)
        matches = re.finditer(r"([a-zA-Z]+)\(\s?([^;]+}\s?)\);", result.text, re.MULTILINE)
        results = {'missions':[],'drive':[],'patients':[],'combined_patients':[]}
        for match in matches:
            try:
                data = json.loads(match.group(2))
            except json.decoder.JSONDecodeError:
                continue
            if match.group(1) == 'missionMarkerAdd':
                results['missions'].append(data)
            elif match.group(1) == 'vehicleDrive':
                results['drive'].append(data)
            elif match.group(1) == 'patientMarkerAddCombined':
                results['combined_patients'].append(data)
            elif match.group(1) == 'patientMarkerAdd':
                results['patients'].append(data)
        return results

    def get_units_from_building(self, building_id):
        result = requests.get(self.base_url + '/buildings/{}/vehiclesMap'.format(building_id), cookies=self.cookies)
        matches = re.finditer(r"([a-zA-Z]+)\(\s?([^;]+}\s?)\);", result.text, re.MULTILINE)
        units = []
        for match in matches:
            try:
                data = json.loads(match.group(2))
            except json.decoder.JSONDecodeError:
                continue
            if match.group(1) == 'vehicleMarkerAdd':
                units.append(data)
        # logging.info(units)
        return units

    def get_mission_auth_code(self, mission_id):
        result = requests.get(self.base_url + '/missions/{}'.format(mission_id), cookies=self.cookies)
        matches = re.finditer(r"<meta(.)*content=(\"|')(.*)(\"|')(.)*name=(\"|')csrf-token(\"|')\s?/?>", result.text, re.MULTILINE)
        for match in matches:
            return match.group(3)

    def mission_active(self, mission_id):
        result = requests.get(self.base_url + '/missions/{}'.format(mission_id), cookies=self.cookies)
        return not 'The mission has been successfully completed.' in result.text

    def mission_get_required_units(self, mission_id, mission_type_id):
        url = self.base_url + "/einsaetze/{}?mission_id={}".format(mission_type_id, mission_id)
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8",
            'Accept-Language': "en-GB,en;q=0.5",
            'Connection': "keep-alive",
            'Upgrade-Insecure-Requests': "1",
            'cache-control': "no-cache",
        }
        fresh = {}
        result = requests.request("GET", url, headers=headers, cookies=self.cookies)
        matches = re.finditer(r"<tr>([^<]*<td>([^<]*)<\/td>[^<]*<td>([^<]*)<\/td>)[^<]*<\/tr>", result.text, re.MULTILINE)
        for match in matches:
            key = match.group(2).strip()
            if ('patient codes' in key):
                if ('C-1' in match.group(3)):
                    fresh['rapid response vehicle'] = 1
                continue
            if ('Required' in key and 'Stations' not in key):
                fresh[key[9:]] = int(match.group(3).strip())
        return fresh

    def back_alarm_units(self, units):
        for id, unit in units.items():
            url = self.base_url + "/vehicles/{}/backalarm".format(unit.id)
            headers = {
                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0",
                'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8",
                'Accept-Language': "en-GB,en;q=0.5",
                'Content-Type': "application/x-www-form-urlencoded",
                'Connection': "keep-alive",
                'Referer': "https://missionchief.co.uk/vehicles/{}".format(unit.id),
                'Upgrade-Insecure-Requests': "1",
                'cache-control': "no-cache",
            }
            response = requests.request("GET", url, headers=headers, cookies=self.cookies)

    def dispatch(self, mission_id, unit_ids):
        url = self.base_url + "/missions/{}/alarm".format(mission_id)
        payload = "utf8=%25E2%259C%2593&authenticity_token={}&commit=Dispatch&next_mission=0&alliance_mission_publish=0".format(self.get_mission_auth_code(mission_id))
        vehicle_string = ''
        for id in unit_ids:
            vehicle_string = vehicle_string + '&vehicle_ids%5B%5D={}'.format(id)
        payload = payload + vehicle_string
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8",
            'Accept-Language': "en-GB,en;q=0.5",
            'Content-Type': "application/x-www-form-urlencoded",
            'Connection': "keep-alive",
            'Referer': "https://missionchief.co.uk/missions/{}".format(mission_id),
            'Upgrade-Insecure-Requests': "1",
            'cache-control': "no-cache",
        }
        response = requests.request("POST", url, data=payload, headers=headers, cookies=self.cookies)
        if ('/sign_in' in response.url):
            raise Exception('login_required')
        return response


    def medical_transport(self, unit_id):
        result = requests.get(self.base_url + '/vehicles/{}'.format(unit_id), cookies=self.cookies)
        matches = re.finditer(r"<a(\s)?(href=\")([^\"]*)\"(\s)?class=\"([A-Za-z\s-]*)\"", result.text, re.MULTILINE)
        for match in matches:
            if ("btn-success" in match.group(5) and "patient" in match.group(3)):
                requests.get(self.base_url + match.group(3), cookies=self.cookies)
                return True
        return False

    def prisoner_transport(self, mission_id):
        result = requests.get(self.base_url + '/missions/{}'.format(mission_id), cookies=self.cookies)
        matches = re.finditer(r"<a(\s)?(href=\")([^\"]*)\"(\s)?class=\"([A-Za-z\s-]*)\"", result.text, re.MULTILINE)
        for match in matches:
            if ("btn-success" in match.group(5) and "vehicles" in match.group(3)):
                requests.get(self.base_url + match.group(3), cookies=self.cookies)
                return True
        return False
