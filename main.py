from ambientproc import *
import numpy as np

cfg = load_config()
cfg_d = AmbientDataConfig(cfg["root_dir"])
dataset = AmbientDataset(cfg_d)
