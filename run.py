import math
import matplotlib.pyplot as plt
import numpy as np
import os
import imageio.v2 as imageio
import random
from tqdm import tqdm
import pandas as pd

polaris_x, polaris_y = 0., 0.
sleep_x, sleep_y = -1., -1.
x_min, x_max = -300., 300.
y_min, y_max = 0., 300.
mirror_num = [25, 10, 5, 5, 1]
mirror_used = [[0]*25, [0]*10, [0]*5, [0]*5, [0]*1]
mirror_queue = [[], [], [], [], []]
mirror_color = [[], [], [], [], []]
mirror_coords = [[], [], [], [], []]
mirror_info = []
mirror_use = {}
mirror_height = 0.0
light = (0, 450, 150)
mirror_center = (0, 5, 300)
meteor_p = 0.1
loop = 10
n = 3
steps = 360

class point:
    
    def __init__(self, r, theta, mirror_type):
        self.r = r
        self.theta = theta
        self.mirror_type = mirror_type
        self.mirror_id = -1
        self.valid = False

class meteor:
    
    def __init__(self, start_tick):
        self.start_tick = start_tick
        self.end_tick = min(start_tick + int(random.random()*30 + 10), steps*loop)
        start_angle = random.random() * math.pi * 2/3 + math.pi / 6
        end_angle = random.random() * math.pi * 2
        self.start_coords = (300*math.cos(start_angle), 300*math.sin(start_angle))
        self.end_coords = (300*math.cos(end_angle), 300*math.sin(end_angle))
        if end_angle > math.pi:
            x1, y1 = self.start_coords
            x2, y2 = self.end_coords
            t = -y1 / (y2 - y1)
            self.end_coords = (x1 + t * (x2 - x1), 0)
        if random.random() < 0.5:
            self.start_coords, self.end_coords = self.end_coords, self.start_coords
        self.mirror_type = -1
        self.mirror_id = -1
        init = random.randint(0, 45)
        for i in range(init, init+46):
            id = i % 46
            mirror_type, mirror_id = mirror_info[id]
            valid = True
            for j in range(self.start_tick, self.end_tick+1):
                tick = j % steps
                if mirror_use[(mirror_type, mirror_id)][tick]:
                    valid = False
                    break
            if valid:
                self.mirror_type, self.mirror_id = mirror_type, mirror_id
                for j in range(self.start_tick, self.end_tick+1):
                    tick = j % steps
                    mirror_use[(mirror_type, mirror_id)][tick] = True
                break
        if self.mirror_type < 0:
            print("???")
        

    
    def calc(self, tick):
        if tick > self.end_tick:
            return {}
        theta = math.pi * 2 / steps * (tick-self.start_tick)
        x1, y1 = self.start_coords
        x2, y2 = self.end_coords
        x = (x1 * (self.end_tick-tick) + x2 * (tick-self.start_tick)) / (self.end_tick - self.start_tick)
        y = (y1 * (self.end_tick-tick) + y2 * (tick-self.start_tick)) / (self.end_tick - self.start_tick)
        x_rot = x * math.cos(theta) - y * math.sin(theta)
        y_rot = x * math.sin(theta) + y * math.cos(theta)
        ret = {}
        ret[(self.mirror_type, self.mirror_id)] = (x_rot, y_rot)
        return ret
    
    def print(self):
        print(self.mirror_type, self.mirror_id, self.start_tick, self.end_tick, self.start_coords, self.end_coords)

class astronomical_object:
    
    def __init__(self, angle, points):
        self.center_default = angle
        self.point_list = []
        for r, theta, mirror_type in points:
            self.point_list.append(point(r, theta, mirror_type))
        self.ret = []
        for i in range(steps):
            self.ret.append({})
    
    def calc_invalid_points(self, step):
        degree = math.pi * 2 / steps * step
        for p in self.point_list:
            x = polaris_x - p.r * math.sin(self.center_default + p.theta + degree)
            y = polaris_y + p.r * math.cos(self.center_default + p.theta + degree)
            if x <= x_min or x >= x_max or y <= y_min or y >= y_max:
                if p.valid:
                    mirror_queue[p.mirror_type].append(p.mirror_id)
                    self.ret[step][(p.mirror_type, p.mirror_id)] = (sleep_x, sleep_y)
                    p.valid = False

    def calc_valid_points(self, step):
        degree = math.pi * 2 / steps * step
        for p in self.point_list:
            x = polaris_x - p.r * math.sin(self.center_default + p.theta + degree)
            y = polaris_y + p.r * math.cos(self.center_default + p.theta + degree)
            if x <= x_min or x >= x_max or y <= y_min or y >= y_max:
                continue
            p.valid = True
            if p.mirror_id < 0:
                if len(mirror_queue[p.mirror_type]) <= 0:
                    print("NO MIRROR!")
                else:
                    p.mirror_id = mirror_queue[p.mirror_type].pop(0)
            if p.mirror_id >= 0:
                self.ret[step][(p.mirror_type, p.mirror_id)] = (x, y)
                mirror_use[(p.mirror_type, p.mirror_id)][step] = True
    
    def valid_points(self, step):
        return self.ret[step%steps]


