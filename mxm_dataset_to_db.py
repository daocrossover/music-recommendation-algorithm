# -*- coding: UTF-8 -*-
# store lyrics(bag of words) with TF-IDF to database
from __future__ import division
import pymysql
import json
import math

def musiXmatch_dataset_to_db(trainFile, testFile):
	wordIDs = {}
	bowList = []
	db = pymysql.connect(host="localhost", user="root", password="960513", db="recommenderSystem", use_unicode=True, charset="utf8")
	cur = db.cursor()
	cur.execute('use recommenderSystem')
	with open(trainFile, 'r', encoding='UTF-8') as openTrainFile:
		for line in openTrainFile:
			if line == '':
				continue
			if line[0] == '#':
				continue
			if line[0] == '%':
				topwords = line.strip()[1:].split(',')
				openTrainFile.close()
				break
		for w in topwords:
			wordIDs[str(topwords.index(w)+1)] = []
			wordIDs[str(topwords.index(w)+1)].append(w)
			wordIDs[str(topwords.index(w)+1)].append(0)
		print(wordIDs)
		print("wordIDs dict finished")

	trainTrackCount = 0
	with open(trainFile, 'r', encoding='UTF-8') as openTrainFile:
		for line in openTrainFile:
			if line == '' or line.strip() == '':
				continue
			if line[0] in ('#', '%'):
				continue
			lineparts = line.strip().split(',')
			trackID = lineparts[0]
			TFDict = dict()
			wordCount = 0
			for wordmap in lineparts[2:]:
				wordID, count = wordmap.split(':')
				wordCount += int(count)
				wordIDs[wordID][1] += 1
			for wordmap in lineparts[2:]:
				wordID, count = wordmap.split(':')
				TFDict[wordID] = int(count) / wordCount
			bowList.append([trackID, TFDict, wordCount, 0])
			trainTrackCount += 1
			if trainTrackCount % 15000 == 0:
				print("Done with %d train songs." % trainTrackCount)
	openTrainFile.close()

	testtrackCount = 0
	with open(testFile, 'r', encoding='UTF-8') as openTestFile:
		for line in openTestFile:
			if line == '' or line.strip() == '':
				continue
			if line[0] in ('#', '%'):
				continue
			lineparts = line.strip().split(',')
			trackID = lineparts[0]
			TFDict = dict()
			wordCount = 0
			for wordmap in lineparts[2:]:
				wordID, count = wordmap.split(':')
				wordCount += int(count)
				wordIDs[wordID][1] += 1
			for wordmap in lineparts[2:]:
				wordID, count = wordmap.split(':')
				TFDict[wordID] = int(count) / wordCount
			bowList.append([trackID, TFDict, wordCount, 1])
			testtrackCount += 1
			if testtrackCount % 15000 == 0:
				print("Done with %d train songs." % testtrackCount)
	openTestFile.close()
	print('bowList finished')

	totalTrackCount = trainTrackCount + testtrackCount
	print(totalTrackCount)
	for v in wordIDs.values():
		if v[1] != 0:
			v[1] = math.log(totalTrackCount / v[1])

	wordIDsList = []
	for k in wordIDs:
		wordIDsList.append((wordIDs[k][0], int(k), wordIDs[k][1]))
	try:
		cur.executemany("insert into words(word,wordID,IDF) values(%s,%s,%s)",wordIDsList)
		db.commit()
	except Exception as e:
		print(e)
		db.rollback()
	wordIDsList.clear()
	print("words dump finished")

	for tup in bowList:
		for k in tup[1]:
			tup[1][k] *= wordIDs[k][1]
			tup[1][k] = round(tup[1][k], 4)
		tup[1] = json.dumps(tup[1])
	try:
		cur.executemany("insert into lyrics(trackID,bow_TFIDF,wordCount,isTest) values(%s,%s,%s,%s)", bowList)
		cur.execute("alter table lyrics add primary key (trackID)")
		db.commit()
	except Exception as e:
		print(e)
	
	print("lyrics dump finished")
	wordIDs.clear()
	bowList.clear()
	db.close()

musiXmatch_dataset_to_db('mxm_dataset_train.txt', 'mxm_dataset_test.txt')