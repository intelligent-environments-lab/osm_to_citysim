import xml.etree.ElementTree as ET
import pdb
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import axes3d
from scipy.stats import truncexpon


class Street:
    direction = 'vertical'
    width = 3.05
    x = 0
    y = 0

    def __init__(self, direction: str, width: float, x: float, y: float) -> None:
        self.direction = direction
        self.width = width
        self.x = x
        self.y = y


class Building:
    length = 0
    width = 0
    height = 0
    x = 0
    y = 0

    def __init__(self, length: int, width: int, height: int, x: int, y: int) -> None:
        self.length = length
        self.width = width
        self.height = height
        self.x = x
        self.y = y


def edit_height_on_xml(xml_file_path: str, height) -> None:
    my_tree = ET.parse(xml_file_path)
    root = my_tree.getroot()
    for buds in root.iter('Building'):
        new_random_height = float(random.randrange(5, 205, 5))
        for wall in buds.iter('Wall'):
            for node_v in wall:
                # if z of node_v is not equal to zero, change that to a random height
                old_height = float(node_v.get('z'))
                if old_height != 0:
                    node_v.set('z', str(new_random_height))

        for roof in buds.iter('Roof'):
            for node_v in roof:
                # if z of node_v is not equal to zero, change that to a random height
                old_height = float(node_v.get('z'))
                if old_height != 0:
                    node_v.set('z', str(new_random_height))

        # no need to change floor since we we only modify height.

    my_tree.write('test_2.xml')


