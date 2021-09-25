from os.path import exists as file_exists

import requests


def download_extension(layout_dir, extension_uuid, shell_version):
    try:
        if not file_exists(f"{layout_dir}/extensions/{extension_uuid}"):
            download_url = get_download_link(extension_uuid, shell_version)

            r = requests.get(download_url, allow_redirects=True)

            with open(f"{layout_dir}/extensions/{extension_uuid}", "wb") as f:
                f.write(r.content)

            # print(f"{extension_uuid} downloaded")
        return True

    except IndexError:
        # print(f"{extension_uuid} not found")
        return None
    except KeyError:
        # print("{extension_uuid} download link not found")
        return None


def get_download_link(extension_uuid, shell_version):
    r = requests.get(
        f"https://extensions.gnome.org/extension-query/?shell_version=all&search={extension_uuid}"
    )
    ext_id = r.json()["extensions"][0]["pk"]

    r = requests.get(
        f"https://extensions.gnome.org/extension-info/?pk={ext_id}&shell_version={shell_version}"
    )

    download_url = "https://extensions.gnome.org" + r.json()["download_url"]

    return download_url
