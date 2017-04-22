import matplotlib.pyplot as plt
import math
import openpyxl
import xlrd
import requests
from bs4 import BeautifulSoup
import re

import wangyiyun.Neteasebox.api as api


import numpy as np
import networkx as nx

import time
import random
import datetime


class music_entity:
    # netease = api.NetEase()
    # song_info_collect = {}

    def __init__(self,user_id,graph_size):
        self.user_id=user_id #图生成的起始位置
        self.netease=api.NetEase()
        self.graph_size=graph_size #目标图的节点数量

        #依照从上到下的顺序,递归调用
        self.user_info_collect={}#{用户id：[歌单id,歌单id...]}
        self.play_info_collect={}#{歌单id:{各种信息,包括内含歌曲id列表}}
        self.song_info_collect={}#{歌曲id:{各种信息}}
        self.artist_info_collect={}#{音乐家id:{各种信息-去豆瓣}}

        self.type_dis={}
        self.net_influence={}
        self.type_dict={1:['R&B','电子','说唱','灵歌','Soul','说唱'],2:['流行','民谣','世界音乐','Pop'],
                        3:['摇滚','布鲁斯'],4:['原声','轻音乐','古典'],5:['爵士','拉丁']}
        self.region_dict={1:['台湾','香港','中国'],2:['日本','Japan'],3:['韩国','Korea'],
                          4:['United States','美国','英国','United Kingdom']}
        self.G=nx.DiGraph()
        self.pagerank=''
        self.q=''

    def turn_undirected(self):
        self.G=self.G.to_undirected()

    #调用以规定要对谁进行推荐，类似于一个state machine
    def rec_for(self,q,l,result_size):
        self.q=q
        self.l=l
        self.result_size=result_size

    #A
    #########################################################
    #########################################################
    #########################################################3
    #B

    def read_graph(self,path):
        pass

    def save_graph(self):
        # workbook=openpyxl.Workbook()
        # worksheet=workbook.get_active_sheet()
        # for item in self.G.edges():
        #     print(item,self.G[item[0]][item[1]]['weight'])
        nx.draw(self.G,node_size=45)
        plt.savefig("wangyiyun/new/graph.png")
        plt.show()

    # B
    #########################################################
    #########################################################
    #########################################################3
    # C

    #深度优先搜索
    def user_graph_dfs(self,user_id):

        user_id=int(user_id) #换为整数
        #首先处理该用户下所有歌单的信息
        self.user_plays(user_id)

        #处理完成后构建网络
        for play_id in self.user_info_collect[user_id]:
            creator=int(self.play_info_collect[play_id]['creator']) #换为整数
            if self.G.has_edge(user_id,creator) or user_id==creator:
                continue
            else:
                if self.G.number_of_nodes() > self.graph_size:
                    print(self.G.number_of_nodes())
                    return

                #,weight=math.log(float(self.play_info_collect[play_id]['subcount']))
                self.G.add_edge(user_id,creator)
                self.user_graph_dfs(creator)

    #广度优先搜索
    def user_graph_bfs(self,user_id):

        user_id = int(user_id)  # 换为整数
        tmp_que=[user_id]

        while self.G.number_of_nodes()<self.graph_size:
            self.user_plays(user_id)

            # 处理完成后构建网络
            for play_id in self.user_info_collect[user_id]:

                creator = int(self.play_info_collect[play_id]['creator']) #换为整数
                if self.G.has_edge(user_id, creator) or user_id == creator:
                    continue
                else:
                    if self.G.number_of_nodes() > self.graph_size:
                        print(self.G.number_of_nodes())
                        return
                    self.G.add_edge(user_id, creator,
                                    weight=math.log(float(self.play_info_collect[play_id]['subcount'])))
                    tmp_que.append(creator)
            tmp_que.pop(0)
            # print(str(tmp_que)+'--------------------')
            user_id=tmp_que[0]


    # C
    #########################################################
    #########################################################
    #########################################################3
    # D pagerank


    #寻找一个用户的代表性歌单
    def like_play(self,user_id,issong=True):
        user_id=int(user_id)
        i_like = ''
        # 抽取我喜欢的音乐
        flag = False

        # 成功在已有歌单里找到
        for item in self.user_info_collect[user_id]:
            print(self.play_info_collect[item]['name'])
            if "喜欢的音乐" in self.play_info_collect[item]['name']:
                flag = True
                print(self.play_info_collect[item]['name'])

                self.collect_songs(item)

                i_like = set(self.play_info_collect[item]['songs'])
                # print(i_like, '-----------')

                break

        # 没有成功在已有歌单里找到，尝试扩展
        if flag == False:
            print(user_id, "该用户没有喜欢的歌单")
            time.sleep(random.random()+1.5)

            while True:
                try:
                    new_play = self.netease.user_playlist(user_id,limit=20)
                    enumerate(new_play)
                    break
                except:
                    print('失败1')
                    time.sleep(random.random()+4)
                    continue

            for idx,item in enumerate(new_play):
                # print(idx,item)
                if "喜欢的音乐" in item['name']:
                    flag = True
                    print(item['name'])

                    self.collect_songs(item['id'])

                    i_like = set(self.play_info_collect[item['id']]['songs'])
                    print(user_id, '找到')
                    print('-----------------')
                    break

                # 已经到了最后一个，仍然没有找到，就随机提取一个
                if idx + 1 == len(new_play):
                    # self.collect_songs(new_play[0])
                    print(user_id, '未找到')
                    print('----------------')
                    i_like = set(self.play_info_collect[new_play[0]['id']]['songs'])

                    break
        if issong:
            return i_like
        else:
            a_like=set()
            for item in i_like:
                self.song_attribute(item)
                tmp=self.song_info_collect[item].get('artistid','')
                if tmp=='':
                    self.song_attribute(item)
                    tmp=self.song_info_collect[item].get('artistid','')
                a_like.add(tmp)

            return list(a_like)


    #基于喜爱歌单关系计算相似用户
    def relevant_users(self,user_id):
        user_id=int(user_id)
        similar_users=[]
        nodes=self.G.nodes()

        i_like=set(self.like_play(user_id))


        #有向图的neighbor只考虑后继节点，因此做出修改
        tmp_neighbor=set(self.G.predecessors(user_id)) | set(self.G.successors(user_id))
        if len(i_like) < 10:  # 喜爱歌单代表性太差，返回其所有邻居
                return tmp_neighbor

        #基于喜爱歌单计算用户之间相似性
        for cand_id in nodes:
            print(cand_id,"进行中")
            other_like = set(self.like_play(cand_id))
            if len(other_like)<10:
                continue

            similarity=len(other_like & i_like)/(len(i_like) if len(i_like)<=len(other_like) else len(other_like))
            if similarity>0.3:
                similar_users.append(cand_id)

        return similar_users if len(similar_users)>1 else tmp_neighbor



    #query 为目标用户的id值,基于该id值计算相似用户集合
    def per_pagerank(self):
        d=0.1
        nodes=self.G.nodes()
        nonodes=len(nodes)
        trans_mat=np.zeros((nonodes,nonodes))

        u_Q=self.relevant_users(self.q)
        #计算转移矩阵
        for i in range(nonodes):
            u = nodes[i]
            # u_Q = self.relevant_users(u)
            # print("相似用户", u_Q)

            for j in range(nonodes):
                print(i,j)

                v=nodes[j]

                if self.G.has_edge(u,v):
                    #*math.log(self.G[u][v]['weight'])
                    trans_mat[i][j]=(1-d)*(1/len(u_Q) if v in u_Q else 0)+d/self.G.in_degree(v)
                else:
                    trans_mat[i][j]=(1-d)*(1/len(u_Q) if v in u_Q else 0)
        print("success mat")
        p_old=[0.1]*nonodes

        for i in range(20):
            p_old=np.dot(trans_mat,np.transpose(p_old))
            print(p_old)
            print('+++++++++')

        print(p_old)
        self.pagerank=[p_old,nodes]
        return p_old,nodes

    def GSparse(self,k):
        result=[]
        while len(result)<k:
            p_new,nodes=self.per_pagerank()
            rank1=nodes[p_new.argmax(p_new)]
            result.append(rank1)
            self.G.remove_node(rank1)
        return result

    # D
    #########################################################
    #########################################################
    #########################################################3
    # E

    #compute l-step expansion set
    def step_expansion_set(self,ids):
        if isinstance(ids,int):
            S=set([ids])
        else:
            S=set(ids)
        # try:
        #     S=set(ids)
        # except:
        #     print(ids)
        V=set(self.G.nodes())

        for v in V-S:

            for u in S:
                try:
                    tmp_l=nx.shortest_path_length(self.G, u, v)
                    print('最短路径为',tmp_l)
                except:
                    tmp_l=10000
                if tmp_l<=self.l:
                    S.add(v)
                    break
        return S

    def step_expansion_ratio(self,ids):
        ori=len(ids)
        exp=self.step_expansion_set(ids)
        return len(exp)/ori

    def norm_rel(self,ids):
        if self.pagerank=='':
            self.per_pagerank()
        S=set(ids)
        print('norm_rel',len(S),self.result_size)

        r_p_new,r_nodes=self.page_rec()



        # rank=np.argsort(-p_new)
        # r_nodes=nodes[rank] #得到排序后的完整推荐列表
        # r_p_new=p_new[rank]

        tmp=0
        for i in range(self.result_size):
            tmp+=r_p_new[i]
        tmp1=tmp/self.result_size

        tmp=0
        for item in S:
            try:
                tmp+=r_p_new[np.where(r_nodes==item)[0][0]]
            except:
                print(item,'-------------------------')
        tmp2=tmp/len(S)

        return tmp2/tmp1



    def exp_rel(self,ids):
        if self.pagerank=='':
            self.per_pagerank() ##?????
        p_new,nodes=self.pagerank

        V=self.step_expansion_set(ids)

        tmp=0
        for item in V:
            tmp+=p_new[nodes.index(item)]
        return tmp

        ####
        # order=np.argsort(-p_new)
        # ranked_p=nodes[order]
        ####

    #给定集合S和节点v
    def marginal_utility(self,v,S):
        if self.pagerank=='':
            self.per_pagerank()
        if len(S)==0:
            return self.exp_rel(v)

        p_new,nodes=self.pagerank
        Vv=self.step_expansion_set(v)-self.step_expansion_set(S)
        tmp=0
        for item in Vv:
            tmp+=p_new[nodes.index(item)]
        return tmp

    def best_coverage(self):
        if self.pagerank=='':
            self.per_pagerank()
        result=[]
        p_new,nodes=self.pagerank
        while len(result)<self.result_size:

            tmp_max=0
            max_item=''
            for item in nodes:
                tmp=self.marginal_utility(item, result)
                if tmp_max<tmp:
                    tmp_max=tmp
                    max_item=item

            result.append(max_item)
        return result


    # E
    #########################################################
    #########################################################
    #########################################################3
    # F



    #给一个歌单id，并计算歌单的各种属性
    def play_stat(self,play_id,mode=1):

        if mode==1:
            #热门度
            tmp=[self.song_info_collect[song]["cmttotal"] for song in self.play_info_collect[play_id]]
            tmp=[1/math.log(x) for x in tmp]
            self.play_info_collect[play_id]['popularity']=sum(tmp)/len(tmp)
            return sum(tmp)/len(tmp)

        elif mode==2:
            #多样性-基于类别
            #标准差越小，多样性越强
            tmp = [self.artist_info_collect[self.song_info_collect[song]['artistid']]["liupai"] for song in self.play_info_collect[play_id]]
            print(tmp)

            for i in range(len(tmp)):
                song_type=tmp[i]
                for item in self.type_dict.items():
                    for k_word in item[1]:
                        if k_word in song_type:
                            tmp[i]=item[0]


            tmp_dict = {}
            for i in range(len(self.type_dict) + 1):
                tmp_dict[i] = 0
            for st in tmp:
                tmp_dict[st] = tmp_dict.get(st, 0) + 1
            tmp = list(tmp_dict.values())
            print(tmp)
            self.play_info_collect[play_id]['typediv']=np.std(np.array(tmp))
            return np.std(np.array(tmp))

        elif mode==3:
            #多样性，基于地区
            tmp = [self.artist_info_collect[self.song_info_collect[song]['artistid']]["liupai"] for song in
                   self.play_info_collect[play_id]]
            print(tmp)

            for i in range(len(tmp)):
                song_type = tmp[i]
                for item in self.type_dict.items():
                    for k_word in item[1]:
                        if k_word in song_type:
                            tmp[i] = item[0]

            tmp_dict = {}
            for i in range(len(self.region_dict) + 1):
                tmp_dict[i] = 0
            for st in tmp:
                tmp_dict[st] = tmp_dict.get(st, 0) + 1
            tmp = list(tmp_dict.values())
            print(tmp)
            self.play_info_collect[play_id]['regiondiv'] = np.std(np.array(tmp))
            return np.std(np.array(tmp))





    # get information about the artist
    #输入艺术家名字，返回艺术家信息,目前并没有什么用
    def douban_crawler(self, artist_id):
            # album_name =self.song_ids[song_id].get('albumname','')
            artist_name = self.artist_info_collect[artist_id].get('name', '')

            album_link = ''

            if artist_name == '':
                return

            # if album_name=='':
            headers = {"Host": "music.douban.com",
                       "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv",
                       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                       "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
                       "Accept-Encoding": "gzip, deflate, br",
                       "Referer": "https",
                       "Cookie": "ll=\"118274\"; bid=KLgbwiyl6vM; __utma=30149280.1005990748.1470236271.1488283373.1488295460.16; __utmz=30149280.1488295460.16.4.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); _vwo_uuid_v2=FC7864CEBBF2E29A79C5BC20E039561A|2986ee0a6281c8a0e814ba05f8e24381; viewed=\"1431812_20494960_3351597_3599368\"; gr_user_id=061fff7f-19b7-4329-a352-a02d46f36675; _pk_id.100001.afe6=8197e4d9eca902e5.1488237297.4.1488295457.1488285725.; ap=1; _pk_ref.100001.afe6=%5B%22%22%2C%22%22%2C1488295457%2C%22https%3A%2F%2Fwww.google.nl%2F%22%5D; _pk_ses.100001.afe6=*; __utmb=30149280.1.10.1488295460; __utmc=30149280; __utmt=1",
                       "Connection": "keep-alive",
                       "Upgrade-Insecure-Requests": "1"}

            data = {"search_text": artist_name}
            r = requests.get("https://music.douban.com/subject_search", headers=headers, params=data)
            # soup = BeautifulSoup(r.text, "lxml")

            # search for artist
            try:
                artist_url = BeautifulSoup(r.text, "lxml").find("a", attrs={"class": "ll musician_title "})["href"]
                rr = requests.get(artist_url)
                artist_soup = BeautifulSoup(rr.text, "lxml")

                artist_info = artist_soup.find("div", attrs={"class", "info"})
                info_list = artist_info.find_all("li")

                for item in info_list:
                    if "国家/地区" in str(item):
                        region_type = re.sub('[\s:]', '',
                                             re.search(re.compile("(?<=/span>)[^}]*(?=</li>)"),
                                                       str(artist_info)).group())
                        self.artist_info_collect[artist_id]['region'] = region_type
                    elif "出生日期" in str(item):
                        time_slot = re.sub('[\s:]', '',
                                           re.search(re.compile("(?<=/span>)[^}]*(?=</li>)"), str(artist_info)).group())
                        self.artist_info_collect[artist_id]['time'] = time_slot
                    elif "流派" in str(item):
                        liupai = re.sub('[\s:]', '',
                                        re.search(re.compile("(?<=/span>)[^}]*(?=</li>)"), str(artist_info)).group())
                        self.artist_info_collect[artist_id]['liupai'] = liupai
                    elif "类型" in str(item):
                        leixing = re.sub('[\s:]', '',
                                         re.search(re.compile("(?<=/span>)[^}]*(?=</li>)"), str(artist_info)).group())
                        self.artist_info_collect[artist_id]['leixing'] = leixing
                        # best_albs = artist_soup.find("div", attrs={"id": "best_albums"})
                        # alb_url = best_albs.find("div", attrs={"class": "info"}).find("a")["href"]
                        # rrr=requests.get(alb_url)

                        # print(alburl)
            except:
                print('无法找到该歌手' + artist_name)

    #输入歌曲id，返回歌曲信息
    def song_attribute(self,song_id):
        if self.song_info_collect.get(song_id,'')!='':
            return
        self.song_info_collect[song_id] = {}
        song = self.netease.song_detail(song_id)[0]


        # print(cmt)

        # information
        self.song_info_collect[song_id]['name'] = song['name']
        # self.song_info_collect[song_id]['albumid'] = song['album']['id']
        # self.song_info_collect[song_id]['albumname'] = song['album']['name']

        tmp_artist_id=song['artists'][0]['id']
        self.song_info_collect[song_id]['artistid'] = tmp_artist_id
        # self.song_info_collect[song_id]['artistname'] = song['artists'][0]['name']

        #如果没有存储艺术家信息，则...
        if self.artist_info_collect.get(tmp_artist_id,'')=='':
            self.artist_info_collect[tmp_artist_id] = {}
            self.artist_info_collect[tmp_artist_id]['name'] = song['artists'][0]['name']

            #暂时不收集douban上的歌手信息
            # self.douban_crawler(tmp_artist_id)

        cmt = self.netease.song_comments(song_id)
        self.song_info_collect[song_id]['cmttotal'] = cmt['total']

        #评论中的用户采集暂时无用处
        # cmt_block = cmt['hotComments']
        # self.song_info_collect[song_id]['users'] = []
        # for item in cmt_block:
        #     self.song_info_collect[song_id]['users'].append(cmt_block.get('user')['userId'])



    #仅在必要时收集一个歌单的歌曲, 在仅构建网络的前提下暂时无用
    def collect_songs(self,play_id):

        #若之前没有收集过该歌单信息，则创建
        if self.play_info_collect.get(play_id,'')=='':
            self.play_info_collect[play_id]={}

        #若已收集过歌曲，则不再执行
        if self.play_info_collect[play_id].get('songs','')!='':
            return
        #
        song_pool = []

        try:
            # get songs'id in this play list
            for song in self.netease.playlist_detail(play_id):
                song_pool.append(song['id'])

                #暂时不需要歌曲信息
                # if song['id'] not in self.song_info_collect.keys():
                #     self.song_attribute(song['id'])
        except:
            print(play_id)
            print("该歌单为空")

        self.play_info_collect[play_id]['songs'] = song_pool



    # analyzing data in the excel file

    #输入用户id，收集用户的歌单信息
    def user_plays(self,user_id):

        user_id = int(user_id)  # 换为整数

        while True:
            user_lists = self.netease.user_playlist(user_id,limit=60)
            try:
                print(len(user_lists))
                break
            except:
                time.sleep(10)
                print("出现问题")
                continue
        self.user_info_collect[user_id]=[]
        for item in user_lists:


            # get information about the play list

            if "喜欢的音乐" in item['name']:
                play_id = item['id']
                self.user_info_collect[user_id].append(play_id) #加入用户歌单列表中

                self.play_info_collect[play_id]={}
                self.play_info_collect[play_id]['name'] = item['name']
                self.play_info_collect[play_id]['creator'] = int(item['creator']['userId'])  # 换为整数
                continue

            #对于subscribe人数小于500的歌单不予考虑
            if item['subscribedCount']<500 or item['creator']==user_id:
                continue

            play_id = item['id']
            self.user_info_collect[user_id].append(play_id)

            if play_id not in self.play_info_collect.keys():
                self.play_info_collect[play_id]={}
                self.play_info_collect[play_id]['name'] = item['name']
                self.play_info_collect[play_id]['createtime']=datetime.datetime.fromtimestamp(item['createTime'] / 1000.0)
                self.play_info_collect[play_id]['creator'] = int(item['creator']['userId']) #换为整数
                # creator_add = [item['creator'].get('birthday', ''), item['creator'].get('gender', ''),
                #                        item['creator'].get('province', '')]
                self.play_info_collect[play_id]['playcount'] = item['playCount']
                self.play_info_collect[play_id]['subcount'] = int(item['subscribedCount']) #换为整数

                #在仅构建网络的前提下暂时无用
                # song_pool = []
                #
                # try:
                #     # get songs'id in this play list
                #     for song in self.netease.playlist_detail(play_id):
                #         song_pool.append(song['id'])
                #         if song['id'] not in self.song_info_collect.keys():
                #             self.song_attribute(song['id'])
                # except:
                #     print(play_id)
                #     print("该歌单为空")
                #
                # self.play_info_collect[play_id]['songs']= str(song_pool)

    def random_rec(self):
        result=[]
        for i in range(self.result_size):
            nodes=self.G.nodes()
            result.append(nodes[random.randint(0,len(nodes)-1)])
        return result

    def page_rec(self):
        if self.pagerank=='':
            self.per_pagerank()
        p_new,nodes=self.pagerank

        p_new=np.array(p_new)
        nodes=np.array(nodes)
        rank=np.argsort(-p_new)
        p_new=p_new[rank]
        nodes=nodes[rank]
        return p_new,nodes

    #衡量推荐结果,在给定k和推荐对象的条件下
    def rec_stat(self,tar=''):
        result_dict={}
        result_dict['pagerank']={}
        result_dict['random']={}
        result_dict['best']={}

        if tar=='':
            tar=self.user_id
        p_new,nodes=self.page_rec()
        p_rec=nodes[0:self.result_size]

        r_rec=self.random_rec()
        b_rec=self.best_coverage()

        #relevance
        result_dict['pagerank']['rel']=self.norm_rel(p_rec)
        result_dict['random']['rel'] =self.norm_rel(r_rec)
        result_dict['best']['rel'] =self.norm_rel(b_rec)

        #diversity
        result_dict['pagerank']['exp'] = self.step_expansion_ratio(p_rec)
        result_dict['random']['exp'] = self.step_expansion_ratio(r_rec)
        result_dict['best']['exp'] = self.step_expansion_ratio(b_rec)

        #exp rel
        result_dict['pagerank']['er'] = self.exp_rel(p_rec)
        result_dict['random']['er'] = self.exp_rel(r_rec)
        result_dict['best']['er'] = self.exp_rel(b_rec)

        print(result_dict)
        workbook=openpyxl.Workbook()
        worksheet=workbook.get_active_sheet()
        lf=['rel','exp','er']
        lm=['pagerank','random','best']
        for i in range(len(lm)):
            for j in range(len(lf)):
                worksheet.cell(row=i+1,column=j+1).value=result_dict[lm[i]][lf[j]]

        workbook.save('wangyiyun/new/stat'+str(self.result_size)+'.xlsx')





