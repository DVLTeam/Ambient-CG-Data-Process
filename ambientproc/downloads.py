import urllib.request
import json
import time
import os

# request header
CSV_HEAD = "https://ambientCG.com/api/v2/downloads_csv?type=Material"


# get csv file header
def get_download_csv(save_path="./materials.csv"):
    # get csv file
    req = urllib.request.Request(CSV_HEAD)
    with urllib.request.urlopen(req) as res:
        body = res.read()
        with open(save_path, mode='wb') as f:
            f.write(body)


# download materials
def download_materials(input_file="materials.csv", output_dir="./cache",
                       downloaded_files_cache="./downloaded_files.txt"):
    os.makedirs(output_dir, exist_ok=True)
    sf = open(downloaded_files_cache, mode='a')
    tf = open(downloaded_files_cache, mode='r')
    downloaded_files = [s.strip() for s in tf.readlines()]
    print("downloaded:", downloaded_files)
    tf.close()
    with open(input_file, mode='r') as f:
        lines = f.readlines()
        lines_4k_png = []
        for line in lines:
            if line.__contains__("4K-PNG"):
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

                with urllib.request.urlopen(req) as response, open(output_dir + "/" + name + ".zip", 'wb') as out_file:
                    data = response.read()  # a `bytes` object
                    out_file.write(data)
                sf.write(name + "\n")
                time.sleep(1)


# unzip downloaded files
def unzip_datasets(download_dir="./cache", unzip_dir="./cache"):
    import zipfile
    import os
    import shutil
    os.makedirs(unzip_dir, exist_ok=True)
    for file in os.listdir(download_dir):
        if file.endswith(".zip"):
            print("unzipping: " + file)
            with zipfile.ZipFile(download_dir + "/" + file, 'r') as zip_ref:
                zip_ref.extractall(unzip_dir + "/" + file.split(".")[0])
