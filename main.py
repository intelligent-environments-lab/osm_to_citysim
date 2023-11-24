from src.osm_reader import query_osm
from src.osm_to_citysim import prepare_gdf, write_citysim_xml
import argparse
from pathlib import Path
import pdb

def main(args):
    export_path = Path('./export')
    file_name = f'west_{args.west}_south_{args.south}_length_{args.length}'
    osm_path = export_path / 'osm' / f'{file_name}.osm'
    csv_path = export_path / 'csv' / f'{file_name}.csv'
    xml_path = export_path / 'xml' / f'{file_name}.xml'
    osm_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    xml_path.parent.mkdir(parents=True, exist_ok=True)

    query_osm(osm_path, csv_path, args.south, args.west, args.length)
    write_citysim_xml(csv_path, xml_path)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Query OSM data for CitySim usage')
    parser.add_argument('-L', '--length', metavar='L', type=float, default=0.008)
    parser.add_argument('-W', '--west', metavar='W', type=float)
    parser.add_argument('-S', '--south', metavar='S', type=float)
    args = parser.parse_args()

    main(args)