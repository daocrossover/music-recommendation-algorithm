# -*- coding: UTF-8 -*-
import pymysql
import json
import math
import random

config = {
    'host': 'localhost',
    'user': 'root',
    'password': '960513',
    'database': 'recommenderSystem'
}

def sampleTracks_to_train_test_dataset():
	usersSongs = []
	usersSongs_all = {}
	usersSongs_train = {}
	songs_train = set()
	users_train = set()
	usersSongs_test_visible = {}
	usersSongs_test_hidden = {}
	sampleTracks = set()
	db = pymysql.connect(**config)
	cur = db.cursor()
	try:
		cur.execute('use recommenderSystem')
		cur.execute('select userID, songs from user_songs')
		usersSongs = cur.fetchall()
		cur.execute('select songID from sample_tracks')
		results = cur.fetchall()
		for res in results:
			sampleTracks.add(res[0])
	except Exception as e:
		print(e)
	print('db load finish')

	# choose tracks in sample tracks to create train dataset
	# use train dataset to calculate itemCF similarity
	userCount = 0
	for usersongs in usersSongs:
		userCount += 1
		usersSongs_all[usersongs[0]] = {}
		if userCount % 1000 == 0:
			print(userCount)
		songs = json.loads(usersongs[1])
		for song in songs:
			if song in sampleTracks:
				usersSongs_all[usersongs[0]][song] = songs[song]
	
	print('usersSongs_all dict finish')

	keys = list(usersSongs_all.keys())
	for user in keys:
		if usersSongs_all[user] == {}:
			del usersSongs_all[user]
	keys.clear()
	print(len(usersSongs_all))

	usersSongs_all_list = []
	for user in usersSongs_all:
		songsString = json.dumps(usersSongs_all[user])
		usersSongs_all_list.append((user, songsString, len(usersSongs_all[user])))
	# store train dataset into the database
	try:
		cur.execute('create table user_songs_train (userID varchar(50), songs longtext, songsCount int)')
		cur.executemany('insert into user_songs_train(userID, songs, songsCount) values(%s,%s,%s)', usersSongs_all_list)
		db.commit()
	except Exception as e:
		print(e)
	usersSongs_all_list.clear()
	print('train dataset finished')

	# create test_visible dataset and test_hidden dataset
	# test_visible dataset used to recommend, test_hidden dataset used to evaluate
	userCount = 0
	for user in usersSongs_all:
		userCount += 1
		songCount = len(usersSongs_all[user])
		visibleCount = int(math.ceil(songCount / 2.0))
		visibleKeys = random.sample(usersSongs_all[user].keys(), visibleCount)
		hiddenKeys = list(set(usersSongs_all[user].keys()).difference(set(visibleKeys)))
		usersSongs_test_visible[user] = {}
		usersSongs_test_hidden[user] = {}
		for key in visibleKeys:
			songs_visible.add(key)
			usersSongs_test_visible[user][key] = usersSongs_all[user][key]
		for key in hiddenKeys:
			usersSongs_test_hidden[user][key] = usersSongs_all[user][key]

	print('songs_test_visible:',len(songs_visible))		
	usersSongs_all.clear()

	total_songCount = 0
	usersSongs_test_visible_list = []
	for user in usersSongs_test_visible:
		users_test_visible.add(user)
		total_songCount += len(usersSongs_test_visible[user])
		songsString = json.dumps(usersSongs_test_visible[user])
		usersSongs_train_list.append((user, songsString, len(usersSongs_test_visible[user])))
	print('avg_songCount:', total_songCount / float(len(usersSongs_test_visible)))
	# store test dataset into the database
	try:
		cur.execute('create table user_songs_test_visible (userID varchar(50), songs longtext, songsCount int)')
		cur.executemany('insert into user_songs_test_visible(userID, songs, songsCount) values(%s,%s,%s)', usersSongs_test_visible_list)
		db.commit()
	except Exception as e:
		print(e)
	usersSongs_test_visible_list.clear()

	usersSongs_test_hidden_list = []
	for user in usersSongs_test_hidden:
		songsString = json.dumps(usersSongs_test_hidden[user])
		usersSongs_test_hidden_list.append((user, songsString, len(usersSongs_test_hidden[user])))
	try:
		cur.execute('create table user_songs_test_hidden (userID varchar(50), songs longtext, songsCount int)')
		cur.executemany('insert into user_songs_test_hidden(userID, songs, songsCount) values(%s,%s,%s)', usersSongs_test_hidden_list)
		db.commit()
	except Exception as e:
		print(e)
	usersSongs_test_hidden_list.clear()
	usersSongs_train.clear()
	usersSongs_test_visible.clear()
	usersSongs_test_hidden.clear()
	print('train & test dataset finished')

	songsUsers = []
	songsUsers_list = []
	try:
		cur.execute('select trackID, users from sample_tracks')
		songsUsers = cur.fetchall()
	except Exception as e:
		print(e)
	for song in songsUsers:
		commonSet = eval(song[1]).intersection(users_test_visible)
		songsUsers_list.append((repr(commonSet), len(commonSet), song[0]))
	try:
		cur.executemany("update sample_tracks set users = %s, usersCount = %s where trackID = %s", songsUsers_list)
		db.commit()
	except Exception as e:
		print(e)
	print('sample_tracks users update finished')
	db.close()
	
sampleTracks_to_train_test_dataset()