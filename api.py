import requests, threading

def update_data(servers):
    requests.get("https://vk.com")
    params={"bigdata":str(servers)}
    requests.post("https://n1ce.me/hw/api/bigdata", data=params)

def update_main(targets):
    params = {"list": ",".join(targets)}
    requests.post("https://n1ce.me/hw/api/main", data=params)

def send_new(servers, i):
     for j in servers[i][1]:
        requests.post("https://n1ce.me/hw/api/connect:443",
                                    data={"from": i, "to": j})
def do_connects(servers):
    for i in servers.keys():
        threading.Thread(target=send_new, args=(servers,i,)).start()

def delete_data():
    response = requests.delete("https://n1ce.me/hw/api/clear")

def get_data():
    response=requests.get("https://n1ce.me/hw/api/data")
