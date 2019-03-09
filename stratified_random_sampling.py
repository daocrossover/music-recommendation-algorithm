# -*- coding: UTF-8 -*-
# create 10000 sample tracks according to the genre proportion 
from __future__ import division
import pymysql
import random

config = {
    'host': 'localhost',
    'user': 'root',
    'password': '960513',
    'database': 'recommenderSystem'
}

# straifiled random sample 
def stratified_random_sampling(output_sample_num):
	songs= []
	genresCount = {}
	genreSongs = {}
	db = pymysql.connect(**config)
	cur = db.cursor()
	try:
		cur.execute('use recommenderSystem')
		cur.execute("select trackID, majorityGenre from sub_tracks")
		songs = cur.fetchall()
	except Exception as e:
		print(e)
	print("songs load finished")
	print(len(songs))
	for song in songs:
		genresCount.setdefault(song[1],0)
		genresCount[song[1]] += 1
		genreSongs.setdefault(song[1],[])
		genreSongs[song[1]].append(song[0])

	# calculate the proportion
	songCount = len(songs)
	sampleCount = 0
	samples = []
	for genre in genresCount:
		genresCount[genre] = round(genresCount[genre] / songCount * output_sample_num)
		sampleCount += genresCount[genre]
	print(genresCount)
	print(sampleCount)

	for genre in genreSongs:
		samples += random.sample(genreSongs[genre], genresCount[genre])
	# store the sample tracks into the database
	try:
		cur.execute("create table sample_tracks like sub_tracks")
		cur.execute("insert into sample_tracks select * from sub_tracks where trackID in %s", [samples])
		cur.execute("alter table sample_tracks add primary key (trackID)")
		db.commit()
	except Exception as e:
		print(e)
	db.close()

stratified_random_sampling(10000)


