# _*_ coding: utf-8 _*_

#p3# python3用

import tweepy
import sys
import urllib
#p3#import urllib.request
import os
import datetime
import time
import json

# 認証
twitter_conf = {
    'consumer' : {
        'key'    : "",
        'secret' : ""
    },
    'access'   : {
        'key'    : "",
        'secret' : ""
    }
}
auth = tweepy.OAuthHandler(
    twitter_conf['consumer']['key'],
    twitter_conf['consumer']['secret'])
auth.set_access_token(
    twitter_conf['access']['key'],
    twitter_conf['access']['secret'])

api = tweepy.API(auth)


my_id = [ '' , '' ]
# my_id_select = リストmy_idより作業IDを格納する一時変数
# tmp_id = api.friends_idsからmy_friends_idsへ格納するときの一時変数
my_friends_ids = []		#フォローしているIDとスクリーン名
my_friends_list = {}	#
# i = len(my_friends_ids) , maxid格納するときの一時変数
# tmp_user = 何用？
# follow_id = フォローしてるid
# follow_screen = フォローしてるスクリーン名
# err = エラー
# f = ファイル
# l = 16*200の16
# twi = TL
tmp_count = 0
tmp_count2 = 0


def limit_handled(h):
	while True:
		try:
			yield h.next()
		except tweepy.RateLimitError, err:
		#p3#except tweepy.RateLimitError as err:
			print str(datetime.datetime.now()) + ": RateLimitError_1: " + str(err)
			#p3#print(str(datetime.datetime.now()) + ": RateLimitError_1: " + str(err))
			with open(working_directory + "/_log.txt",'a') as f:
				f.write(str(datetime.datetime.now()) + ": RateLimitError_1: " + str(err) + "\n")
			time.sleep(60 * 15)
		except tweepy.TweepError, err:
		#p3#except tweepy.TweepError as err:
			print str(datetime.datetime.now()) + ": TweepError_1: " + str(err)
			#p3#print(str(datetime.datetime.now()) + ": TweepError_1: " + str(err))
			with open(working_directory + "/_log.txt",'a') as f:
				f.write(str(datetime.datetime.now()) + ": TweepError_1: " + str(err) + "\n")
			time.sleep(60 * 15)



def new_follow_ids_json(my_friends_list_def):
	# 新規フォロー用初期化
	json_file = open(working_directory + "/_my_friends_list.json",'r')
	my_friends_list_json = json.load(json_file)
	json_file.close()
	for follow_id,follow_screen in my_friends_list_def.items():
		if my_friends_list_json.has_key(follow_id) == False:
		#if follow_id not in my_friends_list_json:
			my_friends_list_json[follow_id] = follow_screen
			os.makedirs(working_directory + "/" + follow_id)
			f = open(working_directory + "/" + follow_id + "/_maxid.txt" , 'w+')
			f.close()
	json_file = open(working_directory + "/_my_friends_list.json",'w')
	json_file.write(my_friends_list_json)
	json_file.close()


