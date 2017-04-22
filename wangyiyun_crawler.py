import matplotlib.pyplot as plt
import math
import openpyxl
import xlrd
import requests
from bs4 import BeautifulSoup
import re
import logging
import wangyiyun.Neteasebox.api as api


import numpy as np
import networkx as nx

import time
import random
import datetime
logging.basicConfig(level=logging.INFO)

class music_entity:

    def __init__(self,user_id,graph_size,d):
        """

        :param user_id:
        :param graph_size:number of nodes in this graph
        """
        self.user_id=user_id #the target user
        self.netease=api.NetEase()
        self.graph_size=graph_size #number of nodes in the graph
        self.d=d #prob of taking one of the adjacent edge

        #依照从上到下的顺序,递归调用
        self.user_info_collect={}#{user id：[playlist ids,歌单id...]}
        self.play_info_collect={}#{playlist id:{information 各种信息,包括内含歌曲id列表}}
        self.song_info_collect={}#{song id:{information各种信息}}
        self.artist_info_collect={}#{artist id:{information-去豆瓣}}

        self.net_influence={}

        self.G=nx.DiGraph()
        self.pagerank=''
        self.q=''

        self.result_dict={} #store evaluation result

    def turn_undirected(self):
        self.G=self.G.to_undirected()

    #调用以规定要对谁进行推荐，类似于一个state machine
    def rec_for(self,q,l,result_size):
        self.q=q
        self.l=l #number of steps
        self.result_size=result_size

    #########################################################
    #########################################################
    #########################################################3
    #read graph from the database

    #input graph information from database
    def read_graph(self,path):
        pass


    #########################################################
    #########################################################
    #########################################################3
    # methods to construct the graph


    def user_graph_dfs(self,user_id):
        """using depth first search to construct the network, starting from
        the node refered by user_id

        :param user_id: starting node
        """

        user_id=int(user_id)
        #首先处理该用户下所有歌单的信息
        self.user_plays(user_id)

        #处理完成后构建网络
        for play_id in self.user_info_collect[user_id]:
            creator=int(self.play_info_collect[play_id]['creator'])
            if self.G.has_edge(user_id,creator) or user_id==creator:
                continue
            else:
                if self.G.number_of_nodes() > self.graph_size:
                    print(self.G.number_of_nodes())
                    return

                self.G.add_edge(user_id,creator)
                self.user_graph_dfs(creator)

    def user_graph_bfs(self,user_id):
        """using breadth first search to construct the network, starting from
        the node refered by user_id

        :param user_id:
        :return:
        """

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
            user_id=tmp_que[0]


    def save_graph(self):
        #save all the data of the graph

        nx.draw(self.G,node_size=45)
        plt.savefig("wangyiyun/graph.png")
        plt.show()


    #########################################################
    #########################################################
    #########################################################
    # methods to extract information through the Netease api


    #给一个歌单id，并计算歌单的各种属性
    def play_stat(self,play_id):
        """compute the average popularity of the playlist

        :param play_id:
        :return:
        """
        if self.play_info_collect[play_id].get("popularity",'')!='':
            return

        tmp=[self.song_info_collect[song]["cmttotal"] for song in self.play_info_collect[play_id]]
        tmp=[1/math.log(x) for x in tmp]
        self.play_info_collect[play_id]['popularity']=sum(tmp)/len(tmp)


    def song_attribute(self,song_id):
        """collect information of a song

        :param song_id: id of the target song
        """
        if self.song_info_collect.get(song_id,'')!='':
            return #information of this song has already been collected
        self.song_info_collect[song_id] = {}
        song = self.netease.song_detail(song_id)[0]

        logging.info("information of song "+str(song_id))
        # name
        self.song_info_collect[song_id]['name'] = song['name']

        # artist
        tmp_artist_id=song['artists'][0]['id']
        self.song_info_collect[song_id]['artistid'] = tmp_artist_id

        #if the artist have not been seen before, store the information in the dictionary
        if self.artist_info_collect.get(tmp_artist_id,'')=='':
            self.artist_info_collect[tmp_artist_id] = {}
            self.artist_info_collect[tmp_artist_id]['name'] = song['artists'][0]['name']

        #number of comments
        cmt = self.netease.song_comments(song_id)
        self.song_info_collect[song_id]['cmttotal'] = cmt['total']



    #collect songs of a given playlist
    def collect_songs(self,play_id):
        """collect songs of a playlist

        :param play_id: the target playlist
        """

        #check if this playlist have been seen before
        if self.play_info_collect.get(play_id,'')=='':
            self.play_info_collect[play_id]={}

        #若已收集过歌曲，则不再执行
        if self.play_info_collect[play_id].get('songs','')!='':
            return

        logging.info("collect songs of playlist "+str(play_id))
        song_pool = []

        try:
            # get songs'id in this play list
            for song in self.netease.playlist_detail(play_id):
                song_pool.append(song['id'])

                self.song_attribute(song['id'])

        except:
            logging.info(str(play_id)+" playlist is empty")

        self.play_info_collect[play_id]['songs'] = song_pool


    #输入用户id，收集用户的歌单信息
    def user_plays(self,user_id):
        """collect information of playlists of one user

        :param user_id: id of the user
        """

        user_id = int(user_id)

        while True:
            user_lists = self.netease.user_playlist(user_id,limit=60)#get 60 playlists at most
            try:
                logging.info("number of playlist "+str(len(user_lists)))
                break
            except:
                time.sleep(10)
                logging.info("cannot get information of user "+str(user_id))
                continue

        self.user_info_collect[user_id]=[]
        for item in user_lists:


            # get information about the play list

            # "songs I like" playlist
            if "喜欢的音乐" in item['name']:
                play_id = item['id']
                self.user_info_collect[user_id].append(play_id) #add to the playlists record of the user

                self.play_info_collect[play_id]={}
                self.play_info_collect[play_id]['name'] = item['name']
                self.play_info_collect[play_id]['creator'] = int(item['creator']['userId'])
                continue

            #ignore playlists that have less than 500 subscribers or created by user him/erself
            if item['subscribedCount']<500 or item['creator']==user_id:
                continue

            play_id = item['id']
            self.user_info_collect[user_id].append(play_id)

            if play_id not in self.play_info_collect.keys():
                self.play_info_collect[play_id]={}
                self.play_info_collect[play_id]['name'] = item['name']
                self.play_info_collect[play_id]['createtime']=datetime.datetime.fromtimestamp(item['createTime'] / 1000.0)
                self.play_info_collect[play_id]['creator'] = int(item['creator']['userId']) #换为整数
                self.play_info_collect[play_id]['playcount'] = item['playCount']
                self.play_info_collect[play_id]['subcount'] = int(item['subscribedCount']) #换为整数

                #collect songs of this playlist
                self.collect_songs(play_id)

 
