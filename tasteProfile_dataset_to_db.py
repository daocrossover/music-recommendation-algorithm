# -*- coding: UTF-8 -*-
from __future__ import division
import pymysql
import json
import os
import math
import time
import sys
import pickle

config = {
    'host': 'localhost',
    'user': 'root',
    'password': '960513',
    'database': 'recommenderSystem'
}

def appendData(userID, songs, usersSongs, songsUsers):
    songsString = ''
    for song, playCount in songs.items():
        songs[song] = playCount
        
        if song not in songsUsers:
            songsUsers[song] = set()
            songsUsers[song].add(userID)
        else:
            songsUsers[song].add(userID)
    
    songsString = json.dumps(songs)
    usersSongs.append((userID, songsString, len(songs)))

# MySQL dataset config：
# max_allowed_packet = 512M
# innodb_buffer_pool_size = 2G

# process the Taste Profile subset and store it into the database
def tasteProfile_dataset_to_db(dataFile):
    usersSongs = []
    songsUsers = {} # keys are songIDs, values are sets of listeners
    userID = None
    songs = {}
    totalPlays = 0
    lineCount = 0
    totalUserCount = 0
    bashCount = 0
    db = pymysql.connect(**config)
    cur = db.cursor()
    cur.execute('use recommenderSystem')
    with open(dataFile,'r') as openFile:
        for line in openFile:
            thisLine = line.replace('\n', '').split('\t')
            if thisLine[0] != userID:
                if userID is not None:
                    appendData(userID, songs, usersSongs, songsUsers)
                    totalUserCount += 1
                    bashCount += 1
                userID = thisLine[0]
                songs = {}
                totalPlays = 0
                
            songs[thisLine[1]] = int(thisLine[2])
            lineCount += 1
            if bashCount > 50000:
                try:
                    cur.executemany("insert into user_songs(userID,songs,songsCount) values(%s, %s, %s)", usersSongs)
                    db.commit()
                    print('insert bash users finished')
                except Exception as e:
                    print(e)

                usersSongs.clear()
                bashCount = 0
                print("bash operation finished")
                #break

    appendData(userID, songs, usersSongs, songsUsers)
    openFile.close()

    try:
        cur.executemany("insert into user_songs(userID,songs,songsCount) values(%s, %s, %s)", usersSongs)
        cur.execute("alter table user_songs add primary key (userID)")
        db.commit()
    except Exception as e:
        print(e)
    usersSongs.clear()
    print("user_songs dump finished")
    print("totalUserCount: ", totalUserCount)

    songsUsersList = []
    for song in songsUsers:
        songsUsersList.append((song, repr(songsUsers[song]), len(songsUsers[song])))
    songsUsers.clear()
    try:
        cur.executemany("insert into song_users(songID, users, usersCount) values(%s, %s, %s)", songsUsersList)
        cur.execute("alter table song_users add primary key (songID)")
        db.commit()
    except Exception as e:
        print(e)
    print("totalSongCount: ", len(songsUsersList))
    songsUsersList.clear()
    print("song_users dump finished")
    db.close()