def tweet_id_get():
	# 取得開始のツイートIDをmaxidへいれる
	# tmp_countはAPIエラー時のMAXID確認用フラグ
	# ./my_id_select/follow_id/_maxid.txtに前回実行時のMAXIDを記録している
	# ここ以下のAPIは鍵アカだと取得できないので対ループ用にtmp_countを使用
	tmp_count = 0
	json_file = open(working_directory + "/_my_friends_list.json",'r')
	my_friends_list_json = json.load(json_file)
	json_file.close()
	
	for follow_id,follow_screen in my_friends_list_json.items():
		# 新規 ->maxidを取得し_maxid.txtファイルへ。クエリはmax_search
		if os.path.getsize(working_directory + "/" + follow_id + "/_maxid.txt") == 0:
			query = 'max_search'
			try:
				maxid = api.user_timeline(follow_id).max_id
			# API対策
			except tweepy.RateLimitError, err:
			#p3#except tweepy.RateLimitError as err:
				print str(datetime.datetime.now()) + ": " + str(follow_id) + ": RateLimitError_3: " + str(err)
				#p3#print(str(datetime.datetime.now()) + ": " + str(follow_id) + ": RateLimitError_3: " + str(err))
				with open(working_directory + "/_log.txt",'a') as f:
					f.write(str(datetime.datetime.now()) + ": " + str(follow_id) + ": RateLimitError_3: " + str(err) + "\n")
				time.sleep(60 * 15)
				continue
			# その他、鍵アカ対策
			except tweepy.TweepError, err:
			#p3#except tweepy.TweepError as err:
				print str(datetime.datetime.now()) + ": " + str(follow_id) + ": TweepError_3: " + str(err)
				#p3#print(str(datetime.datetime.now()) + ": " + str(follow_id) + ": TweepError_3: " + str(err))
				with open(working_directory + "/_log.txt",'a') as f:
					f.write(str(datetime.datetime.now()) + ": " + str(follow_id) + ": TweepError_3: " + str(err) + "\n")
				tmp_count = tmp_count +1
				if tmp_count < 3:
					time.sleep(60 * 5)
					continue
				else:
					tmp_count = 0
			tmp_count = 0
			f = open(working_directory + "/" + follow_id + "/_maxid.txt" , 'w')
			f.write(str(maxid))
			f.close()
		# 既存 ->maxidに_maxid.txt、クエリはsince_search
		else:
			f = open(working_directory + "/" + follow_id + "/_maxid.txt" , 'r')
			for i in f: maxid = i
			f.close()
			query = 'since_search'
		media_get(query, follow_id)



