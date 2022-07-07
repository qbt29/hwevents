import vk_api, threading, re, api
from vk_api.bot_longpoll import *
from settings import *
from collections import deque
from time import time
vk = vk_api.VkApi(token=token)
longpoll = VkBotLongPoll(vk, bot_id)
vk._auth_token()
vk = vk.get_api()

global servers, targets

try:
    with open("servers.py", "r") as read:
        servers=eval(read.readline())
        if servers=="": servers={'01F8A001': (0, ['01F8A000', '01F8A002', '01F8A003'])}
        try:
            targets=eval(read.readline())
            if targets=="": targets=[]
        except:
            targets=[]
except:
    servers={'01F8A000': (0, ['01F8A001', '01F8A002', '01F8A003'])}

print(vk.storage.get(key="key", user_id=298149825))
try:
    longpoll.ts=int(vk.storage.get(key="key", user_id=298149825))
except:
    longpoll.ts=None

def send_long(peer_id, message,random_id=0):
    text=""
    for i in message:
        text += i
        if len(text) >= 4000:
            vk.messages.send(peer_id=peer_id, message=text, random_id=0)
            text = ""
    if text!="":
        vk.messages.send(peer_id=peer_id, message=text, random_id=0)

def find_short_way(start,goal):
    global servers
    if start not in servers and header+start in servers: start=header+start
    if goal not in servers and header+goal in servers: goal=header+goal
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
        return f"Cost: {steps}⚡\nShort way: " + short_way
    except:
        return f"No way from {start} to {goal}"

def dfs(server, unreached, visited):
    global servers
    for i in servers[server][1]:
        if i not in visited:
            print(i, visited, unreached)
            visited.append(i)
            unreached.remove(i)
            unreached,visited = dfs(i,unreached, visited)
    return unreached, visited

def get_known(lst):
    global servers
    text=""
    cnt=0
    for i in lst:
        text+=str(i)
        if i in servers:
            text+="&#9989;\n"
            cnt+=1
        else:
            text+="&#10060;\n"
    text+=f"Найдено {cnt}/{len(lst)}"
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
def write_file():
    with open("servers.py", "w") as f:
        f.write(str(servers))
        f.write('\n' + str(targets))
def fix(peer):
    global servers, targets
    fix_mode=0
    send_long(peer_id=peer, message='Исправление начато', random_id=0)
    changes=[]
    start=time()
    for i in servers.copy().keys():
        if i[:6]!=header:
            changes+=[[i, 'Not a server']]
            fix_mode=1
            del servers[i]
        elif int(servers[i][0])<int(servers['01F8A000'][0]):
            changes+=[[i, f'Sent before reset: {servers[i][0]}<{servers["9184A500"][0]}']]
            del servers[i]
    for i in targets:
        if i[:6]!=header:
            changes+=[[i, 'Not a server']]
            fix_mode=1
            targets.remove(i)
    if len(changes):
        if fix_mode:
            api.drop(vk)
        else:
            api.delete_data(vk)
        update()
    end=time()
    send_long(peer_id=peer, message=f"Исправление заверешено\nУдалено объектов: {len(changes)}\nЗатраченное время: {end-start}", random_id=0)
    if len(changes):
        text=[]
        for i in changes:
            text+=[f"Сервер {i[0]}  удалён по причине {i[1]} \n"]
        send_long(peer, text)
        write_file()

def sync(peer):
    global targets, servers
    data=api.get_data()
    if data['success']:
        try:
            new_targets=data['data']['main']
            new_servers=servers.copy()
            for i in data['data']['edges']:
                if i['from'] in servers and len(servers[i['from']][1])==3:
                    new_servers[i['from']][1]=[]
                    new_servers[i['from']][0]=servers['01F8A000'][0]
                elif i['from'] not in servers:
                    new_servers[i['from']] = [servers['01F8A000'][0], []]
                if i['to'] not in servers:
                    new_servers[i['to']] = [servers['01F8A000'][0], []]
                new_servers[i['from']][1].append(i['to'])
            servers=new_servers.copy()
            targets=new_targets.copy()
            del new_servers
            del new_targets
            fix(peer)
            send_long(peer, "Синхронизация завершена успешно")
            return True
        except Exception as e:
            send_long(peer, f"Ошибка во время синхронизации: {e}")
    send_long(peer, "Синхронизация прошла неуспешно")

