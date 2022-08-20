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

def write_file():
    with open("../servers.py", "w") as f:
        f.write(str(servers))
        f.write('\n' + str(targets))

try:
    with open("../servers.py", "r") as read:
        servers=eval(read.readline())
        if servers=="" or servers=={}: servers={'01F8A000': [0, ['01F8A001', '01F8A002', '01F8A003']]}
        try:
            targets = eval(read.readline())
            if targets == "": targets = {}
        except:
            targets = {}
except:
    servers={'01F8A000': [0, ['01F8A001', '01F8A002', '01F8A003']]}
    targets={}
    write_file()

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
            vk.messages.send(peer_id=peer_id, message=text, random_id=random_id)
            text = ""
    if text!="":
        vk.messages.send(peer_id=peer_id, message=text, random_id=random_id)

def find_short_way(start,goal, args=[]):
    global servers
    if start not in servers and header+start in servers: start=header+start
    if goal not in servers and header+goal in servers: goal=header+goal
    queue = deque([start])
    visited = {start: None}
    while queue:
        cur_node = queue.popleft()
        if cur_node == goal:
            break
        if cur_node in servers and cur_node[-2:] not in args and cur_node not in args:
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
    api.bigdata(servers)
    api.update_main(targets)

def fill_starts(date):
    global servers
    servers['01F8A000'][0]=int(date)

def fix(peer):
    global servers
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
            changes+=[[i, f'Sent before reset: {servers[i][0]}<{servers["01F8A000"][0]}']]
            del servers[i]
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

def sync(peer, stime=servers[header+'00'][0]):
    global servers, targets
    data= api.get_from_sb()
    if data!=[]:
        try:
            new_servers = servers
            new = 0
            for i in data:
                fr = i['from']
                to = i['to']
                if fr in new_servers and to != servers[fr][1] or fr not in new_servers:
                    if fr not in new_servers:
                        new += 1
                    new_servers[fr] = [stime, to]
                    for j in to:
                        if j not in new_servers:
                            new_servers[j] = [stime, []]
                            new += 1
            servers=new_servers.copy()
            del new_servers
            fill_starts(stime)
            fix(peer)
            write_file()
            send_long(peer, f"Синхронизация завершена успешно\n Добавлено {new} новых серверов")
            return True
        except Exception as e:
            send_long(peer, f"Ошибка во время синхронизации: {e}")
    send_long(peer, "Синхронизация прошла неуспешно")

