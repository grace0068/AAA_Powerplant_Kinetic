import math

rad = [3/20, 5.5/20, 9/20, 12/20, 16/20]

def parse_file(file_name):
    with open(file_name, 'r') as f:
        lines = f.read().splitlines()
    
    print(math.radians(float(lines[0])))
    pairs = []
    for line in lines[1:]:
        split = line.split()
        x, y, z = float(split[0]), float(split[1]), int(split[2])
        x = 30 - x - rad[z]
        y = 30 - y - rad[z]
        print(round(((x**2+y**2)**0.5)*10), round(math.atan(x/y)*10000)/10000, z)

pairs = parse_file("a.txt")