"""
def calculate_ItemCF_similarity():
    userSongs = []
    songsUserCount = {}
    songSimilarity = {}
    db = pymysql.connect(host="localhost", user="root", password="960513", db="recommenderSystem")
    cur = db.cursor()
    try:
        cur.execute('use recommenderSystem')
        cur.execute("select songs from user_songs")
        userSongs = cur.fetchall()
    except Exception as e:
        print(e)
    print("userSongs load finished")

    try:
        cur.execute("select * from sub_song_users")
        results = cur.fetchall()
        for result in results:
            songsUserCount[result[1]] = (result[0], result[2])
    except Exception as e:
        print(e)
    print("songsUserCount load finished")
    db.close()

    for usersong in userSongs:
        songs = json.loads(usersong[0])
        keys = sorted(songs.keys())
        for i in range(len(keys)):
            if songsUserCount.__contains__(keys[i]):
                songSimilarity.setdefault(keys[i], {})
                for j in range(i+1, len(keys)):
                    if songsUserCount.__contains__(keys[j]):
                        songSimilarity[keys[i]].setdefault(keys[j], 0)
                        songSimilarity[keys[i]][keys[j]] += 1       
        if (userSongs.index(usersong) + 1) % 50 == 0:
            print(userSongs.index(usersong))
            print(len(songSimilarity))
            db = pymysql.connect(host="localhost", user="root", password="960513", db="recommenderSystem")
            cur = db.cursor()
            cur.execute('use recommenderSystem')
            for key1 in songSimilarity:
                for key2 in songSimilarity[key1]:
                    cur.execute("select * from itemCF_similarity where songID_i = %s and songID_j = %s limit 1", (key1, key2))
                    result = cur.fetchone()
                    if result == None:
                        cur.execute("insert into itemCF_similarity(songID_i,songID_j,commonUsersCount) values(%s,%s,%s)", (key1, key2, songSimilarity[key1][key2]))
                    else:
                        cur.execute("update itemCF_similarity set commonUsersCount = commonUsersCount + %s where songID_i = %s and songID_j = %s", (songSimilarity[key1][key2], key1, key2))
            db.commit()
            print(userSongs.index(usersong), " db change finished")
            songSimilarity.clear()
            #break
    print(len(songSimilarity))
    db = pymysql.connect(host="localhost", user="root", password="960513", db="recommenderSystem")
    cur = db.cursor()
    for key1 in songSimilarity:
        for key2 in songSimilarity[key1]:
            cur.execute("select * from itemCF_similarity where songID_i = %s and songID_j = %s limit 1", (key1, key2))
            result = cur.fetchone()
            if result == None:
                cur.execute("insert into itemCF_similarity(songID_i,songID_j,commonUsersCount) values(%s,%s,%s)", (key1, key2, songSimilarity[key1][key2]))
            else:
                cur.execute("update itemCF_similarity set commonUsersCount = commonUsersCount + %s where songID_i = %s and songID_j = %s", (songSimilarity[key1][key2], key1, key2))
    db.commit()
    db.close()
    print("db change finished")
    songSimilarity.clear()
"""

# calculate item-based collaborative filtering similarity matrix and store it into the database
def calculate_ItemCF_similarity(a):
    songsUsers = []
    usersSongsCount = {}
    songSimilarity = []
    songCount = 0
    db = pymysql.connect(**config)
    cur = db.cursor()
    try:
        cur.execute('use recommenderSystem')
        cur.execute("select trackID, users, usersCount from sample_tracks")
        songsUsers = cur.fetchall()
        cur.execute("select userID, songsCount from user_songs_train")
        results = cur.fetchall()
        for res in results:
            usersSongsCount[res[0]] = res[1]
    except Exception as e:
        print(e)
    print("songUsers & usersSongsCount load finished")

    for i in range(len(songsUsers)):
        songCount += 1
        similarityDict = dict()
        for j in range(len(songsUsers)):
            if songsUsers[i][0] != songsUsers[j][0]:
                commonUsers = eval(songsUsers[i][1]) & eval(songsUsers[j][1])
                commonUsersNum = len(commonUsers)
                if commonUsersNum > 0:
                    IUF = 0
                    for commonUser in commonUsers:
                        IUF += 1 / math.log(1 + usersSongsCount[commonUser] * 1.0)
                    # similarity = IUF / math.sqrt(songsUsers[i][2] * songsUsers[j][2])
                    similarity = IUF / math.pow(songsUsers[i][2], 1-a) * math.pow(songsUsers[j][2], a)
                    similarityDict[songsUsers[j][0]] = similarity
        if similarityDict:
            maxSim = max(similarityDict.values())
            for song_j in similarityDict:
                similarityDict[song_j] /= maxSim
                similarityDict[song_j] = round(similarityDict[song_j], 5)
        similarityDictString = json.dumps(similarityDict)
        songSimilarity.append((songsUsers[i][0],similarityDictString))
        print(songCount)
        if songCount == 200:
            try: 
                cur.executemany("insert into song_similarity(trackID,itemCF_similarity) values(%s, %s)", songSimilarity)                #cur.execute("alter table song_similarity add primary key (trackID)")
                db.commit()
                print('bash insert finished')
            except Exception as e:
                print(e)
            songSimilarity.clear()
            songCount = 0
    try: 
        cur.executemany("insert into song_similarity(trackID,itemCF_similarity) values(%s, %s)", songSimilarity)
        cur.execute("alter table song_similarity add primary key (trackID)")
        db.commit()
    except Exception as e:
        print(e)    
    print('itemCF_similarity dump finished')

    db.close()
    #songsUsers.clear()
    usersSongsCount.clear()
    songSimilarity.clear()