def auto_generate_urban_layout(
    lat_length: float,
    lon_length: float,
    export_path: str,
    index: int,
    street_width: float = 3.05,
    building_max_widrh: int = 100,
    building_min_width: int = 10,
) -> None:
    '''
    This function will generate a urban layout based on the given parameters.
    '''
    total_area = lat_length * lon_length
    mask = np.zeros((lat_length, lon_length))
    # auto-generate streets
    streets = []
    street_num = 4
    for street_id in range(street_num):
        new_street = Street(
            direction=random.choice(['vertical', 'horizontal']),
            width=street_width,
            x=random.randrange(0, lon_length, 5),
            y=random.randrange(0, lat_length, 5),)
        # modify current mask
        gap = int(new_street.width // 2)
        if new_street.direction == 'vertical':
            print(f'new street {street_id} is vertical')
            mask[:, (new_street.y - gap):(new_street.y + gap + 1)] = 1
        else:
            print(f'new street {street_id} is horizontal')
            mask[(new_street.x - gap):(new_street.x + gap + 1), :] = 1
        streets.append(new_street)

    # auto-generate buildings
    area = mask.sum()
    buds = []
    niter = 0
    while area < 0.35 * total_area:
        n_flooor = np.round(truncexpon.rvs(6.8, scale=3))
        n_flooor += 1 if n_flooor == 0 else 0
        bud = Building(
            length=random.randrange(building_min_width, building_max_widrh, 10),
            width=random.randrange(building_min_width, building_max_widrh, 10),
            height= n_flooor * 3.5,
            x=random.randint(0, lon_length),
            y=random.randint(0, lat_length),
        )
        niter += 1
        # check if bud is out of bounds
        # if niter == 100000:
        #     break
        if bud.y + bud.length >= lat_length or bud.x + bud.width >= lon_length:
            continue
        # check if bud is not covering the street
        if mask[bud.x:(bud.x + bud.width), bud.y:(bud.y + bud.length)].sum() != 0:
            continue
        mask[bud.x:(bud.x + bud.width), bud.y:(bud.y + bud.length)] = bud.height
        buds.append(bud)
        area = np.count_nonzero(mask)
        # else:
        # raise ValueError('new building is out of range.')
        # print('new building is out of range.')
    print(f'number of iterations: {niter}, number of buildings: {len(buds)}')
    plot_3d_mask_street_building(mask, streets, buds, index)
    he_list = [b.height for b in buds]
    plt.hist(he_list, bins=20)
    plt.savefig(f'figs/hist/random_{index}.png')
    plt.close()
    export_citysim_xml(buds, export_path)
    return None

def v_value_from_cor(bud):
    x1, x2 = bud.x, bud.x + bud.width
    y1, y2 = bud.y, bud.y + bud.length
    height = bud.height
    return [[[x2, y2, height], [x2, y2, 0], [x1, y2, 0], [x1, y2, height], [x2, y2, height]], # wall 0
            [[x1, y2, height], [x1, y2, 0], [x1, y1, 0], [x1, y1, height], [x1, y2, height]], # wall 1
            [[x1, y1, height], [x1, y1, 0], [x2, y1, 0], [x2, y1, height], [x1, y1, height]], # wall 2
            [[x2, y1, height], [x2, y1, 0], [x2, y2, 0], [x2, y2, height], [x2, y1, height]], # wall 3
             ]

def roof_v_value(bud):
    x1, x2 = bud.x, bud.x + bud.width
    y1, y2 = bud.y, bud.y + bud.length
    return [[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]

def export_citysim_xml(buds, export_path):
    my_tree = ET.parse('base.xml')
    root = my_tree.getroot()
    dis = root.find('District')
    for i, bud in enumerate(buds):
        bud_tree = ET.parse('building.xml')
        bud_root = bud_tree.getroot()
        bud_root.set('id', str(i))
        v_values = v_value_from_cor(bud)
        for wall, wall_cors in zip(bud_root.iter('Wall'), v_values):
            for node_v, cors in zip(wall, wall_cors):
                node_v.set('x', str(cors[0]))
                node_v.set('y', str(cors[1]))
                node_v.set('z', str(cors[2]))
        roof_v = roof_v_value(bud)
        for roof in bud_root.iter('Roof'):
            for node_v, cor in zip(roof, roof_v):
                node_v.set('x', str(cor[0]))
                node_v.set('y', str(cor[1]))
                node_v.set('z', str(bud.height))
        
        for floor in bud_root.iter('Floor'):
            for node_v, cor in zip(floor, roof_v):
                node_v.set('x', str((cor[0])))
                node_v.set('y', str(cor[1]))
                node_v.set('z', str(0))

        dis.append(bud_root) # add to root

    # before export prettify them
    ET.indent(my_tree, space="\t", level=0) 
    my_tree.write(export_path)

def plot_3d_mask_street_building(mask, streets, buildings, index):
    # init figure
    fig = plt.figure(figsize=plt.figaspect(.5))

    ax = fig.add_subplot(1, 2, 1)

    ax.imshow(mask)

    ax = fig.add_subplot(1, 2, 2, projection='3d')

    x = np.arange(mask.shape[0])
    y = np.arange(mask.shape[1])
    xv, yv = np.meshgrid(x, y, indexing='ij')
    for street in streets:
        gap = int(street.width // 2)
        if street.direction == 'vertical':
            zero_ela = np.zeros(xv[:, (street.y - gap):(street.y + gap + 1)].shape)
            ax.plot_surface(xv[:, (street.y - gap):(street.y + gap + 1)], yv[:, (street.y - gap):(street.y + gap + 1)], zero_ela, color='black')
        else:
            zero_ela = np.zeros(xv[(street.x - gap):(street.x + gap + 1), :].shape)
            ax.plot_surface(xv[(street.x - gap):(street.x + gap + 1), :], yv[(street.x - gap):(street.x + gap + 1), :], zero_ela, color='black')


    # plt.show()
    for bud in buildings:
        ax.bar3d(bud.x, bud.y, 0, bud.width, bud.length, bud.height, shade=True, color=cm.jet(bud.height / 70))
    ax.view_init(33, 44, 0)
    plt.tight_layout()
    plt.savefig(f'figs/3d/random_{index}.png')
    plt.close()
    return

def plot_roof(roof):
    xy = []
    for node_v in roof:
        xy.append([float(node_v.get('x')), float(node_v.get('y'))])
    xy = np.array(xy)
    plt.fill(xy[:, 0], xy[:, 1])
    plt.show()

if __name__ == '__main__':
    for i in range(1, 11):
        auto_generate_urban_layout(2000, 2000, street_width = 10, export_path = f'generated_urban/random_{i}.xml', index= i)
