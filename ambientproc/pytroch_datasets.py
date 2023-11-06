import pickle
import shutil

import torch
import torch.utils.data as data
import torchvision.transforms as transforms
import lmdb
from PIL import Image
import numpy as np

import os
import os.path
import sys

from tqdm import tqdm

from . import render_utils


class AmbientDataConfig:

    def __init__(self, root_dir,
                 dataset_dir_appendix="dataset",
                 lmdb_dir_appendix="lmdb",
                 resolution=(1024, 1024),
                 fitting_method="RANDOM_CORP",
                 generate_data_per_sample=3,
                 lmdb_name="canonical_lmdb",
                 use_rendered_types=None,
                 use_data_types=None,
                 fetch_pairs=None):
        """
        :param root_dir:                    str, the root directory of the dataset
        :param dataset_dir_appendix:        str, the subdirectory of the dataset (where the directories of the materials are)
        :param lmdb_dir_appendix:           str, the directory of the lmdb files
        :param resolution:                  tuple, the resolution of the images, (x, y)
        :param fitting_method:              str, the method of fitting the material to the plane
                                            CHOICES: ["RANDOM_CORP", "CENTER_CROP", "RANDOM_RESIZE" , "RESIZE"]
        :param generate_data_per_sample:    int, the number of images to generate per material (Should be 1 for "CENTER_CROP" and "RESIZE")
        :param lmdb_name:                   str, the name of the lmdb file for this dataset instance
        :param use_rendered_types:          list, the types of rendered images to use
        :param use_data_types:              list, the types of data to use
                                            CHOICES : ["displacement", "roughness", "normal", "base_color", "metallic","opacity","emission", "ao"]
        """

        if fetch_pairs is None:
            fetch_pairs = [
                ("canonical_render", "displacement"),
                ("canonical_render", "roughness"),
                ("canonical_render", "normal"),
                ("canonical_render", "base_color"),
                ("canonical_render", "metallic"),
            ]

        if use_rendered_types is None:
            use_rendered_types = ["canonical_render"]

        if use_data_types is None:
            use_data_types = ["displacement", "roughness", "normal", "base_color", "metallic"]

        self.root_dir = root_dir
        self.dataset_dir = os.path.join(root_dir, dataset_dir_appendix)
        self.lmdb_dir = os.path.join(root_dir, lmdb_dir_appendix)
        self.resolution = resolution
        self.fitting_method = fitting_method
        self.generate_data_per_sample = generate_data_per_sample
        self.lmdb_name = lmdb_name
        self.use_rendered_types = use_rendered_types
        self.use_data_types = use_data_types
        self.fetch_pairs = fetch_pairs