# score_mode
# 0 —— count
# 1 —— binary count

# implementation of item-based collaborative filtering recommendation algorithm
def ItemCF_Recommendation(userID, K, N, score_mode, ID_mapping):
    action_songs = dict()
    action_songs_set = set()
    similarity = dict()
    rank = dict()
    db = pymysql.connect(**config)
    cur = db.cursor()
    cur.execute('use recommenderSystem')
    try:
        cur.execute("select songs from user_songs_test_visible where userID = %s", userID)
        result = cur.fetchone()
        action_songs = json.loads(result[0])
    except Exception as e:
        print(e)

    for song in action_songs:
        action_songs_set.add(ID_mapping[song])

    for song, score in action_songs.items():
        tmp = 0
        if score_mode == 0:
            tmp = score
        elif score_mode == 1:
            tmp = 1
        try:
            cur.execute("select itemCF_similarity from song_similarity where trackID = %s", ID_mapping[song])
            result = cur.fetchone()
            similarity = json.loads(result[0])
        except Exception as e:
            print(e)
        #print('similarity dict finished')
        #print(similarity)
        for j,sim in sorted(similarity.items(), key=lambda x:x[1], reverse=True)[0:K]:
            if j in action_songs_set:
                continue
            rank.setdefault(j,0)
            rank[j] += tmp * sim
    db.close()
    return dict(sorted(rank.items(),key=lambda x:x[1],reverse=True)[0:N])

# similarity_mode
# 0 —— all 5000 topwords TF-IDF similarities
# 1 —— all 5000 topwords TF-IDF with LSA similarities
# 2 —— 5000 topwords without stopwords TF-IDF similarities
# 3 —— 5000 topwords without stopwords TF-IDF with LSA similarities

# implementation of lyric-based recommendation algorithm
def Lyric_based_Recommendation(userID, K, N, score_mode, ID_mapping, trackID_list, similarity_mode):
    action_songs = dict()
    action_songs_set = set()
    rank = dict()
    db = pymysql.connect(**config)
    cur = db.cursor()
    cur.execute('use recommenderSystem')
    try:
        cur.execute("select songs from user_songs_test_visible where userID = %s", userID)
        result = cur.fetchone()
        action_songs = json.loads(result[0])
    except Exception as e:
        print(e)

    for song in action_songs:
        action_songs_set.add(ID_mapping[song])

    for song, score in action_songs.items():
        tmp = 0
        if score_mode == 0:
            tmp = score
        elif score_mode == 1:
            tmp = 1
        try:
            if similarity_mode == 0:
                cur.execute("select all_TFIDF_similarity from gensim_similarity where trackID = %s limit 1", ID_mapping[song])
            elif similarity_mode == 1:
                cur.execute("select all_TFIDF_LSA_similarity from gensim_similarity where trackID = %s limit 1", ID_mapping[song])
            elif similarity_mode == 2:
                cur.execute("select without_stopwords_TFIDF_similarity from gensim_similarity where trackID = %s limit 1", ID_mapping[song])
            else:
                cur.execute("select without_stopwords_TFIDF_LSA_similarity from gensim_similarity where trackID = %s limit 1", ID_mapping[song])
            result = cur.fetchone()
            similarity_list = json.loads(result[0])
        except Exception as e:
            print(e)

        for j, sim in sorted(enumerate(similarity_list), key=lambda x:x[1], reverse=True)[0:K]:
            #print(sorted(similarity_list, key=lambda x:x[1], reverse=True)[0:K])
            if trackID_list[j] == ID_mapping[song]:
                continue
            if trackID_list[j] in action_songs_set:
                continue
            rank.setdefault(trackID_list[j],0)
            rank[trackID_list[j]] += tmp * sim

    db.close()
    return dict(sorted(rank.items(),key=lambda x:x[1],reverse=True)[0:N])

