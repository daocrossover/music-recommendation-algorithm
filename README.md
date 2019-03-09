# Music-Recommendation-Algorithm
Design and implementation of music recommendation algorithms

## Dataset：Million Song Dataset(MSD)

- train_triplets.txt
	* MSD Taste Profile subset数据集，用于协同过滤推荐算法

- mxm_dataset_train.txt和mxm_dataset_test.txt
	* MSD musiXmatch dataset数据集，用于基于歌词推荐算法

- lastfm_train和lastfm_test
	* 包含MSD Last.fm dataset数据集，用于基于标签的推荐算法

- msd_tagtraum_cd1.cls和msd_tagtraum_cd2.cls
	* MSD tagtraum genre annotations数据集，包含genre信息

- unique_tracks.txt
	* 包含MSD trackID和Echo Nest songID的对应关系以及歌曲名信息和艺术家信息。

## Main files

- construct_train_test_dataset.py:
	* 过滤user_songs数据库表中每个用户听过的歌曲（只包含sample tracks的那10000首），将信息重新存入user_songs_train表中。
	* 以1：1的比例将user_songs_train分成user_songs_test_visible和user_songs_test_hidden数据库表。
	* user_songs_test_visible用于给用户进行推荐，user_songs_test_hidden用于音乐推荐算法评测指标的计算。

- lyrics_similarity_to_db.py:
	* 读取musiXmatch dataset数据库，利用gensim库计算歌词的四种相似度矩阵，并将其存储在gensim_storage文件夹中，再将相似度矩阵存入到gensim_similarity数据库表中。

- stratified_random_sampling.py:
	* 根据genre信息，将MSD各个子数据集交集生成的歌曲进行随机分层抽样，最后生成10000首歌曲存入sample_tracks数据库表中。

- tags_similarity_to_db.py:
	* 读取Last.fm dataset数据库，利用gensim库计算标签的两种相似度矩阵，并将其存储在gensim_storage文件夹中，再将相似度矩阵存入到gensim_tag_similarity数据库表中。

- tagtraum_genre_dataset_to_db.py:
	* 读取tagtraum genre annotations数据集到genre_info数据库表中。

- tasteProfile_dataset_to_db.py:
	* appendData和tasteProfile_dataset_to_db函数用于读取Taste Profile subset数据集到user_songs和song_users数据库表中。
	* caculate_ItemCF_similarity函数用户基于物品的协同过滤算法相似度的计算，并且将它存入到song_similarity数据库表中。
	* ItemCF_Recommendation、Lyric_based_Recommendation、Tag_based_Recommendation、Hybrid_Recommendation和Popularity_based_Recommendation函数为基于物品的协同过滤算法、基于歌词推荐算法、基于标签推荐算法、混合推荐算法和基于流行度推荐算法的实现。
	* Precision_Recall_Coverage_Diversity_Novelty为音乐推荐算法评测指标的计算实现。

- unique_tracks_data_to_db.py:
	* 读取unique.txt数据集到track_info数据库表中。

- trackID_list.txt:
	* sample_tracks中的10000首歌曲的trackID list的存储。