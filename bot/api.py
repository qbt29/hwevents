from settings import sb_header as header
import requests, json
import warnings
import contextlib
from urllib3.exceptions import InsecureRequestWarning

old_merge_environment_settings = requests.Session.merge_environment_settings

@contextlib.contextmanager
def no_ssl_verification():
    opened_adapters = set()

    def merge_environment_settings(self, url, proxies, stream, verify, cert):
        # Verification happens only once per connection so we need to close
        # all the opened adapters once we're done. Otherwise, the effects of
        # verify=False persist beyond the end of this context manager.
        opened_adapters.add(self.get_adapter(url))

        settings = old_merge_environment_settings(self, url, proxies, stream, verify, cert)
        settings['verify'] = False

        return settings

    requests.Session.merge_environment_settings = merge_environment_settings

    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', InsecureRequestWarning)
            yield
    finally:
        requests.Session.merge_environment_settings = old_merge_environment_settings

        for adapter in opened_adapters:
            try:
                adapter.close()
            except:
                pass
def bigdata(servers):
    params={"bigdata":str(servers)}
    with no_ssl_verification():
        response=requests.post("https://n1ce.me/hw/api/bigdata", data=params)
    return response.text

def update_main(targets):
    with no_ssl_verification():
        response=requests.post("https://n1ce.me/hw/api/main", data={targets[i]:i for i in targets})
    return response.text

def send_files(server, files):
    with no_ssl_verification():
        response=requests.post("https://n1ce.me/hw/api/main", data={"server":server, "files":files})
    return response.text

def send_new(servers, i):
    if len(servers[i][1])>0:
        with no_ssl_verification():
            data = {'from': i, 'to': servers[i][1]}
            requests.get("https://api.statbot.info/api/v1/event/add-server", headers=header, params=data)
    for j in servers[i][1]:
         with no_ssl_verification():
            print(requests.post("https://n1ce.me/hw/api/connect",
                             data={"from": i, "to": j}).text)
def do_connects(servers):
    for i in servers.keys():
        send_new(servers, i)

def get_data():
    with no_ssl_verification():
        response=requests.get("https://n1ce.me/hw/api/data")
    return response.json()

def add(servers:list):
    with no_ssl_verification():
        response=requests.post("https://n1ce.me/hw/api/add", data={"ids":servers})
    return response.text

def delete_data(vk):
    vk.messages.send(peer_id=298149825, message="Данные с сайта удалены", random_id=0)
    with no_ssl_verification():
        response = requests.delete("https://n1ce.me/hw/api/clear")
    return response.text
    pass

def drop(vk):
    vk.messages.send(peer_id=298149825, message="Данные с сайта удалены полностью", random_id=0)
    with no_ssl_verification():
        response = requests.delete("https://n1ce.me/hw/api/drop")
    return response.text
    pass

def get_from_sb():
    with no_ssl_verification():
        response=json.loads(requests.get("https://api.statbot.info/api/v1/event/server-map").text)
    return response['data'] if not response['error'] else []