# tag mode
# 0 —— all tags TF-IDF similarities
# 1 —— all tags TF-IDF with LSA similarities

# implementation of tag-based recommendation algorithm
def Tag_based_Recommendation(userID, K, N, score_mode, ID_mapping, trackID_list, tag_mode):
    action_songs = dict()
    action_songs_set = set()
    rank = dict()
    db = pymysql.connect(**config)
    cur = db.cursor()
    cur.execute('use recommenderSystem')
    try:
        cur.execute("select songs from user_songs_test_visible where userID = %s", userID)
        result = cur.fetchone()
        action_songs = json.loads(result[0])
    except Exception as e:
        print(e)

    for song in action_songs:
        action_songs_set.add(ID_mapping[song])

    for song, score in action_songs.items():
        tmp = 0
        if score_mode == 0:
            tmp = score
        elif score_mode == 1:
            tmp = 1
        try:
            if tag_mode == 0:
                cur.execute("select all_TFIDF_similarity from gensim_tag_similarity where trackID = %s limit 1", ID_mapping[song])
            else:
                cur.execute("select all_TFIDF_LSA_similarity from gensim_tag_similarity where trackID = %s limit 1", ID_mapping[song])
            result = cur.fetchone()
            similarity_list = json.loads(result[0])
        except Exception as e:
            print(e)

        for j, sim in sorted(enumerate(similarity_list), key=lambda x:x[1], reverse=True)[0:K]:
            #print(sorted(similarity_list, key=lambda x:x[1], reverse=True)[0:K])
            if trackID_list[j] == ID_mapping[song]:
                continue
            if trackID_list[j] in action_songs_set:
                continue
            rank.setdefault(trackID_list[j],0)
            rank[trackID_list[j]] += tmp * sim
    db.close()
    return dict(sorted(rank.items(),key=lambda x:x[1],reverse=True)[0:N])

# implementation of hybrid recommendation algorithm
def Hybrid_Recommendation(userID, ID_mapping, trackID_list, K, N, a, b, score_mode, similarity_mode, tag_mode):
    action_songs = dict()
    action_songs_set = set()
    rank = dict()
    db = pymysql.connect(**config)
    cur = db.cursor()
    cur.execute('use recommenderSystem')
    try:
        cur.execute("select songs from user_songs_test_visible where userID = %s", userID)
        result = cur.fetchone()
        action_songs = json.loads(result[0])
    except Exception as e:
        print(e)

    for song in action_songs:
        action_songs_set.add(ID_mapping[song])

    for song, score in action_songs.items():
        hybrid_similarity_list = []
        tmp = 0
        if score_mode == 0:
            tmp = score
        elif score_mode == 1:
            tmp = 1
        try:
            if similarity_mode == 0:
                cur.execute("select all_TFIDF_similarity from gensim_similarity where trackID = %s limit 1", ID_mapping[song])
            elif similarity_mode == 1:
                cur.execute("select all_TFIDF_LSA_similarity from gensim_similarity where trackID = %s limit 1", ID_mapping[song])
            elif similarity_mode == 2:
                cur.execute("select without_stopwords_TFIDF_similarity from gensim_similarity where trackID = %s limit 1", ID_mapping[song])
            else:
                cur.execute("select without_stopwords_TFIDF_LSA_similarity from gensim_similarity where trackID = %s limit 1", ID_mapping[song])
            result = cur.fetchone()
            lyrics_similarity_list = json.loads(result[0])

            if tag_mode == 0:
                cur.execute("select all_TFIDF_similarity from gensim_tag_similarity where trackID = %s limit 1", ID_mapping[song])
            else:
                cur.execute("select all_TFIDF_LSA_similarity from gensim_tag_similarity where trackID = %s limit 1", ID_mapping[song])
            result = cur.fetchone()
            tags_similarity_list = json.loads(result[0])

            cur.execute("select itemCF_similarity from song_similarity where trackID = %s limit 1", ID_mapping[song])
            result = cur.fetchone()
            itemCF_similarity_dict = json.loads(result[0])
            itemCF_trackID_set = set()
            for trackID in itemCF_similarity_dict:
                itemCF_trackID_set.add(trackID)
        except Exception as e:
            print(e)

        for i in range(len(lyrics_similarity_list)):
            hybrid_similarity = 0
            if trackID_list[i] in itemCF_trackID_set:
                hybrid_similarity = itemCF_similarity_dict[trackID_list[i]] * a + lyrics_similarity_list[i] * b + tags_similarity_list[i] * (1 - a - b)
            else:
                hybrid_similarity = lyrics_similarity_list[i] * b + tags_similarity_list[i] * (1 - a - b)
            hybrid_similarity_list.append((trackID_list[i], hybrid_similarity))
        
        for trackID, sim in sorted(hybrid_similarity_list, key=lambda x:x[1], reverse=True)[0:K]:
            if trackID == ID_mapping[song]:
                continue
            if trackID in action_songs_set:
                continue
            rank.setdefault(trackID,0)
            rank[trackID] += tmp * sim

    db.close()
    return dict(sorted(rank.items(),key=lambda x:x[1],reverse=True)[0:N])

