import math
import matplotlib.pyplot as plt
import numpy as np
import os
import imageio.v2 as imageio
import random
from tqdm import tqdm

polaris_x, polaris_y = 0., 0.
sleep_x, sleep_y = -1., -1.
x_min, x_max = -300., 300.
y_min, y_max = 0., 300.
mirror_num = [25, 10, 5, 5, 1]
mirror_used = [[0]*25, [0]*10, [0]*5, [0]*5, [0]*1]
mirror_queue = [[], [], [], [], []]
mirror_color = [[], [], [], [], []]
mirror_coords = [[], [], [], [], []]
mirror_height = 0.0
light = (0, 450, 150)
mirror_center = (0, 5, 300)

class point:
    
    def __init__(self, r, theta, mirror_type):
        self.r = r
        self.theta = theta
        self.mirror_type = mirror_type
        self.mirror_id = -1
        self.valid = False

class astronomical_object:
    
    def __init__(self, angle, points):
        self.center_default = angle
        self.point_list = []
        for r, theta, mirror_type in points:
            self.point_list.append(point(r, theta, mirror_type))
        self.ret = {}
    
    def invalid_points(self, degree):
        self.ret = {}
        for p in self.point_list:
            x = polaris_x - p.r * math.sin(self.center_default + p.theta + degree)
            y = polaris_y + p.r * math.cos(self.center_default + p.theta + degree)
            if x <= x_min or x >= x_max or y <= y_min or y >= y_max:
                if p.valid:
                    mirror_queue[p.mirror_type].append(p.mirror_id)
                    self.ret[(p.mirror_type, p.mirror_id)] = (sleep_x, sleep_y)
                    p.valid = False

    def valid_points(self, degree):
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
                self.ret[(p.mirror_type, p.mirror_id)] = (x, y)
        
        return self.ret

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
            ind += 1

n = 3
steps = 360

diurnal_objects = []

for i in range(len(mirror_num)):
    for j in range(mirror_num[i]):
        mirror_queue[i].append(j)
        mirror_color[i].append((random.random(), random.random(), random.random()))

for i in range(1, n + 1):
    file_name = f"objects/{i}.txt"
    angle, pairs = parse_file(file_name)
    diurnal_objects.append(astronomical_object(angle, pairs))

parse_mirror("mirror.txt")

os.makedirs("frames", exist_ok=True)
frame_files = []

width, height = 600, 300
radius = [3, 5.5, 9, 12, 16]

for step in tqdm(range(steps)):
    degree = math.pi * 2 / steps * step
    data_send = {}
    for obj in diurnal_objects:
        obj.invalid_points(degree)
    for obj in diurnal_objects:
        ret = obj.valid_points(degree)
        data_send |= ret
    
    fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
    
    ax.set_xlim(-300, 300)
    ax.set_ylim(0, 300)
    ax.axis('off')
    
    data_normal = {}
    for key, value in data_send.items():
        mirror_type, mirror_id = key
        x, y = value
        data_normal[(mirror_type, mirror_id)] = get_normal(x, y, mirror_type, mirror_id)
    
    for key, value in data_send.items():
        mirror_type, mirror_id = key
        x, y = value
        if x == sleep_x and y == sleep_y:
            continue
        circle = plt.Circle((x, y), radius[mirror_type]/2, color = mirror_color[mirror_type][mirror_id])
        ax.add_patch(circle)
    
    filename = f"frames/frame_{step:03d}.png"
    fig.savefig(filename, bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    frame_files.append(filename)

images = [imageio.imread(fname) for fname in frame_files]
imageio.mimsave('output_video.mp4', images, fps=30)

