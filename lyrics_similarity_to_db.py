# -*- coding: UTF-8 -*-
# use gensim to calculate lyrics similarity between tracks

import logging
import pymysql
import pickle
import numpy
import json
from gensim import corpora, models, similarities
from nltk.corpus import stopwords

config = {
    'host': 'localhost',
    'user': 'root',
    'password': '960513',
    'database': 'recommenderSystem'
}

# vector_mode
# 0 —— topwords 5000
# 1 —— topwords without stopwords

# process the musiXmatch dataset and turn it to a list including lyric list of each track
def mxm_dataset_to_string_list(dataFile, stopWords, sample_IDs_set, trackID_list, songs, vector_mode):
	topwords = []
	songCount = 0
	with open(dataFile, 'r', encoding='UTF-8') as openFile:
		for line in openFile:
			if line == '':
				continue
			if line[0] == '#':
				continue
			if line[0] == '%':
				topwords = line.strip()[1:].split(',')
				continue
			songCount += 1
			lineparts = line.strip().split(',')
			if lineparts[0] in sample_IDs_set:
				trackID_list.append(lineparts[0])
				song = []
				for wordmap in lineparts[2:]:
					wordID, count = wordmap.split(':')
					if vector_mode == 0:
						for i in range(int(count)):
							song.append(topwords[int(wordID) - 1])
					elif vector_mode == 1:
						if topwords[int(wordID) - 1] not in stopWords:
							for i in range(int(count)):
								song.append(topwords[int(wordID) - 1])
				songs.append(song)

def tmp(dataFile, sample_IDs_set, trackID_list):
	songCount = 0
	with open(dataFile, 'r', encoding='UTF-8') as openFile:
		for line in openFile:
			if line == '':
				continue
			if line[0] == '#':
				continue
			if line[0] == '%':
				topwords = line.strip()[1:].split(',')
				continue
			songCount += 1
			lineparts = line.strip().split(',')
			if lineparts[0] in sample_IDs_set:
				trackID_list.append(lineparts[0])

# turn the musiXmatch dataset list to gensim vectors
def mxm_dataset_to_vector(trainFile, testFile, vector_mode):
	stopWords = set(stopwords.words('english'))
	sample_tracks = []
	sample_IDs_set = set()
	trackID_list = []
	songs = []
	db = pymysql.connect(**config)
	cur = db.cursor()
	cur.execute('use recommenderSystem')
	try:
		cur.execute('select trackID from sample_tracks')
		sample_tracks = cur.fetchall()
	except Exception as e:
		print(e)
	for ID in sample_tracks:
		sample_IDs_set.add(ID[0])
	print('sample_tracks IDs load finish')

	mxm_dataset_to_string_list(trainFile, stopWords, sample_IDs_set, trackID_list, songs, vector_mode)
	mxm_dataset_to_string_list(testFile, stopWords, sample_IDs_set, trackID_list, songs, vector_mode)
	print('songs lyrics list construct finish')
	with open("trackID_list.txt", "wb") as fp:
		pickle.dump(trackID_list, fp)

	dictionary = corpora.Dictionary(songs)
	corpus = [dictionary.doc2bow(song) for song in songs]
	if vector_mode == 0:	
		dictionary.save('gensim_storage/songs_lyrics_all.dict')
		corpora.MmCorpus.serialize('gensim_storage/songs_lyrics_all.mm', corpus)
	elif vector_mode == 1:
		dictionary.save('gensim_storage/songs_lyrics_without_stopwords.dict')
		corpora.MmCorpus.serialize('gensim_storage/songs_lyrics_without_stopwords.mm', corpus)
	print(dictionary)
	#print(corpus)