def get_topPopularSongs():
    topPopularSongs = dict()
    db = pymysql.connect(**config)
    cur = db.cursor()
    cur.execute('use recommenderSystem')
    try:
        cur.execute("select trackID, usersCount from sample_tracks order by usersCount desc")
        results = cur.fetchall()
    except Exception as e:
        print(e)
    db.close()
    for res in results:
        topPopularSongs[res[0]] = res[1]
    return topPopularSongs

# # implementation of popularity-based recommendation algorithm
def Popularity_based_Recommendation(userID, N, ID_mapping, topPopularSongs):
    action_songs = dict()
    action_songs_set = set()
    rank = dict()
    db = pymysql.connect(**config)
    cur = db.cursor()
    cur.execute('use recommenderSystem')
    try:
        cur.execute("select songs from user_songs_test_visible where userID = %s", userID)
        result = cur.fetchone()
        action_songs = json.loads(result[0])
    except Exception as e:
        print(e)
    db.close()
    for song in action_songs:
        action_songs_set.add(ID_mapping[song])

    recommendationCount = 0
    for song in topPopularSongs:
        if recommendationCount == 10:
            break
        if song in action_songs_set:
            continue
        rank[song] = topPopularSongs[song]
        recommendationCount += 1
    return rank

# recommender mode
# 0 —— itemCF recommendation only
# 1 —— lyric-based recommendation only
# 2 —— tag-based recommendation only
# 3 —— hybrid recommendation
# 4 —— popularity-based recommendation