def get_normal(dest_x, dest_y, mirror_type, mirror_id):
    mirror_x, mirror_y, mirror_z = mirror_center
    light_x, light_y, light_z = light
    dx, dy = mirror_coords[mirror_type][mirror_id]
    mirror_x += dx
    mirror_y += dy
    return ((dest_x+light_x)/2-mirror_x, (dest_y+light_y)/2-mirror_y, light_z/2-mirror_z)

def parse_file(file_name):
    with open(file_name, 'r') as f:
        lines = f.read().splitlines()
    
    angle = float(lines[0])
    
    points = []
    for line in lines[1:]:
        if line.strip():
            split = line.split()
            r = float(split[0])
            theta = float(split[1])
            mirror_type = int(split[2])
            points.append((r, theta, mirror_type))
    
    return angle, points

def parse_mirror(file_name):
    with open(file_name, 'r') as f:
        lines = f.read().splitlines()
    
    ind = 0
    for i in range(len(mirror_num)):
        for j in range(mirror_num[i]):
            split = lines[ind].split()
            mirror_coords[i].append((float(split[0]), float(split[1])))
            mirror_info.append((i, j))
            mirror_use[(i, j)] = [False]*steps
            ind += 1


diurnal_objects = []
meteors = []

for i in range(len(mirror_num)):
    for j in range(mirror_num[i]):
        mirror_queue[i].append(j)
        mirror_color[i].append((random.random(), random.random(), random.random()))

for filename in sorted(os.listdir("objects")):  
    if filename.endswith(".txt"):
        file_path = os.path.join("objects", filename)
        angle, pairs = parse_file(file_path)
        diurnal_objects.append(astronomical_object(angle, pairs))

parse_mirror("mirror.txt")

os.makedirs("frames", exist_ok=True)
frame_files = []

width, height = 600, 300
radius = [3, 5.5, 9, 12, 16]

for step in range(steps):
    for obj in diurnal_objects:
        obj.calc_invalid_points(step)
    for obj in diurnal_objects:
        obj.calc_valid_points(step)

for step in tqdm(range(steps*loop)):
    data_send = {}
    for obj in diurnal_objects:
        ret = obj.valid_points(step)
        data_send |= ret
    if random.random() < 0.05 and step < steps*loop - 10:
        meteors.append(meteor(step))
    for obj in meteors:
        ret = obj.calc(step)
        data_send |= ret
    
    fig, ax = plt.subplots(figsize=(width/50, height/50), dpi=100)
    
    ax.set_xlim(-300, 300)
    ax.set_ylim(0, 300)
    ax.axis('off')
    
    data_normal = {}
    for key, value in data_send.items():
        mirror_type, mirror_id = key
        x, y = value
        data_normal[(mirror_type, mirror_id)] = get_normal(x, y, mirror_type, mirror_id)
    
    df_send = pd.DataFrame([
        {
            'mirror_type': k[0],
            'mirror_id': k[1],
            'x': v[0],
            'y': v[1]
        } for k, v in data_send.items()
    ])
    df_send.to_csv(f"outputs/coords_{step}.csv", index=False)

    df_normal = pd.DataFrame([
        {
            'mirror_type': k[0],
            'mirror_id': k[1],
            'normal_x': v[0],
            'normal_y': v[1]
        } for k, v in data_normal.items()
    ])
    df_normal.to_csv(f"outputs/normal_{step}.csv", index=False)
    
    for key, value in data_send.items():
        mirror_type, mirror_id = key
        x, y = value
        if x == sleep_x and y == sleep_y:
            continue
        circle = plt.Circle((x, y), radius[mirror_type]/2, color = mirror_color[mirror_type][mirror_id])
        ax.add_patch(circle)
    
    polaris = plt.Circle((0, 0), radius[0], color = (0, 0, 0))
    ax.add_patch(polaris)
    
    filename = f"frames/frame_{step:03d}.png"
    fig.savefig(filename, bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    frame_files.append(filename)

images = [imageio.imread(fname) for fname in frame_files]
imageio.mimsave('output_video.mp4', images, fps=15)