class AmbientDataset(data.Dataset):
    def __init__(self, cfg: AmbientDataConfig, redo_lmdb=False):
        super(AmbientDataset, self).__init__()

        self.cfg = cfg
        self.LMDB_PATH = os.path.join(cfg.lmdb_dir, cfg.lmdb_name)

        if not os.path.exists(self.LMDB_PATH):
            self.make_lmdb()
        if redo_lmdb:
            # remove the lmdb file and remake it
            shutil.rmtree(self.LMDB_PATH)
            self.make_lmdb()

        self.env = lmdb.open(self.LMDB_PATH, max_readers=1, readonly=True, lock=False, readahead=False, meminit=False)

        # get the list of keys
        with self.env.begin(write=False) as txn:
            self.raw_keys = list(txn.cursor().iternext(values=False))

        print("Dataset initialized with {} samples".format(len(self.raw_keys)))

    def __len__(self):
        len(self.raw_keys) * self.cfg.generate_data_per_sample

    def __getitem__(self, index):
        key = self.raw_keys[index]
        sample = {}
        with self.env.begin(write=False) as txn:
            for pair in self.cfg.fetch_pairs:
                if pair[0] in self.cfg.use_rendered_types and pair[1] in self.cfg.use_data_types:
                       sample[pair] = self.fetch_data_pair(key, txn, pair[0], pair[1])

        return sample

    def make_lmdb(self):
        """
        lmdb structure:
        key: material name
        value: map {
            "<channel_descriptor>": "<channel_range (from, to)>",
            "<tensors>": [<processed_torch_tensors, 8 bit>],
        }
        """
        if not os.path.exists(self.cfg.lmdb_dir):
            os.mkdir(self.cfg.lmdb_dir)
        env = lmdb.open(self.LMDB_PATH, map_size=1099511627776)
        txn = env.begin(write=True)
        transformation = self.create_proc_transformation()

        counter = 0
        for material_name in tqdm(os.listdir(self.cfg.dataset_dir)):
            try:
                material_dir = os.path.join(self.cfg.dataset_dir, material_name)

                # read in all png files, and pare them with names in the AMBIENT_NAMINGS dict
                ambient_maps = {}
                modalities = os.listdir(material_dir)
                for modality in modalities:
                    if modality.endswith(".png") or modality.endswith(".PNG"):
                        for key in self.cfg.use_data_types:
                            if modality.__contains__(render_utils.AMBIENT_NAMINGS[key]):
                                ambient_maps[key] = modality

                # read in all the images and concatinate into the same torch tensor along the channel dimension,
                # in the order of the use_data_types list
                material_tensors = []
                tensor_descriptors = []

                # add the feature maps
                for key in ambient_maps:
                    # read image as 8 bit torch tensor
                    img = Image.open(os.path.join(material_dir, ambient_maps[key]))
                    img_tensor = torch.tensor(np.array(img), dtype=torch.uint8)

                    # if a tensor is 2D, add a channel dimension
                    if len(img_tensor.shape) <= 2:
                        img_tensor = img_tensor.unsqueeze(0)
                    else:
                        img_tensor = img_tensor.permute(2, 0, 1)

                    # change the key to be the number of channels in the current map
                    material_tensors.append(img_tensor)
                    tensor_descriptors.append((key, img_tensor.shape[0]))

                # add the renders
                for key in self.cfg.use_rendered_types:
                    # read image as 8 bit torch tensor
                    assert os.path.exists(os.path.join(material_dir, key + ".png")), "Render does not exist"

                    img = Image.open(os.path.join(material_dir, key + ".png"))
                    img_tensor = torch.tensor(np.array(img), dtype=torch.uint8)

                    # if a tensor is 2D, add a channel dimension
                    if len(img_tensor.shape) <= 2:
                        img_tensor = img_tensor.unsqueeze(0)
                    else:
                        img_tensor = img_tensor.permute(2, 0, 1)

                    material_tensors.append(img_tensor)
                    tensor_descriptors.append((key, img_tensor.shape[0]))

                # concatinate the images into one torch tensor
                material_tensors = torch.cat(material_tensors, dim=0)

                output_samples = []

                # run transformation on the torch tensor
                for i in range(self.cfg.generate_data_per_sample):
                    output_samples.append(transformation(material_tensors))

                material_data = {}
                # for each attribute in keys, create a channel descriptor and add it to the lmdb
                for i in range(self.cfg.generate_data_per_sample):
                    used_channels = 0
                    for desc in tensor_descriptors:
                        material_data[desc[0]] = output_samples[i][used_channels: used_channels + desc[1]].numpy()
                        used_channels += desc[1]
                    txn.put((material_name + "_" + str(i)).encode(), pickle.dumps(material_data))

                counter += 1

                if counter % 20 == 0:
                    txn.commit()
                    txn = env.begin(write=True)

            except Exception as e:
                print(e)
                print("Error in material: {}".format(material_name))
                continue

        txn.commit()
        env.close()

    def create_proc_transformation(self):
        """
        creates the transformation for generating lmdb data from cfg
        :return: generated torchvision.transforms.Compose object
        """

        if self.cfg.fitting_method == "RANDOM_CORP":
            return transforms.Compose([
                transforms.RandomCrop(self.cfg.resolution),
            ])
        elif self.cfg.fitting_method == "CENTER_CROP":
            return transforms.Compose([
                transforms.CenterCrop(self.cfg.resolution),
            ])
        elif self.cfg.fitting_method == "RANDOM_RESIZE":
            return transforms.Compose([
                transforms.RandomResizedCrop(self.cfg.resolution),
            ])
        elif self.cfg.fitting_method == "RESIZE":
            return transforms.Compose([
                transforms.Resize(self.cfg.resolution),
            ])
        else:
            raise ValueError("Invalid fitting method: " + self.cfg.fitting_method)

    def fetch_data_pair(self, key, txn, modality1, modality2):
        """
        fetches the data from the lmdb
        :param key: key to fetch
        :param txn: lmdb transaction
        :return: dictionary of data
        """
        print("reading")
        data = pickle.loads(txn.get(key))
        print("done reading")

        return data[modality1], data[modality2]

