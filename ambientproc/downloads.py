import urllib.request
import json
import time
import os
import zipfile

# get csv file header
def get_download_csv(cfg):
    # get csv file
    os.makedirs(cfg["root_dir"], exist_ok=True)
    req = urllib.request.Request(cfg["header_url"])
    csv_cache = os.path.join(cfg["root_dir"],cfg["csv_cache"])
    with urllib.request.urlopen(req) as res:
        body = res.read()
        with open(csv_cache, mode='wb') as f:
            f.write(body)


# download materials
def download_materials(cfg):
    cache_dir = os.path.join(cfg["root_dir"],cfg["cache_dir"])
    os.makedirs(cache_dir, exist_ok=True)

    download_history_cache = os.path.join(cfg["root_dir"],cfg["download_history_cache"])
    csv_cache = os.path.join(cfg["root_dir"],cfg["csv_cache"])

    sf = open(download_history_cache, mode='a')
    tf = open(download_history_cache, mode='r')
    downloaded_files = [s.strip() for s in tf.readlines()]
    print("downloaded:", downloaded_files)
    tf.close()
    with open(csv_cache, mode='r') as f:
        lines = f.readlines()
        lines_4k_png = []
        for line in lines:
            if line.__contains__(cfg["download_format"]):
                lines_4k_png.append(line)

        for line in lines_4k_png:
            if line.split(",")[0] in downloaded_files:
                continue
            else:
                url = line.split(",")[5]
                name = line.split(",")[0]
                print("downloading: " + url)
                headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0'}
                req = urllib.request.Request(url, headers=headers)

                with urllib.request.urlopen(req) as response, open(os.path.join(cache_dir, name + ".zip"), 'wb') as out_file:
                    data = response.read()  # a `bytes` object
                    out_file.write(data)
                sf.write(name + "\n")
                time.sleep(1)


# unzip downloaded files
def unzip_datasets(cfg):
    dataset_dir = os.path.join(cfg["root_dir"],cfg["dataset_dir"])
    cache_dir = os.path.join(cfg["root_dir"],cfg["cache_dir"])
    os.makedirs(dataset_dir, exist_ok=True)

    for file in os.listdir(cache_dir):
        if file.endswith(".zip"):
            print("unzipping: " + file)
            with zipfile.ZipFile(os.path.join(cache_dir, file), 'r') as zip_ref:
                zip_ref.extractall(os.path.join(dataset_dir, file.split(".")[0]))


def reset_download_history(cfg):
    download_history_cache = os.path.join(cfg["root_dir"],cfg["download_history_cache"])
    tf = open(download_history_cache, mode='w')
    tf.close()

def download(cfg):
    get_download_csv(cfg)
    download_materials(cfg)
    unzip_datasets(cfg)