import os
import requests
import glob
import lxml.html as lx
import json
from soil_scripts import utils
from soil_scripts.config import DOWNLOAD_FOLDER

session = requests.Session()


def from_json(data: dict) -> list:
    zip_files: list = []
    items = data["/app-api/enduserapp/shared-folder"]["items"]
    for i in items:
        if i["type"] != "file":
            continue
        zip_files.append([i["name"], i["typedID"]])
    return zip_files


def json_with_files(pg: int) -> dict:
    headers = {
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    }
    # TODO: Before run check if this is valid path - from time time this is
    # changed on server
    list_url = 'https://nrcs.app.box.com/v/soils/folder/180112652169?page={}'

    itry = 0
    while itry < 4:
        try:
            r = session.get(list_url.format(pg))  # , headers=headers)
            itry = 7
        except Exception:
            itry += 1

    if itry == 4:
        utils.log_event('Cannot download file list from BOX', 'ERROR')
        print('BOX error')
        return dict()

    html = lx.fromstring(r.text)
    scripts = html.xpath(".//script")
    for script in scripts:
        try:
            script_text: str = script.xpath("./text()")[0].strip()
        except IndexError:
            continue
        if script_text.startswith("Box.postStreamData ="):
            return str2json(script_text)
    return dict()


def str2json(text: str) -> dict:
    text = "=".join(text.split("=")[1:]).strip().rstrip(";")
    js: dict = json.loads(text)
    return js


def download_file(fl_tab: list) -> bool:
    flname = fl_tab[0]
    flurl = fl_tab[1]

    utils.log_event(f'Start dowloading SSURGO db: {flname}')

    file_path = os.path.join(DOWNLOAD_FOLDER, flname)
    if os.path.isfile(file_path):
        utils.log_event(f'Downloaded {flname}')
        return True
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:101.0) "
        "Gecko/20100101 Firefox/101.0"
    }
    url = "https://nrcs.app.box.com/index.php" + \
        f"?rm=box_download_shared_file&vanity_name=soils&file_id={flurl}"

    with session.get(url,
                     headers=headers,
                     allow_redirects=True,
                     stream=True,) as r:
        r.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    utils.log_event(f'Downloaded {flname}')
    return True


def download_ssurgo(selected_states: [str, str] = []) -> None:
    """
    download ssurgo dbs for all or selected states
    If You need only specified states pass list with states codes
    ie ['IA', 'IL', 'ND']
    """
    pcnt = 1  # page counter
    fls = []  # list with all files

    while True:
        dwn = json_with_files(pcnt)
        pcnt += 1
        fljs = from_json(dwn)
        if len(fljs) == 0:
            break
        fls += fljs
        if pcnt > 30:
            utils.log_event('Error downloading ssurgo db list', ltype='ERROR')
            return

    to_download = []
    if len(selected_states) > 0:
        for it in fls:
            if it[0].split('_')[-1].replace('.zip', '') in selected_states:
                to_download.append(it)
    else:
        to_download = fls

    for dw in to_download:
        download_file(dw)
        try:
            download_file(dw)
        except Exception:
            utils.log_event(f'Error downloading ssurgo for state {dw[0]}',
                            ltype='ERROR')


if __name__ == '__main__':
    download_ssurgo()