def media_get(query_def, follow_id_def_def):
	# 画像取得
	# tmp_count2は3回まで再試行する用
	tmp_count = 0
	tmp_count2 = 0

	for l in range(16):
		#02-1 TLを取得_API
		try:
			#02のチェック後半
			if query_def == 'max_search':
				#03-1
				for twi in api.user_timeline(follow_id_def, count=500, max_id=maxid):
					# リツイート判断
					if hasattr(twi, 'retweeted_status') is False:
						# 画像保存
						if hasattr(twi, "extended_entities"):
							if 'media' in twi.extended_entities:
								for media in twi.extended_entities["media"]:
									if media["type"] == 'photo':
										dl_filename = media["media_url"]
										dl_media = dl_filename + ":orig"
									if media["type"] == 'animated_gif':
										dl_media = media["video_info"]["variants"][0]["url"]
										dl_filename = dl_media
									if media["type"] == 'video':
										dl_media = media["video_info"]["variants"][0]["url"]
										if '.m3u8' in dl_media:
											dl_media = media["video_info"]["variants"][1]["url"]
										if '?tag=3' in dl_media:
											dl_media = dl_media.replace("?tag=3", "")
										dl_filename = dl_media
									try:
										with open(working_directory + "/" + follow_id_def + "/" + os.path.basename(dl_filename), 'wb') as f:
											dl_file = urllib.urlopen(dl_media).read()
											#dl_file = urllib.request.urlopen(dl_media).read()
											f.write(dl_file)
									except Exception as err:
										print(str(datetime.datetime.now()) + str(follow_id_def) + ": 03-1: " + str(dl_media) + ": TC=" + str(tmp_count2) + ": " + str(err))
										with open(working_directory + "/_log.txt",'a') as f:
											f.write(str(datetime.datetime.now()) + str(follow_id_def) + ": 03-1: " + str(dl_media) + ": TC=" + str(tmp_count2) + ": " + str(err) + "\n")
										tmp_count2 = tmp_count2 +1
										if tmp_count2 < 3:
											time.sleep(60)
											continue
										else:
											tmp_count2 = 0
									except:
										# 不具合発生中
										print(str(datetime.datetime.now()) + str(follow_id_def) + ": !!!fail!!!")
										with open(working_directory + "/_log.txt",'a') as f:
											f.write(str(datetime.datetime.now()) + str(follow_id_def) + ": 03-1: " + str(dl_media) + ": TC=" + str(tmp_count2) + ": " + str(err) + "\n")
										tmp_count2 = tmp_count2 +1
										if tmp_count2 < 3:
											time.sleep(60)
											continue
										else:
											tmp_count2 = 0
									tmp_count2 = 0
					maxid = twi.id
				#03-1 終了
			elif query_def == 'since_search':
				#03-2
				for twi in api.user_timeline(follow_id_def, count=500, since_id=maxid):
					#リツイート判断
					if hasattr(twi, 'retweeted_status') is False:
						# 画像保存
						if hasattr(twi, "extended_entities"):
							if 'media' in twi.extended_entities:
								for media in twi.extended_entities["media"]:
									if media["type"] == 'photo':
										dl_filename = media["media_url"]
										dl_media = dl_filename + ":orig"
									if media["type"] == 'animated_gif':
										dl_media = media["video_info"]["variants"][0]["url"]
										dl_filename = dl_media
									if media["type"] == 'video':
										dl_media = media["video_info"]["variants"][0]["url"]
										if '.m3u8' in dl_media:
											dl_media = media["video_info"]["variants"][1]["url"]
										if '?tag=3' in dl_media:
											dl_media = dl_media.replace("?tag=3", "")
										dl_filename = dl_media
									try:
										with open(working_directory + "/" + follow_id_def + "/" + os.path.basename(dl_filename), 'wb') as f:
											dl_file = urllib.urlopen(dl_media).read()
											#dl_file = urllib.request.urlopen(dl_media).read()
											f.write(dl_file)
									except Exception as err:
									#except Exception as err:
										print str(datetime.datetime.now()) + str(follow_id_def) + ": 03-2: " + str(dl_media) + ": TC=" + str(tmp_count2) + ": " + str(err)
										#print(str(datetime.datetime.now()) + str(follow_id_def) + ": 03-2: " + str(dl_media) + ": TC=" + str(tmp_count2) + ": " + str(err))
										with open(working_directory + "/_log.txt",'a') as f:
											f.write(str(datetime.datetime.now()) + str(follow_id_def) + ": 03-2: " + str(dl_media) + ": TC=" + str(tmp_count2) + ": " + str(err) + "\n")
										tmp_count2 = tmp_count2 +1
										if tmp_count2 < 3:
											time.sleep(60)
											continue
										else:
											tmp_count2 = 0
									except:
										# 不具合発生中
										print str(datetime.datetime.now()) + str(follow_id_def) + ": !!!fail!!!"
										#print(str(datetime.datetime.now()) + str(follow_id_def) + ": !!!fail!!!")
										with open(working_directory + "/_log.txt",'a') as f:
											f.write(str(datetime.datetime.now()) + str(follow_id_def) + ": 03-2: " + str(dl_media) + ": TC=" + str(tmp_count2) + ": " + str(err) + "\n")
										tmp_count2 = tmp_count2 +1
										if tmp_count2 < 3:
											time.sleep(60)
											continue
										else:
											tmp_count2 = 0
									tmp_count2 = 0
					maxid = twi.id
				#03-2 終了
				with open(working_directory + "/" + follow_id_def + "/_maxid.txt", 'w+') as f:
					f.write(str(maxid))
		#02-2
		except tweepy.RateLimitError, err:
		#except tweepy.RateLimitError as err:
			with open(working_directory + "/_log.txt",'a') as f:
				f.write(str(datetime.datetime.now()) + str(follow_id_def) + ": RateLimitError_4: " + str(maxid) + ": TC=" + str(tmp_count2) + ": " + str(err) + "\n")
			time.sleep(60 * 15)
			continue
		#02-3
		except tweepy.TweepError, err:
		#except tweepy.TweepError as err:
			print str(datetime.datetime.now()) + str(follow_id_def) + ": TweepError_4: " + str(maxid) + ": TC=" + str(tmp_count2) + ": " + str(err)
			#print(str(datetime.datetime.now()) + str(follow_id_def) + ": TweepError_4: " + str(maxid) + ": TC=" + str(tmp_count2) + ": " + str(err))
			with open(working_directory + "/_log.txt",'a') as f:
				f.write(str(datetime.datetime.now()) + str(follow_id_def) + ": TweepError_4: " + str(maxid) + ": TC=" + str(tmp_count2) + ": " + str(err) + "\n")
			tmp_count2 = tmp_count2 +1
			if tmp_count2 < 3:
				time.sleep(60 * 5)
				continue
			else:
				tmp_count2 = 0
		tmp_count2 = 0



