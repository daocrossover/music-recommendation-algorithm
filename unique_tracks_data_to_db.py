import pymysql

# process unique_tracks.txt and store it into the database
def trackInfo_to_db(dataFile):
	songsInfos = []
	db = pymysql.connect(host="localhost", user="root", password="960513", db="recommenderSystem", use_unicode=True, charset="utf8mb4")
	cur = db.cursor()
	cur.execute('set names utf8mb4')
	cur.execute("set character set utf8mb4")
	cur.execute("set character_set_connection=utf8mb4")
	cur.execute('use recommenderSystem')
	with open(dataFile, 'r', encoding='UTF-8') as openFile:
		for line in openFile:
			thisLine = line.replace('\n', '').split('<SEP>')
			songsInfos.append((thisLine[0], thisLine[1], thisLine[2], thisLine[3]))
	print('songsIDs list load finished')
	try:
		cur.executemany("insert into track_info(trackID,songID,artistName,trackName) values(%s,%s,%s,%s)",songsInfos)
		cur.execute("alter table track_info add primary key (trackID)")
		db.commit()
	except Exception as e:
		print(e)
		db.rollback()
	songsInfos.clear()
	db.close()

trackInfo_to_db("unique_tracks.txt")