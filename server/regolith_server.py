#!/usr/bin/env python
from __future__ import print_function
from gevent import monkey
monkey.patch_all()
from gevent.server import StreamServer
import gevent
import random
import json


class Rock:
    def mark(self, layer):
        return layer == 0

    def symbol(self):
        return "#"

    def update(self, x, y):
        pass

class Food:
    def mark(self, layer):
        return layer == 1

    def symbol(self):
        return "F"

    def update(self, x, y):
        pass

class Agent:
    def __init__(self):
        self.action = None
        self.socket = None
        self.reward = 0
        self.dead = False
        self.signal = 0

    def send(self, msg):
        try:
            self.socket.write(json.dumps(msg) + "\n")
            self.socket.flush()
        except IOError, e:
            self.dead = True
            print("error", e)

    def mark(self, layer):
        if layer == 2:
            return True
        if layer == 3 and self.signal == 0:
            return True
        if layer == 4 and self.signal == 1:
            return True
        if layer == 5 and self.signal == 2:
            return True
        return False

    def symbol(self):
        return "abc"[self.signal]

    def update(self, x, y):

        if self.dead:
            world[x][y] = 0
            return

        self.reward = 0

        for dir in [(-1,0),(1,0),(-1,1),(1,1),(0,1),(0,-1)]:
            xd = x + dir[0]
            yd = y + dir[1]
            if xd >=0 and xd < W and yd >= 0 and yd < H :
                if isinstance(world[xd][yd], Food):
                    world[xd][yd] = 0
                    self.reward += 1

        if self.action == 1: # move left
            if x+1 < W and world[x+1][y] == 0: # normal left
                world[x+1][y] = world[x][y]
                world[x][y] = 0
            elif x+1 < W and y+1 < H and world[x+1][y+1] == 0: # climb left
                world[x+1][y+1] = world[x][y]
                world[x][y] = 0

        if self.action == 2: # move right
            if x > 0 and world[x-1][y] == 0: # normal right
                world[x-1][y] = world[x][y]
                world[x][y] = 0
            elif x > 0 and y+1 < H and world[x-1][y+1] == 0: # climb right
                world[x-1][y+1] = world[x][y]
                world[x][y] = 0

        if self.action == 3:
            self.signal = 0
        if self.action == 4:
            self.signal = 1
        if self.action == 5:
            self.signal = 2

        self.action = None

W = 80
H = 3
L = 5
world = []
for x in range(W):
    row = []
    for y in range(H):
        row.append(0)
    world.append(row)

for b in range(22):
    x = random.randint(0, W-1)
    for y in range(0,H-1):
        #print(x, y)
        if world[x][y] == 0:
            world[x][y] = Rock()
            break

def world_print():
    for y in reversed(range(H)):
        s = ""
        for x in range(W):
            thing = world[x][y]
            if thing:
                s += thing.symbol()
            else:
                s += " "
        print(s)
    print("-"*80)


agents = []

def handle(socket, address):
    print('New agent from %s:%s' % address)
    socket.settimeout(5)

    # using a makefile because we want to use readline()
    agent = Agent()
    agent.address = address
    agent.socket = socket.makefile(mode='rwb')

    agent.send({
        'world_size': [L+1, 10, H],
        'actions': 6
    })

    agents.append(agent)

    while True:
        x = random.randint(0, W-1)
        y = H-1
        if world[x][y] == 0:
            world[x][y] = agent
            break

    try:
        while True:
            line = agent.socket.readline()
            #print("%s action %s" % (address, line))

            if not line:
                break
            elif line.strip() == "r":
                agent.action = 1
            elif line.strip() == "l":
                agent.action = 2
            elif line.strip() == "a":
                agent.action = 3
            elif line.strip() == "b":
                agent.action = 4
            elif line.strip() == "c":
                agent.action = 5
            else:
                command = json.loads(line.strip())
                agent.action = command['action']

    except Exception, e:
        print("error", e)

    print("agent disconnected", address)
    agents.remove(agent)
    agent.dead = True
    agent.socket.close()

def tick():
    step = 0

    while True:
        print("\033[2J\033[1;1H")
        print("tick players:%i step:%i" % (len(agents),step))
        world_print()

        if random.random() > .2:
            x = random.randint(0, W-1)
            y = H-1
            if world[x][y] == 0:
                world[x][y] = Food()

        # simulation EVEYRTHING
        for y in reversed(range(H)):
            for x in range(W):
                if world[x][y] != 0 and y > 0 and world[x][y-1] == 0:
                    world[x][y-1] = world[x][y]
                    world[x][y] = 0

                if world[x][y]:
                    world[x][y].update(x, y)

        for agent in agents:

            myx = 0
            myy = 0
            for y in range(H):
                for x in range(W):
                    if world[x][y] == agent:
                       myx = x
                       myy = y

            layers = []
            for l in range(L):
                layer = []
                for x in range(myx-5,myx+5):
                    row = []
                    for y in range(H):
                        if x >= W or x < 0:
                            if l == 0:
                                row.append(1)
                            else:
                                row.append(0)
                        else:
                            thing = world[x][y]
                            if thing and thing.mark(l):
                                row.append(1)
                            else:
                                row.append(0)
                    layer.append(row)
                layers.append(layer)

            # self layer
            layer = []
            for x in range(myx-5,myx+5):
                row = []
                for y in range(H):
                    if x >= W or x < 0:
                        row.append(0)
                    else:
                        thing = world[x][y]
                        if thing and thing == agent:
                            row.append(1)
                        else:
                            row.append(0)
                layer.append(row)
            layers.append(layer)

            state = {
                'world': layers,
                'reward': agent.reward,
                'step': step,
                'done': False
            }
            agent.send(state)

        step += 1
        gevent.sleep(.1)

if __name__ == '__main__':
    server = StreamServer(('0.0.0.0', 16000), handle)
    print('Starting game server on port 16000')
    gevent.spawn(tick)
    server.serve_forever()
