import osmium as osm
import pandas as pd
import requests
import shapely.wkb as wkblib

class OSMHandler(osm.SimpleHandler):
    def __init__(self):
        osm.SimpleHandler.__init__(self)
        self.wkbfab = osm.geom.WKBFactory()
        self.osm_data = []

    def tag_inventory(self, elem, elem_type):
        if 'building' in elem.tags:
            obj_dict = {}
            wkb = self.wkbfab.create_multipolygon(elem)
            poly = wkblib.loads(wkb, hex=True)
            obj_dict['type'] = elem_type
            obj_dict['id'] = elem.id
            obj_dict['version'] = elem.version
            obj_dict['visible'] = elem.visible
            obj_dict['ts'] = pd.Timestamp(elem.timestamp)
            obj_dict['uid'] = elem.uid
            obj_dict['user'] = elem.user
            obj_dict['chgset'] = elem.changeset
            obj_dict['geometry'] = poly
            for tag in elem.tags:
                obj_dict[tag.k] = tag.v
            self.osm_data.append(obj_dict)

    # def node(self, n):
    #     self.tag_inventory(n, "node")

    # def way(self, w):
    #     self.tag_inventory(w, "way")

    # def relation(self, r):
    #     self.tag_inventory(r, "relation")
    
    def area(self, o):
        self.tag_inventory(o, "area")

def query_osm(osm_path, csv_path, south=30.29293, west=-97.72175, length=0.008):
    osmhandler = OSMHandler()

    # request by the overpass api 
    # https://overpass-api.de/api/map?bbox=-97.7157,30.2765,-97.6483,30.3069
    east = west + length
    north = south + length
    map = requests.get(f'https://overpass-api.de/api/map?bbox={west},{south},{east},{north}')
    with open(osm_path, 'w', encoding="utf_8_sig") as f:
        f.write(map.text)
    osmhandler.apply_file(osm_path)

    # transform the list into a pandas DataFrame
    df_osm = pd.DataFrame(osmhandler.osm_data)
    df_osm = df_osm.sort_values(by=['type', 'id', 'ts'])
    df_osm.to_csv(csv_path)