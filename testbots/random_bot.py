import socket
import json
import random

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("nyt.istrolid.com", 16000))
file = s.makefile(mode='rwb')

header = json.loads(file.readline().strip())

Reset = "\x1b[0m"
FgRed = "\x1b[31m"

print "header", header

while True:
    data = file.readline().strip()
    if data:
        data = json.loads(data)

        map = []
        for x in range(header["world_size"][2]):
            row = []
            for y in range(header["world_size"][1]):
                row.append(-1)
            map.append(row)

        for i, layer in enumerate(data["world"]):
            for y, row in enumerate(layer):
                for x, e in enumerate(row):
                    if e == 1:
                        map[x][y] = i

        print "\033[2J\033[1;1H"
        print "step", data["step"]
        for row in reversed(map):
            line = ""
            for e in row:
                if e == -1:
                    line += " "
                else:
                    if e >= 2:
                        line += FgRed
                    line += "#Fabc*"[e]
                    if e >= 2:
                        line += Reset
            print line
        print "-"*80

    command = {"action": random.randint(0, header['actions']-1)}

    #print command
    s.send(json.dumps(command)+"\n")
    #s.flush()
