import json
import requests
from clint.textui import progress
from datetime import date
from bs4 import BeautifulSoup
import os, sys
from genericpath import exists

if sys.platform != "linux":
    exit()

URL="https://kernel.org"
WORKING_DIR= f"{os.getenv('HOME')}/.KernelManager"
TODAY = date.today()

class Kernel():
    branch: str
    version: str
    date: str
    tarball: str
    pgp: str

def check_path():
    if not exists(f"{WORKING_DIR}"):
            os.mkdir(f"{WORKING_DIR}")
    if not exists(f"{WORKING_DIR}/downloads/"):
            os.mkdir(f"{WORKING_DIR}/downloads/")
    if not exists(f"{WORKING_DIR}/cache/"):
            os.mkdir(f"{WORKING_DIR}/cache/")

def get_kernel_page_source():
    global kernels
    if not exists(f'{WORKING_DIR}/cache/temp{TODAY}'):
        print(f"Sending GET request to {URL}...")
        page = requests.get(URL)
        print("Saving file to cache...")
        file = open(f'{WORKING_DIR}/cache/temp{TODAY}', 'wb')
        file.write(page.content)
        page = page.content
    else:
        print("Reading from file...")
        file = open(f'{WORKING_DIR}/cache/temp{TODAY}', 'r')
        page = file.read()
    file.close()

    soup = BeautifulSoup(page, 'html.parser')
    release = soup.find(id="releases")
    releases_items = release.find_all("tr")
    kernels = []
    for release in releases_items:
        kernel = Kernel()
        kernel.branch = release.find_all("td")[0].get_text()
        if kernel.branch == "linux-next:":
            continue
        kernel.branch = kernel.branch.replace(":", "")
        kernel.version = release.find("strong").get_text()
        kernel.date = release.find_all("td")[2].get_text()
        if kernel.branch != "mainline" or "linux-next":
            kernel.tarball = release.find_all('a', href=True)[0]['href']
        if kernel.branch != "linux-next":
            kernel.pgp = release.find_all('a', href=True)[1]['href']
        kernels.append(kernel)
def get_json():
    list = '{"kernels":[]}'
    data = json.loads(list)
    for kernel in kernels:

        if kernel.branch != 'mainline':
            data["kernels"].append({"branch": kernel.branch, "version": kernel.version, "release_date": kernel.date, "tarball": kernel.tarball, "PGP": kernel.pgp})

        elif kernel.branch == 'mainline' or kernel.pgp == None:
            data["kernels"].append({"branch": kernel.branch, "version": kernel.version, "release_date": kernel.date, "tarball": kernel.tarball, "PGP": None})
    json.dumps(data, indent=4)
    return data

def ask_version():
    print("Available versions: ")
    json = get_json()
    data = json["kernels"]
    version_list = []
    i = 0
    for element in data:
        i += 1
        print(f"[{i}] {element['branch']} {element['version']} {element['release_date']}")
        version_list.append(element['tarball'])
    version = check_input()

    download_kernel(version_list[version-1])

def download_kernel(url: str):
    response = requests.get(url, stream=True)
    name = url.split("/")[-1]
    path= f"{WORKING_DIR}/downloads/{name}"
    with open(path, 'wb') as file:
        total_length = int(response.headers.get('content-length'))
        for chunk in progress.bar(response.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1): 
            if chunk:
                file.write(chunk)
                file.flush()
    print("download done")

def check_input() -> int:
    version = int(input("> "))
    return version

def main():
    check_path()
    get_kernel_page_source()
    ask_version()

    
if __name__ == '__main__':
    main()
