import pymysql

# process the tagtraum genre annotations and store it into the database
def tagtraum_genre_dataset_to_db(dataFile):
	genreInfos = []
	db = pymysql.connect(host="localhost", user="root", password="960513", db="recommenderSystem")
	cur = db.cursor()
	cur.execute('use recommenderSystem')
	with open(dataFile, 'r') as openFile:
		for line in openFile:
			if line[0] == '#':
				continue
			thisLine = line.replace('\n', '').split('\t')
			if len(thisLine) == 2:
				thisLine.append('')
			genreInfos.append(thisLine)
	print('genreInfos list load finished')
	try:
		cur.executemany("insert into genre_info(trackID, majorityGenre, minorityGenre) values(%s,%s,%s)",genreInfos)
		cur.execute("alter table genre_info add primary key (trackID)")
		db.commit()
	except Exception as e:
		print(e)
		db.rollback()
	genreInfos.clear()
	db.close()

tagtraum_genre_dataset_to_db("msd_tagtraum_cd2.cls")