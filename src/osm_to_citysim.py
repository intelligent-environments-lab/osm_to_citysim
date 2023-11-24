import geopandas as gpd
import pandas as pd
import numpy as np
from shapely import wkt
import pdb
import pyproj
from box import Box
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import copy
from operator import itemgetter

def prepare_gdf(file_path):
    df = pd.read_csv(file_path)
    df['geometry'] = df['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, crs='epsg:4326')
    gdf = gdf.to_crs(32614)
    return gdf

def find_min_xy(gdf):
    bounds = gdf.geometry.apply(lambda x: x.bounds).tolist()
    return min(bounds, key=itemgetter(0))[0], min(bounds, key=itemgetter(1))[1]

def cor_from_xy(x1, x2, y1, y2, height):
    return [[x2, y2, height], [x1, y1, height], [x1, y1, 0], [x2, y2, 0], [x2, y2, height]]

def export_bud_xml(x_list, y_list, height, bud_id):
    bud_tree = ET.parse('./data/building.xml')
    bud_root = bud_tree.getroot()
    bud_root.set('id', str(bud_id))
    
    # walls
    w_node = copy.deepcopy(bud_root.find('Zone').find('Wall'))
    # first delete current walls
    for wall in bud_root.find('Zone').findall('Wall'):
        bud_root.find('Zone').remove(wall)
    # then add new walls
    for i in range(len(x_list) - 1):
        new_w_node = copy.deepcopy(w_node)
        new_w_node.set('id', str(i))
        x1, x2 = x_list[i], x_list[i + 1]
        y1, y2 = y_list[i], y_list[i + 1]
        cors = cor_from_xy(x1, x2, y1, y2, height)
        for node_v, cor in zip(new_w_node, cors):
            node_v.set('x', str(cor[0]))
            node_v.set('y', str(cor[1]))
            node_v.set('z', str(cor[2]))
        bud_root.find('Zone').append(new_w_node)
    
    # roof 
    r_node = bud_root.find('Zone').find('Roof')
    for i in range(len(x_list)):
        v_tag = 'V' + str(i)
        if r_node.find(v_tag) is not None:
            v_node = r_node.find(v_tag)
        else:
            v_node = ET.SubElement(r_node, v_tag)
        v_node.set('x', str(x_list[i]))
        v_node.set('y', str(y_list[i]))
        v_node.set('z', str(height))
    
    # floor
    f_node = bud_root.find('Zone').find('Floor')
    for i in range(len(x_list)):
        v_tag = 'V' + str(i)
        if f_node.find(v_tag) is not None:
            v_node = f_node.find(v_tag)
        else:
            v_node = ET.SubElement(f_node, v_tag)
        v_node.set('x', str(x_list[i]))
        v_node.set('y', str(y_list[i]))
        v_node.set('z', "0.00")

    return bud_root

def write_citysim_xml(gdf_path, export_path):
    gdf = prepare_gdf(gdf_path)
    minx, miny = find_min_xy(gdf)

    base_tree = ET.parse('./data/base.xml')
    root = base_tree.getroot()
    dis = root.find('District')
    height_list = gdf['height'][gdf['height'].notna()].to_numpy()
    for i, row in gdf.iterrows():
        geometry = row['geometry']
        cor_list = geometry.geoms[0].exterior.coords
        x_list = [cor[0] - minx for cor in cor_list]
        y_list = [cor[1] - miny for cor in cor_list]
        height = row['height']
        if np.isnan(height):
            # random pick height from height_list
            height = np.random.choice(height_list, 1).item()
        bud_root = export_bud_xml(x_list, y_list, height, i)
        dis.append(bud_root)
    
    # before export prettify them
    ET.indent(base_tree, space="\t", level=0) 
    base_tree.write(export_path)

if __name__ == '__main__':                
    bud_param = Box.from_yaml(filename="BUD_PARAM.yaml") 

    write_citysim_xml('./test.csv', 'test.xml')