# プログラムを実行しているパスを取得
file_path = os.getcwd()
# working_directory = file_path + "/" + my_id_select


### 初期化・ユーザIDチェック

for my_id_select in my_id:
	working_directory = file_path + "/" + my_id_select
	# ユーザディレクトリチェック
	if os.path.exists(working_directory) == False:
		os.makedirs(working_directory)
	# ログファイル作成
	with open(working_directory + "/_log.txt",'w+') as f:
		f.write(str(datetime.datetime.now()) + ": start: " + str(my_id_select) + "\n")
	
	
	# my_id_selectのフォローしたIDをmy_friends_idsに取得
	# Cursor使うとすべて取ってきてくれるが，配列ではなくなるので配列に入れる
	for tmp_id in limit_handled(tweepy.Cursor(api.friends_ids, id=my_id_select).items()):
		my_friends_ids.append(tmp_id)
	# 100IDsずつ詳細をmy_friends_listへ
	# tmp_countはフォロー数カウンター、tmp_count2はエラー時のiチェック
	tmp_count = 0
	tmp_count2 = 0
	for i in range(0, len(my_friends_ids), 100):
		try:
			for tmp_user in api.lookup_users(user_ids=my_friends_ids[i:i+100]):
				tmp_count = tmp_count + 1
				my_friends_list[unicode(tmp_user.screen_name)] = unicode(tmp_user.name)
				#p3#my_friends_list[tmp_user.screen_name] = tmp_user.name
		except tweepy.RateLimitError, err:
		#p3#except tweepy.RateLimitError as err:
			print str(datetime.datetime.now()) + ": RateLimitError_2: " + str(err)
			#p3#print(str(datetime.datetime.now()) + ": RateLimitError_2: " + str(err))
			with open(working_directory + "/_log.txt",'a') as f:
				f.write(str(datetime.datetime.now()) + ": RateLimitError_2: " + str(err) + "\n")
			time.sleep(60 * 15)
			continue
		except tweepy.TweepError, err:
		#p3#except tweepy.TweepError as err:
			print str(datetime.datetime.now()) + ": TweepError_2: " + str(err)
			#p3#print(str(datetime.datetime.now()) + ": TweepError_2: " + str(err))
			with open(working_directory + "/_log.txt",'a') as f:
				f.write(str(datetime.datetime.now()) + ": TweepError_2: " + str(err) + "\n")
			time.sleep(60 * 15)
			continue
	print str(datetime.datetime.now()) + ": " + str(len(my_friends_ids)) + "/" + str(tmp_count)
	#p3#print(str(datetime.datetime.now()) + ": " + str(len(my_friends_ids)) + "/" + str(tmp_count))
	with open(working_directory + "/_log.txt",'a') as f:
		f.write(str(datetime.datetime.now()) + ": " + str(len(my_friends_ids)) + "/" + str(tmp_count) + "\n")

	# _my_friends_ids.jsonが無ければ作成
	if os.path.exists(file_path + "/_my_friends_ids.json") == False:
		with open(file_path + "/_my_friends_ids.json",'w+') as f:
			f.write(my_friends_ids)
	# _my_friends_list.jsonが無ければ作成
	if os.path.exists(file_path + "/_my_friends_list.json") == False:
		with open(file_path + "/_my_friends_list.json",'w+') as f:
			f.write(my_friends_list)

	# 新規フォローIDをjsonに保存
	new_follow_ids_json(my_friends_list)

	# ツイートIDの取得
	tweet_id_get()

	my_friends_list.clear()
	my_friends_list_json.clear()
	my_friends_ids = []
