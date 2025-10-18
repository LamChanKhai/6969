from django.conf import settings
import requests
import zipfile

storage_url = settings.STORAGE_URL
allow_storage_file = settings.ALLOW_STORAGE_FILE

def transport_file(id, file):
    try:
        res = requests.post(
            url= storage_url + "/storage.php",
            files={
                "id":(None,id),
                "file":file
            },
            allow_redirects=False,
            timeout=2
        )
        return "OK"
    except Exception as e:
        return "ERR"


def check_file(file):
    try:
        with zipfile.ZipFile(file,"r") as zf:
            namelist = zf.namelist()
            if len([f for f in namelist if not f.endswith(allow_storage_file)]) > 0:
                return False
    except:
        return False

    return True


def health_check(module):
    try:
        res = requests.get(storage_url + module, timeout=2)
        if res.status_code == 200:
            return True
        return False
    except:
        return False