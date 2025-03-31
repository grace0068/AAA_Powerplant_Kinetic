import math
import matplotlib.pyplot as plt
import numpy as np
import os
import imageio.v2 as imageio
import random
from tqdm import tqdm

polaris_x, polaris_y = 0., 0.
sleep_x, sleep_y = -1., -1.
x_min, x_max = -500., 500.
y_min, y_max = 0., 500.
mirror_num = 40
mirror_used = [0] * mirror_num
mirror_queue = []
mirror_color = []

class point:
    
    def __init__(self, r, theta):
        self.r = r
        self.theta = theta
        self.mirror_id = -1
        self.valid = False

class astronomical_object:
    
    def __init__(self, angle, pairs):
        self.center_default = angle
        self.point_list = []
        for r, theta in pairs:
            self.point_list.append(point(r, theta))
        self.ret = {}
    
    def invalid_points(self, degree):
        self.ret = {}
        for p in self.point_list:
            x = polaris_x - p.r * math.sin(self.center_default + p.theta + degree)
            y = polaris_y + p.r * math.cos(self.center_default + p.theta + degree)
            if x <= x_min or x >= x_max or y <= y_min or y >= y_max:
                if p.valid:
                    mirror_queue.append(p.mirror_id)
                    self.ret[p.mirror_id] = (sleep_x, sleep_y)
                    p.valid = False

    def valid_points(self, degree):
        for p in self.point_list:
            x = polaris_x - p.r * math.sin(self.center_default + p.theta + degree)
            y = polaris_y + p.r * math.cos(self.center_default + p.theta + degree)
            if x <= x_min or x >= x_max or y <= y_min or y >= y_max:
                continue
            p.valid = True
            if p.mirror_id < 0:
                if len(mirror_queue) <= 0:
                    print("NO MIRROR!")
                else:
                    p.mirror_id = mirror_queue.pop(0)
            self.ret[p.mirror_id] = (x, y)
        
        return self.ret

def parse_file(file_name):
    with open(file_name, 'r') as f:
        lines = f.read().splitlines()
    
    angle = float(lines[0])
    
    pairs = []
    for line in lines[1:]:
        if line.strip():
            r, theta = map(float, line.split())
            pairs.append((r, theta))
    
    return angle, pairs

n = 3
steps = 360

diurnal_objects = []

for i in range(mirror_num):
    mirror_queue.append(i)
    mirror_color.append((random.random(), random.random(), random.random()))

for i in range(1, n + 1):
    file_name = f"objects/{i}.txt"
    angle, pairs = parse_file(file_name)
    diurnal_objects.append(astronomical_object(angle, pairs))

os.makedirs("frames", exist_ok=True)
frame_files = []

width, height = 1000, 500
radius = 5

for step in tqdm(range(steps)):
    degree = math.pi * 2 / steps * step
    data_send = {}
    for obj in diurnal_objects:
        obj.invalid_points(degree)
    for obj in diurnal_objects:
        ret = obj.valid_points(degree)
        data_send |= ret
    
    fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
    
    ax.set_xlim(-500, 500)
    ax.set_ylim(0, 500)
    ax.axis('off')
    
    for key, value in data_send.items():
        x, y = value
        if x == sleep_x and y == sleep_y:
            continue
        circle = plt.Circle((x, y), radius, color = mirror_color[key])
        ax.add_patch(circle)
    
    filename = f"frames/frame_{step:03d}.png"
    fig.savefig(filename, bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    frame_files.append(filename)

images = [imageio.imread(fname) for fname in frame_files]
imageio.mimsave('output_video.mp4', images, fps=30)

