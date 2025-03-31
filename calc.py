import math

def parse_file(file_name):
    with open(file_name, 'r') as f:
        lines = f.read().splitlines()
    
    pairs = []
    for line in lines[0:]:
        x, y = map(float, line.split())
        print(round(((x**2+y**2)**0.5)*50), round(math.atan(y/x)*10000)/10000)

pairs = parse_file("a.txt")