def calculate_Diversity(rank, trackID_list, N, a, b, recommender_mode, similarity_mode, tag_mode):
    recommendation_list_len = len(rank)
    similarity_sum = 0
    db = pymysql.connect(**config)
    cur = db.cursor()
    cur.execute('use recommenderSystem')
    recommendation_list = list(rank.keys())
    if recommender_mode == 0:
        for i in range(len(recommendation_list)):
            try:
                cur.execute("select itemCF_similarity from song_similarity where trackID = %s limit 1", recommendation_list[i])
                result = cur.fetchone()
                itemCF_similarity = json.loads(result[0])
            except Exception as e:
                print(e)
            for j in range(i+1, len(recommendation_list)):
                if recommendation_list[j] in itemCF_similarity:
                    similarity_sum += itemCF_similarity[recommendation_list[j]]
    elif recommender_mode == 1:
        for i in range(len(recommendation_list)):
            try:
                if similarity_mode == 0:
                    cur.execute("select all_TFIDF_similarity from gensim_similarity where trackID = %s limit 1", recommendation_list[i])
                elif similarity_mode == 1:
                    cur.execute("select all_TFIDF_LSA_similarity from gensim_similarity where trackID = %s limit 1", recommendation_list[i])
                elif similarity_mode == 2:
                    cur.execute("select without_stopwords_TFIDF_similarity from gensim_similarity where trackID = %s limit 1", recommendation_list[i])
                else:
                    cur.execute("select without_stopwords_TFIDF_LSA_similarity from gensim_similarity where trackID = %s limit 1", recommendation_list[i])
                result = cur.fetchone()
                lyrics_similarity_list = json.loads(result[0])
            except Exception as e:
                print(e)
            for j in range(i+1, len(recommendation_list)):
                index = trackID_list.index(recommendation_list[j])
                similarity_sum += lyrics_similarity_list[index]
    elif recommender_mode == 2:
        for i in range(len(recommendation_list)):
            try:
                if tag_mode == 0:
                    cur.execute("select all_TFIDF_similarity from gensim_tag_similarity where trackID = %s limit 1", recommendation_list[i])
                else:
                    cur.execute("select all_TFIDF_LSA_similarity from gensim_tag_similarity where trackID = %s limit 1", recommendation_list[i])
                result = cur.fetchone()
                tags_similarity_list = json.loads(result[0])
            except Exception as e:
                print(e)
            for j in range(i+1, len(recommendation_list)):
                index = trackID_list.index(recommendation_list[j])
                similarity_sum += tags_similarity_list[index]
    elif recommender_mode == 3:
        for i in range(len(recommendation_list)):
            try:
                if similarity_mode == 0:
                    cur.execute("select all_TFIDF_similarity from gensim_similarity where trackID = %s limit 1", recommendation_list[i])
                elif similarity_mode == 1:
                    cur.execute("select all_TFIDF_LSA_similarity from gensim_similarity where trackID = %s limit 1", recommendation_list[i])
                elif similarity_mode == 2:
                    cur.execute("select without_stopwords_TFIDF_similarity from gensim_similarity where trackID = %s limit 1", recommendation_list[i])
                else:
                    cur.execute("select without_stopwords_TFIDF_LSA_similarity from gensim_similarity where trackID = %s limit 1", recommendation_list[i])
                result = cur.fetchone()
                lyrics_similarity_list = json.loads(result[0])

                if tag_mode == 0:
                    cur.execute("select all_TFIDF_similarity from gensim_tag_similarity where trackID = %s limit 1", recommendation_list[i])
                else:
                    cur.execute("select all_TFIDF_LSA_similarity from gensim_tag_similarity where trackID = %s limit 1", recommendation_list[i])
                result = cur.fetchone()
                tags_similarity_list = json.loads(result[0])

                cur.execute("select itemCF_similarity from song_similarity where trackID = %s limit 1", recommendation_list[i])
                result = cur.fetchone()
                itemCF_similarity = json.loads(result[0])
            except Exception as e:
                print(e)
            for j in range(i+1, len(recommendation_list)):
                index = trackID_list.index(recommendation_list[j])
                hybrid_similarity = 0
                if recommendation_list[j] in itemCF_similarity:
                    hybrid_similarity = itemCF_similarity[recommendation_list[j]] * a + lyrics_similarity_list[index] * b + tags_similarity_list[index] * (1 - a - b)
                else:
                    hybrid_similarity = lyrics_similarity_list[index] * b + tags_similarity_list[index] * (1 - a - b)
                similarity_sum += hybrid_similarity

    db.close()
    Diversity = 1 - 2 * similarity_sum / float(N * (N - 1))
    return Diversity

def calculate_Novelty(rank):
    popularity_sum = 0
    db = pymysql.connect(**config)
    cur = db.cursor()
    cur.execute('use recommenderSystem')
    recommendation_list = list(rank.keys())
    for song in recommendation_list:
        try:
            cur.execute("select usersCount from sample_tracks where trackID = %s limit 1", song)
            result = cur.fetchone()
            popularity_sum += math.log(1 + result[0] * 1.0)
        except Exception as e:
            print(e)
    db.close()
    return popularity_sum

