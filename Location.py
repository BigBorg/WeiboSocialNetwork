# -*- encoding: utf-8 -*-
import urllib.request, urllib.parse, urllib.error
import json


class LocationService(object):
    def __init__(self, key):
        self.key = key

    def get_geo_GCJ(self, location):
        '''
        Chinese Standard
        '''
        api = "http://restapi.amap.com/v3/geocode/geo?"
        try:
            fhand = urllib.request.urlopen( api + urllib.parse.urlencode({'key':self.key,'address':location}) )
            response = fhand.read().decode("utf-8")
            response = json.loads(response)
        except Exception as e:
            print("Geode connection fail")
            print(e)
            return None,None
        try:
            geo_list = response['geocodes'][0]['location'].split(',')
            lon = float(geo_list[0])
            lat = float(geo_list[1])
            return lat,lon
        except Exception as e:
            return None,None

    def get_geo_WGS(self,location):
        '''
        International Standard
        '''
        lat_gcj, lon_gcj = self.get_geo_GCJ(location)
        if lat_gcj!= None and lon_gcj!=None:
            try:
                api = 'http://api.zdoz.net/transgps.aspx?'
                fhand = urllib.request.urlopen( api + urllib.parse.urlencode({'lat':lat_gcj,'lng':lon_gcj}) )
                response = fhand.read().decode("utf-8")
                response = json.loads(response)
            except Exception as e:
                print("ZODZ connection fail")
                print(e)
                return None,None
        else:
            response = dict()
        try:
            lat_wgs = response['Lat']
            lon_wgs = response['Lng']
            return lat_wgs,lon_wgs
        except Exception as e:
            return None,None

if __name__=='__main__':
    service = LocationService("Your Key")
    service.get_geo_WGS("Location")