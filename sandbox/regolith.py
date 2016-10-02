import numpy as np
from rllab.envs.base import Env, Step
from rllab.spaces.discrete import Discrete
from rllab.spaces.box import Box
from rllab.core.serializable import Serializable
from rllab.misc.overrides import overrides

import socket
import json
import random
import sys

width = 10

class RegolithEnv(Env, Serializable):
    def __init__(self, verbose=False):
        Serializable.quick_init(self, locals())
        self.verbose = verbose
        self.obs_size = [6,width,3]
        self.actions = 6

    @property
    @overrides
    def action_space(self):
        return Discrete(self.actions)

    @property
    @overrides
    def observation_space(self):
        return Box(0,1,self.obs_size)

    def reset(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(("nyt.istrolid.com", 16000))
        self.file = self.s.makefile(mode='rwb')
        self.header = json.loads(self.file.readline().strip())
        print("header: " + str(self.header))
        self.world = self.empty_world()
        self.get_obs_from_world()
        step = self.step_from_world()
        return step[0]

    def empty_world(self):
        return {u'world':self.observation_space.low.copy(), u'step':0, u'reward':0, u'done':False}

    def world_is_empty(self):
        return self.world['step']==0

    def get_obs_from_world(self):
        if self.world_is_empty():
            while self.world_is_empty():
                self.world, no_error = self.ask_world_for_obs()
        else:
            old_step = self.world['step']
            while self.world['step'] == old_step:
                self.world, no_error = self.ask_world_for_obs()
        if not(no_error):
            self.reset()

    def ask_world_for_obs(self):
        try:
            data = self.file.readline().strip()
            if data:
                world = json.loads(data)
                return world, True
            return self.world, True
        except IOError:
            return self.world, False

    def step(self, action):
        command = {"action" : action}
        if self.verbose:
            print(command)
        
        self.s.send(json.dumps(command)+"\n")

        self.get_obs_from_world()

        return self.step_from_world()

    def step_from_world(self):
        next_obs = np.array(self.world['world'],dtype=np.float32)
        reward   = self.world['reward']
        done     = self.world['done']

        print ".",
        sys.stdout.flush()

        next_obs = next_obs.swapaxes(0,1)
        next_obs = next_obs.reshape(width,18)

        return Step(next_obs, reward, done)

    def terminate(self):
        self.s.close()



