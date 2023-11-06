from setuptools import setup, find_packages

setup(
    name='ambientCGproc',
    version='0.1.0',
    author='Dylan Sun',
    author_email='dylansun@usc.edu',
    packages=find_packages(),
    install_requires=["numpy","torch>=2.0","torchvision","bpy>=3.6.0","lmdb","tqdm","pillow"],  # List your package's dependencies here
)