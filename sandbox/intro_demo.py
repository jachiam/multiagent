from rllab.algos.trpo import TRPO
from rllab.algos.vpg import VPG
from rllab.baselines.linear_feature_baseline import LinearFeatureBaseline
from rllab.baselines.zero_baseline import ZeroBaseline
from rllab.envs.box2d.cartpole_env import CartpoleEnv
from rllab.envs.normalized_env import normalize
from rllab.policies.gaussian_mlp_policy import GaussianMLPPolicy
from rllab.misc.instrument import stub, run_experiment_lite
from custom_plotter import *

from sandbox.multiagent.regolith import RegolithEnv
from sandbox.multiagent.conv_policy import *

#stub(globals())

env = RegolithEnv()

policy = CategoricalConvPolicy('pilots-prayer',env.spec,(3,3),(3,3),(1,1),(2,0))

baseline = ZeroBaseline(env.spec)

algo = VPG(
    env=env,
    policy=policy,
    baseline=baseline,
    batch_size=500,
    whole_paths=True,
    max_path_length=100,
    n_itr=40,
    discount=0.99,
    #step_size=0.01,
    #plot=True,
)

algo.train()

"""
run_experiment_lite(
    algo.train(),
    n_parallel=1,
    snapshot_mode="last",
    seed=0,
    exp_prefix='please_run',
    #mode="ec2",
    plot=True,
)"""