def request(msg):
    global servers,targets
    # if msg['from_id']!=298149825:
    #     return
    def reset(date):
        global servers
        servers.clear()
        fill_starts(date)
        for i in range(1, 4):
            servers[f"{header}{i}"] = [date, []]
        write_file()
    unique=[]
    f=False
    out_of_date=0
    for message in msg['fwd_messages']:
        text,from_id,date=message['text'],message['from_id'],message['date']
        if from_id != -172959149:
            continue
        find=re.findall(header+r'[A-Z0-9]{2}', text)
        if len(find) == 4:
            if date < servers[header + "00"][0]:
                out_of_date += 1
                continue
            server, *ways=find
            files = re.findall(r'📝.+\n', text)
            if len(files) > 0 and date//3600==time()//3600:
                print(f"Отправка информации о файлах {files} на сервере {server}:", api.send_files(server, [i[1:-1] for i in files]))
            f = True
            if server in servers:
                if date<=servers[server][0] or servers[server][1]==ways:
                    continue
                if date>=servers[server][0] and servers[server][1]!=ways and servers[server][1]!=[]:
                	servers['01F8A000'][0]=int(date)//3600*3600
                	fix(298149825)
            if server[-2:]!='00':
                servers[server]=[date, ways]
            unique+=[server]
            for i in ways:
                if i not in servers:
                    unique+=[i]
                    servers[i]=[date, []]
            api.send_new(servers, server)
            write_file()
        elif len(find)==9 and servers[header+'00'][0]<=date:
            fill_starts(date)
            fix(msg['peer_id'])
            fracs = re.findall(r'[🔱🇺🇸💠🚧🎭🈵].{3,8}', text)
            targets={}
            for i in range(6):
                frac = fracs[i]
                frac = "NHS" if frac[-3:] == "NHS" else "Huoqiang" if frac[-1]=='g' else frac[1:]
                targets[frac]=find[i]
            write_file()
            api.delete_data(vk)
            api.update_main(targets)
            api.bigdata(servers)
            send_long(peer_id=298149825, message=f"@id{msg['from_id']} отправил целевые сервера:\n{text}", random_id=0)
            send_long(peer_id=msg['peer_id'], message="Целевые сервера обновлены", random_id=0)
    if unique!=[]:
        unique=set(unique)
        send_long(peer_id=msg['peer_id'], message=f"Получено {len(unique)} уникальных серверов:\n"+",".join(unique), random_id=0)
    elif f:
        send_long(peer_id=msg['peer_id'], message=f"Получено 0 уникальных серверов", random_id=0)
    if out_of_date>0:
        send_long(peer_id=msg['peer_id'], message=f"Получено {out_of_date} устаревших серверов", random_id=0)
    lst = msg['text'].split()
    if len(lst)==0: return
    if lst[0]=='/w' and len(lst)>=3:
            if len(lst)>3:
                avade=msg['text'].upper().split()[3:]
            else:
                avade=[]
            if 'T' in avade:
                avade.remove('T')
                avade+=targets.values()
            avade=list(set(avade))
            send_long(peer_id=msg['peer_id'], message=find_short_way(lst[1].upper(),lst[2].upper(), avade), random_id=0)
    elif lst[0]=='/t':
        if len(lst)==1:
            send_long(peer_id=msg['peer_id'], message="Целевые сервера:\n"+'\n'.join([i+': '+targets[i] for i in targets])+'\n--------------------------', random_id=0)
            return
        start=lst[1].upper()
        if start not in servers and header+start not in servers:
            send_long(peer_id=msg['peer_id'], message='Стартовый сервер не изучен', random_id=0)
            return
        if targets=={}:
            send_long(peer_id=msg['peer_id'], message='Нет целевых серверов', random_id=0)
            return
        text=""
        if start not in servers: start=header+start
        for i in targets:
            text+='- '*5+i+' -'*5+'\n'+find_short_way(start, targets[i], list(targets.values()))+'\n\n'
        send_long(peer_id=msg['peer_id'], message=text, random_id=0)
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
    elif lst[0]=='/we' and len(lst)>1:
        start=lst[1].upper()
        if start not in servers and header+start not in servers: return
        if start not in servers: start=header+start
        ends=get_ends()
        text=""
        a=[]
        for i in ends:
            path=find_short_way(start, i)
            if path[:2] != 'No':
                a+=[path]
        a.sort(key=len)
        try:
            n=int(lst[2])-1
        except:
            n=4
        for cnt, i in enumerate(a):
            text += '- ' * 5 + i[-8::] + ' -' * 5 + '\n' + i + '\n\n'
            if cnt==n:
                break
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
    elif lst[0]=='/idea' and len(lst)>1:
        send_long(peer_id=298149825, message=f"@id{msg['from_id']} предложил идею:\n"+msg['text'][6:],random_id=0)
        send_long(peer_id=msg['peer_id'], message="Предложение отправлено",random_id=0)
    elif lst[0]=='/help':
        send_long(peer_id=msg['peer_id'], message=helps, random_id=0)
    elif lst[0].lower()=='/reset' and msg['from_id'] in [211586351, 298149825, 120358503, 195575331, 249231064]:
        reset(msg['date'])
        api.delete_data(vk)
        api.do_connects(servers)
        send_long(peer_id=msg['peer_id'], message='Все сервера удалены', random_id=0)
    elif lst[0]=="/update" and msg['from_id'] in [211586351, 298149825, 120358503, 249231064]:
        threading.Thread(target=update).start()
        send_long(peer_id=msg['peer_id'], message='Обновление запущено', random_id=0)
    elif lst[0]=="/delete" and len(lst)==2 and msg['from_id'] in [211586351, 298149825, 120358503,195575331, 249231064]:
        lst[1] = lst[1].upper()
        if lst[1] not in servers and header + lst[1] not in servers: return
        if lst[1] not in servers: lst[1] = header + lst[1]
        servers[lst[1]]=[int(msg['date']), []]
        send_long(peer_id=msg['peer_id'], message=f'{lst[1]} удалён', random_id=0)
    elif lst[0].lower() == '/fix' and msg['from_id'] in [211586351, 298149825, 120358503, 195575331, 249231064]:
        threading.Thread(target=fix, args=(msg['peer_id'],)).start()
    elif lst[0].lower()=='/servers' and msg['from_id'] in [211586351, 298149825, 120358503,195575331, 249231064]:
        keys=list(servers.keys())
        send_long(peer_id=msg['peer_id'], message=f'Total: {len(keys)}\n {" ".join(keys)}', random_id=0)
    elif lst[0]=='/sync' and msg['from_id'] in [211586351, 298149825, 120358503, 195575331, 249231064]:
        sync(msg['peer_id'])
    elif lst[0] == "/clear" and len(lst)>1 and msg['from_id'] in [211586351, 298149825, 120358503, 249231064]:
        if 's' in lst[1]:
            api.delete_data(vk)
            send_long(msg['peer_id'], "Данные с сайта удалены")
        if 'e' in lst[1]:
            servers={'01F8A000': servers['01F8A000']}
            send_long(peer_id=msg['peer_id'], message="Сервера удалены")
        if 't' in lst[1]:
            targets = {}
            send_long(msg['peer_id'], "Целевые сервера удалены")
    elif lst[0]=='/set' and len(lst)>1 and msg['from_id'] in [211586351, 298149825, 120358503,195575331, 249231064]:
        if lst[1]=='time' and len(msg['fwd_messages'])==1:
            fill_starts(int(msg['fwd_messages'][0]['date']))
            send_long(peer_id=msg['peer_id'], message='Стартовое время установлено', random_id=0)
    elif lst[0]=='/stop' and msg['from_id'] in [211586351, 298149825, 120358503,195575331, 249231064]:
        send_long(peer_id=msg['peer_id'], message='Бот выключается', random_id=0)
        vk.storage.set(user_id=298149825, key="key", value=str(int(longpoll.ts)+1))
        exit()
    elif lst[0]=='/drop' and msg['from_id'] in [211586351, 298149825, 120358503, 249231064]:
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

