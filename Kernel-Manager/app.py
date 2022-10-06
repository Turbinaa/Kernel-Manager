import json
import os
import sys
from datetime import date
from genericpath import exists
import requests
from bs4 import BeautifulSoup

# Check if user runs linux
if sys.platform != "linux":
    exit()

# Constants
URL = "https://kernel.org"
WORKING_DIR = f"{os.getenv('HOME')}/.KernelManager"
TODAY = date.today()


class Kernel:
    """
        Class used to store information about kernel

        Takes values:

        branch: str
        version: str
        date: str
        tarball: str
        pgp: str
    """
    branch: str
    version: str
    date: str
    tarball: str
    pgp: str


def check_path():
    """Checks if .KernelManager exists in users home directory"""
    if not exists(f"{WORKING_DIR}"):
        os.mkdir(f"{WORKING_DIR}")
    if not exists(f"{WORKING_DIR}/downloads/"):
        os.mkdir(f"{WORKING_DIR}/downloads/")
    if not exists(f"{WORKING_DIR}/cache/"):
        os.mkdir(f"{WORKING_DIR}/cache/")


def get_kernel_page_source():
    """Download and scrap webpage of the global variable URL"""

    # Check if it's necessary to download source from url
    if not exists(f'{WORKING_DIR}/cache/temp{TODAY}'):
        # Download source and write to file marked as from today
        print(f"Sending GET request to {URL}...")
        page = requests.get(URL)
        print("Saving file to cache...")
        file = open(f'{WORKING_DIR}/cache/temp{TODAY}', 'wb')
        file.write(page.content)
        page = page.content
    else:
        # Read source from existing file
        print("Reading from file...")
        file = open(f'{WORKING_DIR}/cache/temp{TODAY}', 'r')
        page = file.read()
    file.close()

    # Scrap source
    soup = BeautifulSoup(page, 'html.parser')
    release = soup.find(id="releases")
    releases_items = release.find_all("tr")
    kernels = []
    # Find all found kernel versions
    for release in releases_items:
        kernel = Kernel()
        kernel.branch = release.find_all("td")[0].get_text()
        # App doesn't support linux-next for now
        if kernel.branch == "linux-next:":
            continue

        kernel.branch = kernel.branch.replace(":", "")
        kernel.version = release.find("strong").get_text()
        kernel.date = release.find_all("td")[2].get_text()
        kernel.tarball = release.find_all('a', href=True)[0]['href']
        # Scrap pgp download url (mainline doesnt have one)
        if kernel.branch != "mainline":
            kernel.pgp = release.find_all('a', href=True)[1]['href']
        kernels.append(kernel)
    return kernels


def get_json():
    """Return JSON data from kernels found on the page"""
    kernels = get_kernel_page_source()
    # JSON format
    kernel_list = '{"kernels":[]}'
    data = json.loads(kernel_list)

    for kernel in kernels:

        if kernel.branch != 'mainline':
            data["kernels"].append({"branch": kernel.branch, "version": kernel.version, "release_date": kernel.date,
                                    "tarball": kernel.tarball, "PGP": kernel.pgp})

        elif kernel.branch == 'mainline' or kernel.pgp is None:
            data["kernels"].append({"branch": kernel.branch, "version": kernel.version, "release_date": kernel.date,
                                    "tarball": kernel.tarball, "PGP": None})
    json.dumps(data, indent=4)
    return data


def ask_version(i=0):
    print("Available versions: ")
    version_json = get_json()
    data = version_json["kernels"]
    version_list = []
    for element in data:
        i += 1
        print(f"[{i}] {element['branch']} {element['version']} {element['release_date']}")
        version_list.append(element['tarball'])
    version = check_input()

    download_kernel(version_list[version - 1])


def check_input() -> int:
    version = int(input("> "))
    return version


def download_kernel(url: str):
    # GET url
    response = requests.get(url, stream=True)
    # returns text after the last '/' in url
    name = url.split("/")[-1]
    path = f"{WORKING_DIR}/downloads/{name}"
    # Save downloaded tarball
    with open(path, 'wb') as file:
        file.write(response.content)
    print("Download done")


def main():
    check_path()
    ask_version()


if __name__ == '__main__':
    main()