# calculate the lyric similarity matrix
def gensim_lyrics_similarity():
	logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

	# topwords 5000 TF-IDF without LSA MatrixSimilarity
	dictionary = corpora.Dictionary.load('gensim_storage/songs_lyrics_all.dict')
	corpus = corpora.MmCorpus('gensim_storage/songs_lyrics_all.mm')
	tfidf = models.TfidfModel(corpus)
	corpus_tfidf = tfidf[corpus]
	index = similarities.MatrixSimilarity(corpus_tfidf)
	index.save('gensim_storage/songs_lyrics_all.index')

	# topwords 5000 TF-IDF with LSA MatrixSimilarity
	lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=300)
	#lsi.print_topics(300)
	corpus_lsi = lsi[corpus_tfidf]
	index1 = similarities.MatrixSimilarity(corpus_lsi)
	index1.save('gensim_storage/songs_lyrics_all_LSA.index')

	# topwords 5000 without stopwords TF-IDF without LSA MatrixSimilarity
	dictionary = corpora.Dictionary.load('gensim_storage/songs_lyrics_without_stopwords.dict')
	corpus = corpora.MmCorpus('gensim_storage/songs_lyrics_without_stopwords.mm')
	tfidf = models.TfidfModel(corpus)
	corpus_tfidf = tfidf[corpus]
	index2 = similarities.MatrixSimilarity(corpus_tfidf)
	index2.save('gensim_storage/songs_lyrics_without_stopwords.index')

	# topwords 5000 without stopwords TF-IDF with LSA MatrixSimilarity
	lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=300)
	#lsi.print_topics(300)
	corpus_lsi = lsi[corpus_tfidf]
	index3 = similarities.MatrixSimilarity(corpus_lsi)
	index3.save('gensim_storage/songs_lyrics_without_stopwords_LSA.index')

# similarity_mode
# 0 —— all 5000 topwords TF-IDF similarities
# 1 —— all 5000 topwords TF-IDF with LSA similarities
# 2 —— 5000 topwords without stopwords TF-IDF similarities
# 3 —— 5000 topwords without stopwords TF-IDF with LSA similarities

# store lyric similarity matrix produced by gensim into the database
def gensim_lyrics_similarity_to_db(similarity_mode):
	with open("trackID_list.txt", "rb") as fp:
		trackID_list = pickle.load(fp)
	similarity_list = []
	if similarity_mode == 0:
		index = similarities.MatrixSimilarity.load('gensim_storage/songs_lyrics_all.index')
	elif similarity_mode == 1:
		index = similarities.MatrixSimilarity.load('gensim_storage/songs_lyrics_all_LSA.index')
	elif similarity_mode == 2:
		index = similarities.MatrixSimilarity.load('gensim_storage/songs_lyrics_without_stopwords.index')
	elif similarity_mode == 3:
		index = similarities.MatrixSimilarity.load('gensim_storage/songs_lyrics_without_stopwords_LSA.index')
	else:
		print('input similarity_mode error')
	i = 0
	if similarity_mode == 0: 
		for sim in index:
			simString = json.dumps(sim.tolist())
			similarity_list.append((trackID_list[i], simString))
			i += 1
	else:
		for sim in index:
			simString = json.dumps(sim.tolist())
			similarity_list.append((simString, trackID_list[i]))
			i += 1		

	print('similarity_list construct finished')
	db = pymysql.connect(**config)
	cur = db.cursor()
	cur.execute('use recommenderSystem')
	try:
		if similarity_mode == 0:
			cur.executemany("insert into gensim_similarity(trackID, all_TFIDF_similarity) values(%s,%s)", similarity_list)
		elif similarity_mode == 1:
			cur.executemany("update gensim_similarity set all_TFIDF_LSA_similarity = %s where trackID = %s", similarity_list)
		elif similarity_mode == 2:
			cur.executemany("update gensim_similarity set without_stopwords_TFIDF_similarity = %s where trackID = %s", similarity_list)
		else:
			cur.executemany("update gensim_similarity set without_stopwords_TFIDF_LSA_similarity = %s where trackID = %s", similarity_list)
		db.commit()
	except Exception as e:
		print(e)
	db.close()
	print('similarity insert finished')

mxm_dataset_to_vector('Dataset/mxm_dataset_train.txt', 'Dataset/mxm_dataset_test.txt', 0)
mxm_dataset_to_vector('Dataset/mxm_dataset_train.txt', 'Dataset/mxm_dataset_test.txt', 1)
gensim_lyrics_similarity()
gensim_lyrics_similarity_to_db(3)

"""
sample_IDs_set = set()
trackID_list = []
songs = []
db = pymysql.connect(**config)
cur = db.cursor()
cur.execute('use recommenderSystem')
try:
	cur.execute('select trackID from sample_tracks')
	sample_tracks = cur.fetchall()
except Exception as e:
	print(e)
db.close()
for ID in sample_tracks:
	sample_IDs_set.add(ID[0])
print('sample_tracks IDs load finish')
tmp('Dataset/mxm_dataset_train.txt', sample_IDs_set, trackID_list)
tmp('Dataset/mxm_dataset_test.txt', sample_IDs_set, trackID_list)
with open("trackID_list.txt", "wb") as fp:
	pickle.dump(trackID_list, fp)
"""