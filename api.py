import requests, json
def bigdata(servers):
    params={"bigdata":str(servers)}
    response=requests.post("https://n1ce.me/hw/api/bigdata", data=params)
    return response.text

def update_main(targets):
    params = {"list": ",".join(targets)}
    response=requests.post("https://n1ce.me/hw/api/main", data=params)
    return response.text

def send_new(servers, i):
     for j in servers[i][1]:
         print(f"{i} to {j}")
         print(requests.post("https://n1ce.me/hw/api/connect",
                             data={"from": i, "to": j}).text)
def do_connects(servers):
    for i in servers.keys():
        send_new(servers, i)

def get_data():
    response=requests.get("https://n1ce.me/hw/api/data")
    return response.json()

def add(servers:list):
    response=requests.post("https://n1ce.me/hw/api/add", data={"ids":servers})
    return response.text

def delete_data(vk):
    vk.messages.send(peer_id=298149825, message="Данные с сайта удалены", random_id=0)
    response = requests.delete("https://n1ce.me/hw/api/clear")
    return response.text
    pass

def drop(vk):
    vk.messages.send(peer_id=298149825, message="Данные с сайта удалены полностью", random_id=0)
    response = requests.delete("https://n1ce.me/hw/api/drop")
    return response.text
    pass
