from ambientproc import *
import numpy as np

cfg = load_config()
cfg_d = AmbientDataConfig(cfg)
dataset = AmbientDataset(cfg_d)
sample = dataset.__getitem__(0)