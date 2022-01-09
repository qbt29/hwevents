import vk_api, threading, re, api, os
from vk_api.bot_longpoll import *
from settings import *
from collections import deque
vk = vk_api.VkApi(token=token)
longpoll = VkBotLongPoll(vk, bot_id)
vk._auth_token()
vk = vk.get_api()

global servers, targets

try:
    with open("servers.py", "r") as read:
        servers=eval(read.readline())
        if servers=="": servers={'9184A500': (0, ['9184A501', '9184A502', '9184A503'])}
        try:
            targets=eval(read.readline())
            if targets=="": targets=[]
        except:
            targets=[]
except:
    servers={'9184A500': (0, ['9184A501', '9184A502', '9184A503'])}

print(vk.storage.get(key="key", user_id=298149825))
try:
    longpoll.ts=int(vk.storage.get(key="key", user_id=298149825))
except:
    longpoll.ts=None

def find_short_way(start,goal):
    global servers
    if start not in servers: start=header+start
    if goal not in servers: goal=header+goal
    queue = deque([start])
    visited = {start: None}

    while queue:
        cur_node = queue.popleft()
        if cur_node == goal:
            break
        if cur_node in servers:
            next_nodes = servers[cur_node][1]
            for next_node in next_nodes:
                if next_node not in visited:
                    queue.append(next_node)
                    visited[next_node] = cur_node
    try:
        short_way = goal
        cur_node = goal
        steps=0
        while cur_node != start:
            short_way = visited[cur_node] + "--->" + short_way
            cur_node = visited[cur_node]
            steps+=1
        return f"Cost: {steps}&#9889;\nShort way: " + short_way
    except:
        return "No way"

def get_known(lst):
    global servers
    text=""
    for i in lst:
        text+=str(i)
        if i in servers:
            text+="&#9989;\n"
        else:
            text+="&#10060;\n"
    return text

def get_ends():
    global servers
    ends=[]
    for i in servers:
        if servers[i][1]==[]:
            ends.append(i)
    return ends

def update():
    global servers, targets
    print(api.update_main(targets))
    api.do_connects(servers.copy())

def request(msg):
    global servers, targets
    def write_file():
        with open("servers.py", "w") as f:
            f.write(str(servers))
            f.write('\n' + str(targets))
    unique=0
    for message in msg['fwd_messages']:
        text,from_id,date=message['text'],message['from_id'],message['date']
        if from_id!=-172959149:
            continue
        find=re.findall(r'[A-Z0-9]{8}', text)
        if len(find) == 4:
            server, *ways=find
            if server in servers:
                if date<=servers[server][0] or servers[server][1]==ways:
                    continue
            servers[server]=date, ways
            unique+=1
            for i in ways:
                if i not in servers:
                    unique+=1
                    servers[i]=(0, [])
            api.send_new(servers, server)
            write_file()
        elif len(find)==16:
            targets=find.copy()
            api.update_main(targets)
            write_file()
    if unique:
        vk.messages.send(peer_id=msg['peer_id'], message=f"Получено уникальных серверов: {unique}", random_id=0)
    lst = msg['text'].split()
    if len(lst)==0: return
    if lst[0]=='/w' and len(lst)==3:
            vk.messages.send(peer_id=msg['peer_id'], message=find_short_way(lst[1].upper(),lst[2].upper()), random_id=0)
    elif lst[0]=='/t' and len(lst)==2:
        start=lst[1].upper()
        if start not in servers and header+start not in servers:
            vk.messages.send(peer_id=msg['peer_id'], message='No way', random_id=0)
            return
        if targets==[]:
            vk.messages.send(peer_id=msg['peer_id'], message='No data', random_id=0)
            return
        text=""
        if start not in servers: start=header+start
        for i in targets:
            text+='- '*5+i+' -'*5+'\n'+find_short_way(start, i)+'\n\n'
        vk.messages.send(peer_id=msg['peer_id'], message=text, random_id=0)
    elif lst[0]=='/k':
        vk.messages.send(peer_id=msg['peer_id'], message=get_known(targets), random_id=0)
    elif lst[0]=='/e':
        ends=get_ends()
        vk.messages.send(peer_id=msg['peer_id'], message=f"Total: {len(ends)}\n"+"\n".join(ends)+'\n'+'----------------', random_id=0)
    elif lst[0]=='/info' and len(lst)==2:
        if lst[1] not in servers and header + lst[1] not in servers: return
        if lst[1] not in servers: lst[1] = header + lst[1]
        vk.messages.send(peer_id=msg['peer_id'], message=f"Connects {lst[1]}:\n"+ '\n'.join(servers[lst[1]][1]), random_id=0)
    elif lst[0]=='/we' and len(lst)==2:
        start=lst[1].upper()
        if start not in servers and header+start not in servers: return
        if start not in servers: start=header+start
        ends=get_ends()
        text=""
        for i in ends:
            if len(text)>=3000:
                vk.messages.send(peer_id=msg['peer_id'], message=text, random_id=0)
                text=""
            text += '- ' * 5 + i + ' -' * 5 + '\n' + find_short_way(start, i) + '\n\n'
        vk.messages.send(peer_id=msg['peer_id'], message=text, random_id=0)
    elif lst[0]=='/help':
        vk.messages.send(peer_id=msg['peer_id'], message=helps, random_id=0)
    elif lst[0].lower()=='/reset' and msg['from_id'] in [211586351, 298149825, 120358503, 195575331]:
        servers={'9184A500': (0, ['9184A501', '9184A502', '9184A503'])}
        targets=[]
        api.delete_data()
        api.do_connects(servers)
        vk.messages.send(peer_id=msg['peer_id'], message='Все сервера удалены', random_id=0)
    elif lst[0]=="/update" and msg['from_id'] in [211586351, 298149825, 120358503]:
        threading.Thread(target=update).start()
        vk.messages.send(peer_id=msg['peer_id'], message='Обновление запущено', random_id=0)
    elif lst[0].lower()=='/servers' and msg['from_id'] in [211586351, 298149825, 120358503,195575331]:
        keys=list(servers.keys())
        vk.messages.send(peer_id=msg['peer_id'], message=f'Total: {len(keys)}\n {" ".join(keys)}', random_id=0)
def chat_reqs(reqs):
    i=0
    while i<len(reqs):
        threading.Thread(target=request(reqs[i].obj['message'])).start()
        i+=1

def main():
    reqs={}
    while True:
        try:
            for event in longpoll.check():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    if event.obj['message']['peer_id'] not in reqs:
                        reqs[event.obj['message']['peer_id']]=[event]
                    else:
                        reqs[event.obj['message']['peer_id']].append(event)
            for i in reqs.keys():
                threading.Thread(target=chat_reqs(reqs[i].copy())).start()
            reqs={}
            vk.storage.set(user_id=298149825, key="key", value=str(longpoll.ts))
        except Exception as e:
            print("Error:", e)
main()