def request(msg):
    global servers, targets
    def fill_starts(date):
        global servers, targets
        servers = {'01F8A000': [date, ['01F8A001', '01F8A002', '01F8A003']]}
        for i in range(1, 4):
            servers[f"{header}{i}"] = [date, []]
    def reset(date):
        global servers, targets
        targets.clear()
        servers.clear()
        fill_starts(date)
        write_file()
    unique=[]
    for message in msg['fwd_messages']:
        text,from_id,date=message['text'],message['from_id'],message['date']
        if from_id!=-172959149 or date<servers[header+"00"][0]:
            continue
        find=re.findall(header+r'[A-Z0-9]{2}', text)
        if len(find) == 4:
            server, *ways=find
            if server in servers:
                if date<=servers[server][0] or servers[server][1]==ways:
                    continue
                # if date>=servers[server][0] and servers[server][1]!=ways and servers[server][1]!=[]:
                # 	servers['9184A500']=int(date)
                # 	fix(298149825)
            if server[-2:]!='00':
                servers[server]=[date, ways]
            unique+=[server]
            for i in ways:
                if i not in servers:
                    unique+=[i]
                    servers[i]=[date, []]
            api.send_new(servers, server)
            write_file()
        elif len(find)>=16:
            targets=find[:16]
            fill_starts(date)
            fix(msg['peer_id'])
            api.update_main(targets)
            send_long(peer_id=298149825, message=f"@id{msg['from_id']} отправил целевые сервера:\n{text}", random_id=0)
            send_long(peer_id=msg['peer_id'], message="Получены целевые сервера", random_id=0)
    if unique!=[]:
        unique=set(unique)
        send_long(peer_id=msg['peer_id'], message=f"Получено {len(unique)} уникальных серверов:\n"+",".join(unique), random_id=0)
    lst = msg['text'].split()
    if len(lst)==0: return
    if lst[0]=='/w' and len(lst)==3:
            send_long(peer_id=msg['peer_id'], message=find_short_way(lst[1].upper(),lst[2].upper()), random_id=0)
    elif lst[0]=='/t' and len(lst)==2:
        start=lst[1].upper()
        if start not in servers and header+start not in servers:
            send_long(peer_id=msg['peer_id'], message='No way', random_id=0)
            return
        if targets==[]:
            send_long(peer_id=msg['peer_id'], message='No data', random_id=0)
            return
        text=""
        if start not in servers: start=header+start
        for i in targets:
            text+='- '*5+i+' -'*5+'\n'+find_short_way(start, i)+'\n\n'
        send_long(peer_id=msg['peer_id'], message=text, random_id=0)
    elif lst[0]=='/k':
        send_long(peer_id=msg['peer_id'], message=get_known(targets), random_id=0)
    elif lst[0]=='/e':
        ends=get_ends()
        send_long(peer_id=msg['peer_id'], message=f"Total: {len(ends)}\n"+"\n".join(ends)+'\n'+'-------------------', random_id=0)
    elif lst[0]=='/info' and len(lst)==2:
        lst[1]=lst[1].upper()
        if lst[1] not in servers and header + lst[1] not in servers: return
        if lst[1] not in servers: lst[1] = header + lst[1]
        send_long(peer_id=msg['peer_id'], message=f"Updated: {servers[lst[1]][0]}\nConnects {lst[1]}:\n"+ '\n'.join(servers[lst[1]][1]), random_id=0)
    elif lst[0]=="/total":
        send_long(peer_id=msg['peer_id'], message=f"Total: {len(servers.keys())}", random_id=0)
    elif lst[0]=='/we' and len(lst)==2:
        start=lst[1].upper()
        if start not in servers and header+start not in servers: return
        if start not in servers: start=header+start
        ends=get_ends()
        text=""
        a=[]
        for i in ends:
            a+=[find_short_way(start, i)]
        a.sort(key=len)
        for i in a:
            text += '- ' * 5 + i[-8::] + ' -' * 5 + '\n' + i + '\n\n'
        send_long(peer_id=msg['peer_id'], message=text, random_id=0)
    elif lst[0]=='/ways' and len(lst)==2:
        lst[1]=lst[1].upper()
        if lst[1] not in servers and header + lst[1] not in servers: return
        if lst[1] not in servers: lst[1] = header + lst[1]
        unreached, _ = dfs(lst[1], list(servers.keys()), [])
        send_long(peer_id=msg['peer_id'], message=f"Достижимо {len(servers.keys())-len(unreached)} устройств\nНедостижимо {len(unreached)} устройств:\n" +" ".join(unreached), random_id=0)
    elif lst[0]=='/c' and len(lst)==2:
        lst[1] = lst[1].upper()
        if lst[1] not in servers and header + lst[1] not in servers: return
        if lst[1] not in servers: lst[1] = header + lst[1]
        way=find_short_way(servers[lst[1]][1][0], lst[1])
        for i in servers[lst[1]][1][1:]:
            nway=find_short_way(i, lst[1])
            if nway == "No way": continue
            if way=="No way" or len(nway)<len(way): way=nway
        send_long(peer_id=msg['peer_id'], message=way, random_id=0)
    elif lst[0]=='/targets':
        send_long(peer_id=msg['peer_id'], message="Targets:\n"+", ".join(targets), random_id=0)
    elif lst[0]=='/idea' and len(lst)>1:
        send_long(peer_id=298149825, message=f"@id{msg['from_id']} предложил идею:\n"+msg['text'][6:],random_id=0)
        send_long(peer_id=msg['peer_id'], message="Предложение отправлено",random_id=0)
    elif lst[0]=='/help':
        send_long(peer_id=msg['peer_id'], message=helps, random_id=0)
    elif lst[0].lower()=='/reset' and msg['from_id'] in [211586351, 298149825, 120358503, 195575331]:
        reset(msg['date'])
        api.delete_data(vk)
        api.do_connects(servers)
        send_long(peer_id=msg['peer_id'], message='Все сервера удалены', random_id=0)
    elif lst[0]=="/update" and msg['from_id'] in [211586351, 298149825, 120358503]:
        threading.Thread(target=update).start()
        send_long(peer_id=msg['peer_id'], message='Обновление запущено', random_id=0)
    elif lst[0]=="/delete" and len(lst)==2 and msg['from_id'] in [211586351, 298149825, 120358503,195575331]:
        lst[1] = lst[1].upper()
        if lst[1] not in servers and header + lst[1] not in servers: return
        if lst[1] not in servers: lst[1] = header + lst[1]
        servers[lst[1]]=[int(msg['date']), []]
        send_long(peer_id=msg['peer_id'], message=f'{lst[1]} удалён', random_id=0)
    elif lst[0].lower() == '/fix' and msg['from_id'] in [211586351, 298149825, 120358503, 195575331]:
        threading.Thread(target=fix, args=(msg['peer_id'],)).start()
    elif lst[0].lower()=='/servers' and msg['from_id'] in [211586351, 298149825, 120358503,195575331]:
        keys=list(servers.keys())
        send_long(peer_id=msg['peer_id'], message=f'Total: {len(keys)}\n {" ".join(keys)}', random_id=0)
    elif lst[0]=='/sync' and msg['from_id'] in [211586351, 298149825, 120358503,195575331]:
        sync(msg['peer_id'])
    elif lst[0] == "/clear" and len(lst)>1 and msg['from_id'] in [211586351, 298149825, 120358503]:
        if 's' in lst[1]:
            api.delete_data(vk)
            send_long(msg['peer_id'], "Данные с сайта удалены")
        if 'e' in lst[1]:
            servers={'01F8A000': servers['01F8A000']}
            send_long(peer_id=msg['peer_id'], message="Сервера удалены")
        if 't' in lst[1]:
            targets=[]
            send_long(msg['peer_id'], "Целевые сервера удалены")
    elif lst[0]=='/set' and len(lst)>1 and msg['from_id'] in [211586351, 298149825, 120358503,195575331]:
        if lst[1]=='time' and len(msg['fwd_messages'])==1:
            fill_starts(msg['fwd_messages'][0]['date'])
            send_long(peer_id=msg['peer_id'], message='Стартовое время установлено', random_id=0)
    elif lst[0]=='/stop' and msg['from_id'] in [211586351, 298149825, 120358503,195575331]:
        send_long(peer_id=msg['peer_id'], message='Бот выключается', random_id=0)
        vk.storage.set(user_id=298149825, key="key", value=str(int(longpoll.ts)+1))
        exit()
    elif lst[0]=='/drop' and msg['from_id'] in [211586351, 298149825, 120358503]:
        api.drop(vk)
        send_long(peer_id=msg['peer_id'], message='Данные сайта сброшены', random_id=0)

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
            vk.storage.set(user_id=298149825, key="key", value=longpoll.ts)
        except Exception as e:
            print("Error:", e)
main()

