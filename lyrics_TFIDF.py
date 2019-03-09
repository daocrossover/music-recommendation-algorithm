# -*- coding: UTF-8 -*-
from __future__ import division
import pymysql
import numpy as np
import json

config = {
    'host': 'localhost',
    'user': 'root',
    'password': '960513',
    'database': 'recommenderSystem'
}

def cos_similarity(x, y):
	tx = np.array(x)
	ty = np.array(y)
	dot_product = np.sum(tx * ty)
	norm_x = np.sqrt(sum(tx**2))
	norm_y = np.sqrt(sum(ty**2))
	return dot_product / float(norm_x * norm_y)

def bow_to_array(words, bow):
    bowDict = json.loads(bow)
    array = []
    for key in sorted(words.keys()):
        if bowDict.__contains__(str(key)):
            array.append(bowDict[str(key)])
        else:
            array.append(0)
    return array

def caculate_lyrics_similarity():
    songCount = 0
    songsBow = []
    songSimilarity = []
    words = {}
    db = pymysql.connect(**config)
    cur = db.cursor()
    cur.execute("use recommenderSystem")
    cur.execute("select trackID, bow_TFIDF from sample_tracks")
    songsBow = cur.fetchall()
    cur.execute("select wordID, word from words")
    results = cur.fetchall()
    for res in results:
        words[res[0]] = res[1]
    print("songsBow load finished")

    for i in range(3500, len(songsBow)):
        songCount += 1
        similarityDict = dict()
        for j in range(len(songsBow)):
            if songsBow[i][0] != songsBow[j][0]:
                song_i = bow_to_array(words, songsBow[i][1])
                song_j = bow_to_array(words, songsBow[j][1])
                similarityDict[songsBow[j][0]] = round(cos_similarity(song_i, song_j), 5)
        """
        if similarityDict:
            maxSim = max(similarityDict.values())
            for song_j in similarityDict:
                similarityDict[song_j] /= maxSim
                similarityDict[song_j] = round(similarityDict[song_j], 5)
        """
        similarityDictString = json.dumps(similarityDict)
        songSimilarity.append((similarityDictString,songsBow[i][0]))
        print(songCount)
        if songCount == 50:
            try:
                cur.executemany("update song_similarity set lyrics_similarity = %s where trackID = %s", songSimilarity)
                db.commit()
                print('bash update finished')
            except Exception as e:
                print(e)
            songSimilarity.clear()
            songCount = 0

    try:
        cur.executemany("update song_similarity set lyrics_similarity = %s where trackID = %s", songSimilarity)             
        db.commit()
    except Exception as e:
        print(e)
    db.close()
    #songsBow.clear()
    songSimilarity.clear()
    print('lyrics_similarity dump finished')

caculate_lyrics_similarity()