#static methods
def to_unweighted(G):
    new_G=nx.Graph()
    for edges in G.edges():
        new_G.add_edge(edges[0],edges[1])
    return new_G


def degree_hist(G):
    G=to_unweighted(G)
    # G = nx.gnp_random_graph(100, 0.02)

    degree_sequence = sorted(nx.degree(G).values(), reverse=True)  # degree sequence
    # print "Degree sequence", degree_sequence
    dmax = max(degree_sequence)

    plt.loglog(degree_sequence, 'b-', marker='o')
    plt.title("Degree rank plot")
    plt.ylabel("degree")
    plt.xlabel("rank")

    # draw graph in inset
    plt.axes([0.45, 0.45, 0.45, 0.45])
    Gcc = sorted(nx.connected_component_subgraphs(G), key=len, reverse=True)[0]
    pos = nx.spring_layout(Gcc)
    plt.axis('off')
    nx.draw_networkx_nodes(Gcc, pos, node_size=20)
    nx.draw_networkx_edges(Gcc, pos, alpha=0.4)

    plt.savefig("wangyiyun/new/degree_histogram.png")
    plt.show()


def graph_stat(G):
    # print(G)
    G=to_unweighted(G)
    print("图为")
    print(G.edges())
    workbook=openpyxl.Workbook()
    worksheet=workbook.get_active_sheet()

    worksheet.cell(row=1,column=1).value=nx.average_clustering(G)
    worksheet.cell(row=1,column= 2).value =nx.degree_assortativity_coefficient(G)
    worksheet.cell(row=1, column=3).value =nx.diameter(G)
    worksheet.cell(row=1, column=4).value =nx.average_shortest_path_length(G)

    workbook.save("wangyiyun/new/stat.xlsx")


test_id="48548007"
graph=music_entity(user_id=test_id,graph_size=500)
graph.user_graph_dfs(graph.user_id) #生成图

#第一部分，只要求提供图结构
#计算图的各种统计指标，这里将其转化成了无向无权图
graph.save_graph()
# degree_hist(graph.G.to_undirected())
# print(graph.G.nodes())
# print(graph.G.to_undirected().nodes())
# graph_stat(graph.G.to_undirected())
#
#
# #第二部分，基于图的推荐，需要提供 推荐对象，步长，和推荐列表大小
# test_k=[10,20,50]
#
# for k in test_k:
#
#     #设定实验参数
#     print("success1")
#     graph.rec_for(graph.user_id,l=2,result_size=k)
#     graph.per_pagerank()
#     graph.rec_stat()
#     print("success2")
