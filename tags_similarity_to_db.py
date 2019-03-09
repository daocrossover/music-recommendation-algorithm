# -*- coding: UTF-8 -*-
# use gensim to calculate tags similarity between tracks
import logging
import pickle
import simplejson
import os
import pymysql
import numpy
from gensim import corpora, models, similarities
from nltk.corpus import stopwords

config = {
    'host': 'localhost',
    'user': 'root',
    'password': '960513',
    'database': 'recommenderSystem'
}

# process the Last.fm dataset(read json files) and turn it to a list including tag list of each track
def read_json_files(path, count, songs, tag_dict, sample_IDs_set):
	stopWords = set(stopwords.words('english'))
	for root,dirs,files in os.walk(path):
		for file in files:
			if count == 9998:
				break
			trackID = file[:-5]
			if trackID in sample_IDs_set:
				count += 1
				song = []
				with open(os.path.join(root,file), "r") as fp:
					r_load = simplejson.load(fp)
					tags = r_load["tags"]
					for tag in tags[0:5]:
						if tag[0] not in stopWords:
							song.append(tag[0])
							if tag[0] in tag_dict:
								tag_dict[tag[0]] += 1
							else:
								tag_dict[tag[0]] = 1
				songs.append((trackID, song))

# process both train dataset and test dataset and combine them	
def get_tags_from_json():
	sample_IDs_set = set()
	tag_dict = dict()
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

	count = 0
	songs = []
	read_json_files('E:/Recommender System/Dataset/lastfm_test/', count, songs, tag_dict, sample_IDs_set)
	read_json_files('E:/Recommender System/Dataset/lastfm_train/', count, songs, tag_dict, sample_IDs_set)
	print(len(tag_dict))
	with open('topTags.txt', 'w') as f:
		for tag in sorted(tag_dict.items(), key=lambda x:x[1], reverse=True)[0:20]:
			f.write(tag[0] + '\t' + str(tag[1]) + '\n')
	tracks = []
	for song in sorted(songs, key=lambda x:x[0]):
		tracks.append(song[1])
	print(tracks[0:10])
	return tracks

# turn the Last.fm dataset list to gensim vectors
def tags_to_vector():
	trackID_list = []
	songs = get_tags_from_json()
	dictionary = corpora.Dictionary(songs)
	corpus = [dictionary.doc2bow(song) for song in songs]
	dictionary.save('gensim_storage/songs_tags.dict')
	corpora.MmCorpus.serialize('gensim_storage/songs_tags.mm', corpus)
	print(dictionary)

# tag mode
# 0 —— all tags TF-IDF similarities
# 1 —— all tags TF-IDF with LSA similarities

# calculate the tag similarity matrix
def gensim_tags_similarity():
	logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

	# all tags TF-IDF without LSA MatrixSimilarity
	dictionary = corpora.Dictionary.load('gensim_storage/songs_tags.dict')
	corpus = corpora.MmCorpus('gensim_storage/songs_tags.mm')
	tfidf = models.TfidfModel(corpus)
	corpus_tfidf = tfidf[corpus]
	index = similarities.MatrixSimilarity(corpus_tfidf)
	index.save('gensim_storage/songs_tags.index')

	# all tags TF-IDF with LSA MatrixSimilarity
	lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=300)
	#lsi.print_topics(300)
	corpus_lsi = lsi[corpus_tfidf]
	index1 = similarities.MatrixSimilarity(corpus_lsi)
	index1.save('gensim_storage/songs_tags_LSA.index')

# store tag similarity matrix produced by gensim into the database
def gensim_tags_similarity_to_db(similarity_mode):
	with open("trackID_list.txt", "rb") as fp:
		trackID_list = pickle.load(fp)
	similarity_list = []
	if similarity_mode == 0:
		index = similarities.MatrixSimilarity.load('gensim_storage/songs_tags.index')
	elif similarity_mode == 1:
		index = similarities.MatrixSimilarity.load('gensim_storage/songs_tags_LSA.index')

	i = 0
	if similarity_mode == 0: 
		for sim in index:
			simString = simplejson.dumps(sim.tolist())
			similarity_list.append((trackID_list[i], simString))
			i += 1
	else:
		for sim in index:
			simString = simplejson.dumps(sim.tolist())
			similarity_list.append((simString, trackID_list[i]))
			i += 1
	print('similarity_list construct finished')

	db = pymysql.connect(**config)
	cur = db.cursor()
	cur.execute('use recommenderSystem')
	try:
		if similarity_mode == 0:
			cur.executemany("insert into gensim_tag_similarity(trackID, all_TFIDF_similarity) values(%s,%s)", similarity_list)
		else:
			cur.executemany("update gensim_tag_similarity set all_TFIDF_LSA_similarity = %s where trackID = %s", similarity_list)
		db.commit()
	except Exception as e:
		print(e)
	db.close()
	print('similarity insert finished')

get_tags_from_json()
tags_to_vector()
gensim_tags_similarity()
gensim_tags_similarity_to_db(0)
gensim_tags_similarity_to_db(1)