# calculate evaluation index of recommendation algorithms
# including precision, recall, coverage, diversity and novelty
def Precision_Recall_Coverage_Diversity_Novelty(K, N, a, b, recommender_mode, score_mode, similarity_mode, tag_mode):
    I = 0
    hit = 0
    n_recall = 0
    n_precision = 0
    diversity_sum = 0
    novelty_sum = 0
    coverage = set()
    usersSongs_test_hidden = []
    ID_mapping = dict()
    db = pymysql.connect(**config)
    cur = db.cursor()
    cur.execute('use recommenderSystem')
    try:
        cur.execute('select userID, songs from user_songs_test_hidden')
        usersSongs_test_hidden = cur.fetchall()
        cur.execute('select count(*) from sample_tracks')
        I = cur.fetchone()
        cur.execute('select trackID, songID from sample_tracks')
        results = cur.fetchall()
        for res in results:
            ID_mapping[res[1]] = res[0]
        print('ID_mapping load finished')
    except Exception as e:
        print(e)
    db.close()

    topPopularSongs = get_topPopularSongs()
    with open("trackID_list.txt", "rb") as fp:
        trackID_list = pickle.load(fp)

    userCount = 0
    rank_sum = 0
    for userSongs in usersSongs_test_hidden:
        userCount += 1
        if userCount % 1000 == 0:
            print(userCount)
        action_songs = json.loads(userSongs[1])
        if len(action_songs) < 5:
            continue
        action_songs_set = set()
        for song in action_songs:
            action_songs_set.add(ID_mapping[song])

        if recommender_mode == 0:
            rank = ItemCF_Recommendation(userSongs[0], K, N, score_mode, ID_mapping)
        elif recommender_mode == 1:
            rank = Lyric_based_Recommendation(userSongs[0], K, N, score_mode, ID_mapping, trackID_list, similarity_mode)
        elif recommender_mode == 2:
            rank = Tag_based_Recommendation(userSongs[0], K, N, score_mode, ID_mapping, trackID_list, tag_mode)
        elif recommender_mode == 3:
            rank = Hybrid_Recommendation(userSongs[0], ID_mapping, trackID_list, K, N, a, b, score_mode, similarity_mode, tag_mode)
        else:
            rank = Popularity_based_Recommendation(userSongs[0], N, ID_mapping, topPopularSongs)

        diversity_sum += calculate_Diversity(rank, trackID_list, N, a, b, recommender_mode, similarity_mode, tag_mode)
        novelty_sum += calculate_Novelty(rank)
        rank_set = set(rank.keys())
        rank_sum += len(rank_set)
        coverage = coverage | rank_set
        hit += len(rank_set & action_songs_set)
        n_recall += len(action_songs_set)
        n_precision += N

    print(userCount)
    Precision = hit / float(n_precision)
    Recall = hit / float(n_recall)
    Coverage = len(coverage) / float(I[0])
    F_measure = 2 * Precision * Recall / float(Precision + Recall)
    Diversity = diversity_sum / float(userCount)
    Novelty = novelty_sum / float(rank_sum)
    return [Precision, Recall, F_measure, Coverage, Diversity, Novelty]

# tasteProfile_dataset_to_db("train_triplets.txt")
# calculate_ItemCF_similarity(a = 0.5)
#recommedDic = ItemCF_Recommendation('bd4c6e843f00bd476847fb75c47b4fb430a06856', 10, 10)
#print(recommedDic)
#for k, v in recommedDic.items():
#    print(k,"\t",v)
print('Precision_Recall_Coverage_Diversity_Novelty(K=6,N=10,a=0.7,b=0.3,recommender_mode=3,score_mode=1,similarity_mode=1,tag_mode=1)')
print(Precision_Recall_Coverage_Diversity_Novelty(K=6,N=10,a=0.7,b=0.3,recommender_mode=3,score_mode=1,similarity_mode=1,tag_mode=1))