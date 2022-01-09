import requests, threading

def update_data(servers):
    params={"bigdata":str(servers)}
    response=requests.post("https://n1ce.me/hw/api/bigdata", data=params)
    return response.text

def update_main(targets):
    params = {"list": ",".join(targets)}
    response=requests.post("https://n1ce.me/hw/api/main", data=params)
    return response.text

def send_new(servers, i):
     for j in servers[i][1]:
         print(requests.post("https://n1ce.me/hw/api/connect",
                             data={"from": i, "to": j}).text)
def do_connects(servers):
    for i in servers.keys():
        send_new(servers, i)

def get_data():
    response=requests.get("https://n1ce.me/hw/api/data")
    return response.text

def add(servers:list):
    response=requests.post("https://n1ce.me/hw/api/add", data={"ids":servers})
    return response.text

def delete_data():
    response = requests.delete("https://n1ce.me/hw/api/clear")
    return response.text

def drop():
    response = requests.delete("https://n1ce.me/hw/api/drop")
    return response.text

