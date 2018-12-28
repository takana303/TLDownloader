#!/usr/bin python3
# _*_ coding: utf-8 _*_

from time import sleep
import datetime
import filecmp
import glob
import json
import os
import requests
import shutil
import subprocess
import sys
import tweepy
import urllib.request
import argparse
import re
import csv



### 認証 ###
def tweepy_api():
	twitter_conf = {
		'consumer' : {
			'key'   : "",
			'secret' : ""
		},
		'access'   : {
			'key'   : "",
			'secret' : ""
		}
	}
	auth = tweepy.OAuthHandler(
		twitter_conf['consumer']['key'],
		twitter_conf['consumer']['secret'])
	auth.set_access_token(
		twitter_conf['access']['key'],
		twitter_conf['access']['secret'])
	tweepy_auth = tweepy.API(auth)
	return(tweepy_auth)



### user object ###

def _twitter_userobject_get(SCREEN_NAME):
	errcount = 0
	USER_OBJECT = ""
	def _get_description():
		nonlocal errcount
		nonlocal USER_OBJECT
		try:
			USER_OBJECT = api.get_user(SCREEN_NAME)
		except Exception as err:
			if errcount < 2:
				errcount = errcount + 1
				err_subject = SCREEN_NAME + " : _twitter_userobject_get"
				_log(err_subject, err)
				sleep(60)
				_get_description()
	_get_description()
	return USER_OBJECT



### URL get ###

def _description_urls(USER_DESCRIPTION):
	DESCURLS = []
	pattern = re.compile("http[!-~]+")
	SHORTURL = re.findall(pattern, USER_DESCRIPTION)
	for d in SHORTURL:
		try:
			DESCURL = (urllib.request.urlopen(d,timeout=3).geturl())
			DESCURLS.extend(DESCURL)
		except Exception as err:
			err_subject = DESCURL + " : "
			_log(err_subject, err)
			DESCURLS.extend(d)
			sleep(30)
	return DESCURLS

def _url_get():
	for i, USER in enumerate(json_dict):
		URLS = []
		USER_OBJECT = _twitter_userobject_get(USER["name"])
		USER_URL = USER_OBJECT.entities
		USER_DESCRIPTION = USER_OBJECT.description
		CHANNEL_ID = ""
		if "url" in USER_URL:
			URLS.extend(USER_URL["url"]["urls"][0]["expanded_url"])
		URLS.extend(_description_urls(USER_DESCRIPTION))
		json_dict[i]["urls"] = URLS



### TL chech ###

def _TL_search():
	def _TL_hashtag_check(hashcheck_object):
		nonlocal hashtag_tmp
		nonlocal hashtag_2csv
		if hasattr(hashcheck_object, "retweeted_status"):
			if "hashtags" in hashcheck_object.retweeted_status.entities:
				for x in hashcheck_object.retweeted_status.entities["hashtags"]:
					if x["text"] not in hashtag_tmp and x["text"] not in hashtag_2csv and x["text"] not in json_dict:
						hashtag_tmp.append(x["text"])
		elif hasattr(hashcheck_object, "quoted_status"):
			if "hashtags" in hashcheck_object.quoted_status.entities:
				for y in hashcheck_object.quoted_status.entities["hashtags"]:
					if y["text"] not in hashtag_tmp and y["text"] not in hashtag_2csv and y["text"] not in json_dict:
						hashtag_tmp.append(y["text"])
		else:
			if "hashtags" in hashcheck_object.entities:
				for z in hashcheck_object.entities["hashtags"]:
					if z["text"] not in hashtag_tmp and z["text"] not in hashtag_2csv and z["text"] not in json_dict:
						hashtag_tmp.append(z["text"])

	def _get_tweetid():
		nonlocal TL_search_fault_count
		try:
			get_id = api.user_timeline(TL_search_object["name"]).max_id
			return get_id
		except tweepy.RateLimitError as err_description:
			if TL_search_fault_count < 2:
				TL_search_fault_count = TL_search_fault_count + 1
				err_subject = TL_search_object["name"] + " : RateLimitError_TL_search"
				_log(err_subject, err_description)
				sleep(60 * 15)
				_get_tweetid()
		except Exception as err_description:
			if TL_search_fault_count < 2:
				TL_search_fault_count = TL_search_fault_count + 1
				err_subject = TL_search_object["name"] + " : Exception_TL_search"
				_log(err_subject, err_description)
				sleep(60)
				_get_tweetid()
	def _TL_tweet_get():
		nonlocal TL_tweet_get_fault_count
		nonlocal TL_search_object
		nonlocal search_flag

		try:
			if search_flag == 'max_search':
				for tl_object in api.user_timeline(TL_search_object["name"], count=100, max_id=TL_search_object["TLflag"]["id"]):
					_download(tl_object, TL_search_object["name"], TL_search_object["RTflag"], TL_search_object["gifflag"], TL_search_object["videoflag"])
					_TL_hashtag_check(tl_object)
					TL_search_object["TLflag"]["id"] = tl_object.id
					TL_tweet_get_fault_count = 0
			elif search_flag == 'since_search':
				for tl_object in api.user_timeline(TL_search_object["name"], count=100, since_id=TL_search_object["TLflag"]["id"]):
					_download(tl_object, TL_search_object["name"], TL_search_object["RTflag"], TL_search_object["gifflag"], TL_search_object["videoflag"])
					_TL_hashtag_check(tl_object)
					TL_search_object["TLflag"]["id"] = tl_object.id
					TL_tweet_get_fault_count = 0
		except tweepy.RateLimitError as err_description:
			if TL_tweet_get_fault_count < 2:
				err_subject = str(TL_search_object["name"]) + " : RateLimitError_tweet_get : " + str(TL_search_object["TLflag"]["id"])
				_log(err_subject, err_description)
				TL_tweet_get_fault_count = TL_tweet_get_fault_count +1
				sleep(60 * 15)
				_TL_tweet_get()
		except Exception as err_description:
			if TL_tweet_get_fault_count < 2:
				err_subject = str(TL_search_object["name"]) + " : Exception_tweet_get : " + str(TL_search_object["TLflag"]["id"])
				_log(err_subject, err_description)
				TL_tweet_get_fault_count = TL_tweet_get_fault_count +1
				sleep(60 * 5)
				_TL_tweet_get()

	tagfile = working_directory + date + '_tag.csv'
	hashtag_2csv = []
	for index,TL_search_object in enumerate(json_dict):
		TL_search_fault_count = 0
		hashtag_tmp = []
		if not TL_search_object["TLflag"] == False:
			if TL_search_object["TLflag"]["id"] == "":
				start_id_and_date = _get_tweetid()
				TL_search_object["TLflag"]["id"] = _get_tweetid()
				TL_search_object["TLflag"]["date"] = date
				search_flag = 'max_search'
			else:
				search_flag = 'since_search'
			if not TL_search_object["TLflag"]["id"] == None:
				TL_tweet_get_fault_count = 0
				DL_or_hash = 0
				for l in range(50):
					_TL_tweet_get()
				json_dict[index]["TLflag"]["id"] = TL_search_object["TLflag"]["id"]
		if TL_search_object["hashtagflag"] == True:
			hashtag_2csv.extend(hashtag_tmp)
	if hashtag_2csv:
		with open(tagfile, 'w') as file:
			writer = csv.writer(file, lineterminator='\n')
			writer.writerow(hashtag_2csv)



### hash tag ###

def _hashtag_split(hashtag_tmp):
	hashtag_tmp = re.sub(r'#', " #", hashtag_tmp)
	emoji_pattern = re.compile("["
		u"\U0001F600-\U0001F64F"
		u"\U0001F300-\U0001F5FF"
		u"\U0001F680-\U0001F6FF"
		u"\U0001F1E0-\U0001F1FF"
		u"\U0001F201-\U0001F9E6"
		"]+", flags=re.UNICODE)
	hashtag_tmp = re.sub(emoji_pattern, " ", hashtag_tmp)
	pattern = re.compile(r'[\s\[\]\(\)\<\>\（\）\＜\＞\"\']')
	hashtag_split = re.split(pattern, hashtag_tmp)
	hashtags = [x for x in hashtag_split if '#' in x]
	for x in range(len(hashtags)):
		hashtags[x] = re.sub(r'#', "", hashtags[x])
	return hashtags


def _hashtag():
	profile_description_hashtag_fault_count = 0
	hashtags = []

	def _profile_description_hashtag(SCREEN_NAME):
		nonlocal profile_description_hashtag_fault_count
		nonlocal hashtags
		try:
			USER_DESCRIPTION = api.get_user(SCREEN_NAME).description
			hashtags = _hashtag_split(hashtag_tmp)
		except Exception as err_description:
			if profile_description_hashtag_fault_count < 2:
				profile_description_hashtag_fault_count = profile_description_hashtag_fault_count + 1
				err_subject = SCREEN_NAME + " : Exception_profile_description"
				_log(err_subject, err_description)
				sleep(60)
				_profile_description_hashtag(SCREEN_NAME)
	for index,hashtag_object in enumerate(json_dict):
		if hashtag_object["hashtagflag"] == True:
			_profile_description_hashtag(hashtag_object["name"])
			for tag in hashtags:
				if not tag in  json_dict:
					json_dict[index]["Query"].update({tag:{"date":"", "id":""}})
'''
	if USER["hashtagflag"] == True:
		_profile_description_hashtag(USER["name"])
		for tag in hashtags:
			if not tag in  json_dict:
				json_dict[index]["Query"].update({tag:{"date":"", "id":""}})
'''



### profile ###

def _profile_get_img(url, file_name):
	profile_get_img_fault_count = 0
	def _get_img(url, file_name):
		nonlocal profile_get_img_fault_count
		res = requests.get(url=url)
		if res.status_code == 200:
			f = open(file_name, 'wb')
			f.write(res.content)
			f.close()
		elif profile_get_img_fault_count < 2:
			profile_get_img_fault_count = profile_get_img_fault_count + 1
			_get_img(url, file_name)
	_get_img(url, file_name)

def _profile_get_capture_icon(screen_name, file_path_cap):
	url_user = "https://twitter.com/" + screen_name
	capture_icon_file = file_path_cap + screen_name + "_capture_icon_" + date + ".jpg"
	cmd_capture_icon = "wkhtmltoimage --crop-h 255 --crop-w 255 --crop-x 50 --crop-y 185 " + url_user + " " + capture_icon_file
	subprocess.call(cmd_capture_icon.split(), shell=False)

def _profile_get_capture_banner(screen_name, file_path_cap):
	url_user = "https://twitter.com/" + screen_name
	capture_banner_file = file_path_cap + screen_name + "_capture_banner_" + date + ".jpg"
	cmd_capture_banner = "wkhtmltoimage --crop-h 380 --crop-w 1023 --crop-x 1 --crop-y 40 " + url_user + " " + capture_banner_file
	subprocess.call(cmd_capture_banner.split(), shell=False)

### test
def _follow_counter_cap(screen_name, counter, file_path_cap):
	for kiri in [1000000, 100000, 10000, 1000, 100]:
		if counter % kiri ==0:
			url_user = "https://twitter.com/" + screen_name
			capture_banner_file = file_path_cap + screen_name + "_" + kiri + "_" + date + ".jpg"
			cmd_capture_banner = "wkhtmltoimage --crop-h 380 --crop-w 1023 --crop-x 1 --crop-y 40 " + url_user + " " + capture_banner_file
			subprocess.call(cmd_capture_banner.split(), shell=False)
			break
		else:
			pass
###
		
def _profile():
	file_path = download_directory
	#file_path_cap = "<capture閲覧用>"
	file_path_cap = "/var/www/html/capture/"
	prof_flag = "0"

	for profile_object in json_dict:
		if "Profileflag" in profile_object:
			if profile_object["Profileflag"] == True:
				profile_object_name = profile_object["name"]
				profile_object = _twitter_userobject_get(SCREEN_NAME)

				### test
				_follow_counter_cap(profile_object_name, profile_object.followers_count, file_path_cap)
				###
		
				if hasattr(profile_object, "profile_image_url_https"):
					profile_icon = profile_object.profile_image_url_https
					if '_normal' in profile_icon:
						profile_icon = profile_icon.replace("_normal", "")
					elif '_mini' in profile_icon:
						profile_icon = profile_icon.replace("_mini", "")
					elif '_bigger' in profile_icon:
						profile_icon = profile_icon.replace("_bigger", "")
					comparison_icon_file = file_path + profile_object_name + "_comparison_icon_" + date + "." + profile_icon.rsplit(".", 1)[1]
					_profile_get_img(profile_icon, comparison_icon_file)
					if not glob.glob(file_path + profile_object_name + '_base_icon*'):
						base_icon_file = file_path + profile_object_name + "_base_icon." + profile_icon.rsplit(".", 1)[1]
						shutil.copyfile(comparison_icon_file, base_icon_file)
						shutil.copyfile(comparison_icon_file, file_path_cap + profile_object_name + "_icon_" + date + "." + profile_icon.rsplit(".", 1)[1])
						_profile_get_capture_icon(profile_object_name, file_path_cap)
					base_icon_file = glob.glob(file_path + profile_object_name + '_base_icon*')[0]
					if filecmp.cmp(base_icon_file, comparison_icon_file) == False :
						shutil.copyfile(comparison_icon_file, file_path_cap + profile_object_name + "_icon_" + date + "." + profile_icon.rsplit(".", 1)[1])
						shutil.copyfile(comparison_icon_file, base_icon_file)
						_profile_get_capture_icon(profile_object_name, file_path_cap)
						#api.update_with_media(filename=capture_file)
						prof_flag = "1"
					os.remove(comparison_icon_file)
				if hasattr(profile_object, "profile_banner_url"):
					profile_banner = profile_object.profile_banner_url
					comparison_banner_file = file_path + profile_object_name + "_comparison_banner_" + date + ".jpg"
					_profile_get_img(profile_banner, comparison_banner_file)
					if not glob.glob(file_path + profile_object_name + '_base_banner*'):
						base_banner_file = file_path + profile_object_name + "_base_banner.jpg"
						shutil.copyfile(comparison_banner_file, base_banner_file)
						shutil.copyfile(comparison_banner_file, file_path_cap + profile_object_name + "_banner_" + date + ".jpg")
						_profile_get_capture_banner(profile_object_name, file_path_cap)
					base_banner_file = glob.glob(file_path + profile_object_name + '_base_banner*')[0]
					if filecmp.cmp(base_banner_file, comparison_banner_file) == False:
						shutil.copyfile(comparison_banner_file, file_path_cap + profile_object_name + "_banner_" + date + ".jpg")
						shutil.copyfile(comparison_banner_file, base_banner_file)
						_profile_get_capture_banner(profile_object_name, file_path_cap)
						#api.update_with_media(filename=capture_file)
						prof_flag = "1"
					os.remove(comparison_banner_file)
				
	if prof_flag != "0":
		twi_str = '変わったかも_{0:%H:%M}'.format(datetime.datetime.now())
		api.update_status(twi_str)



### search ###

def _search():
	search_fault_count = 0
	search_date_tmp = ""
	def _search_start(user_object):
		nonlocal search_fault_count
		nonlocal search_flag
		nonlocal search_query
		nonlocal search_date
		try:
			if search_flag == 'since_search':
				for search_object in api.search(q=search_query, count=100, since_id=search_date["id"]):
					if search_object:
						_download(search_object, user_object["name"], user_object["RTflag"], user_object["gifflag"], user_object["videoflag"])
						search_date["id"] = search_object.id
						search_fault_count = 0
			else:
				for search_object in api.search(q=search_query, count=100, max_id=search_date["id"]):
					if search_object:
						_download(search_object, user_object["name"], user_object["RTflag"], user_object["gifflag"], user_object["videoflag"])
						search_date["id"] = search_object.id
						search_fault_count = 0
		except tweepy.RateLimitError as err_description:
			if search_fault_count < 3:
				search_fault_count = search_fault_count +1
				err_subject = user_object["name"] + " : RateLimitError_search_start"
				_log(err_subject, err_description)
				sleep(60 * 15)
				_search_start(user_object)
		except Exception as err_description:
			if search_fault_count < 3:
				search_fault_count = search_fault_count +1
				err_subject = user_object["name"] + " : Exception_search_start"
				_log(err_subject, err_description)
				sleep(10)
				_search_start(user_object)
	for index,user_object in enumerate(json_dict):
		if not user_object['Query'] == {}:
			for search_query,search_date in user_object['Query'].items():
				if search_date['id']:
					if api.search(q=search_query, since_id=search_date['id']):
						search_flag = 'since_search'
				else:
					search_date_tmp = api.search(q=search_query, count=1)
					if search_date_tmp:
						search_flag = 'max_search'
						search_date['id'] = search_date_tmp[0].id
					else:
						continue
				for l in range(50):
					search_fault_count = 0
					_search_start(user_object)
				json_dict[index]['Query'][search_query]['id'] = search_date['id']



### add ###

def _add_new_object():
	for tmp_user in cmd_args.name:
		if not tmp_user in json_dict:
			if os.path.exists(download_directory + tmp_user) == False:
				os.makedirs(download_directory + tmp_user)
			json_dict.append({
				"name":tmp_user,
				"Query":{},
				"Profileflag":cmd_args.profile,
				"hashtagflag":cmd_args.hashtag,
				"TLflag":add_tl,
				"RTflag":cmd_args.rt,
				"videoflag":cmd_args.video,
				"gifflag":cmd_args.gif
			})



### follow user get ###

def _follow_user_get(SCREEN_NAME):
	my_friends_ids = []
	follow_user_fault_count = 0
	follow_user_list_fault_count = 0
	def _follow_user_list():
		nonlocal follow_user_list_fault_count
		try:
			for tmp_id in tweepy.Cursor(api.friends_ids, id=SCREEN_NAME).items():
				my_friends_ids.append(tmp_id)
				follow_user_list_fault_count = 0
		except tweepy.RateLimitError as err_description:
			if follow_user_list_fault_count < 2:
				follow_user_list_fault_count = follow_user_list_fault_count + 1
				err_subject = "RateLimitError_follow_user_get_1"
				_log(err_subject, err_description)
				sleep(60 * 15)
				_follow_user_list()
		except Exception as err_description:
			if follow_user_list_fault_count < 2:
				follow_user_list_fault_count = follow_user_list_fault_count + 1
				err_subject = "Exception_follow_user_get_1"
				_log(err_subject, err_description)
				sleep(60)
				_follow_user_list()
	def _follow_user_description():
		nonlocal my_friends_ids
		nonlocal follow_user_fault_count
		try:
			for tmp_id in my_friends_ids:
				SCREEN_NAME = api.get_user(tmp_id).screen_name
				if not SCREEN_NAME in json_dict:
					if os.path.exists(download_directory + SCREEN_NAME) == False:
						os.makedirs(download_directory + SCREEN_NAME)
					json_dict.append({
						"name":SCREEN_NAME,
						"Query":{},
						"Profileflag":cmd_args.profile,
						"hashtagflag":cmd_args.hashtag,
						"TLflag":add_tl,
						"RTflag":cmd_args.rt,
						"videoflag":cmd_args.video,
						"gifflag":cmd_args.gif
					})
				follow_user_fault_count = 0
		except tweepy.RateLimitError as err_description:
			if follow_user_fault_count < 2:
				follow_user_fault_count = follow_user_fault_count + 1
				err_subject = "RateLimitError_follow_user_get_2"
				_log(err_subject, err_description)
				sleep(60 * 15)
				_follow_user_description()
		except Exception as err_description:
			if follow_user_fault_count < 2:
				follow_user_fault_count = follow_user_fault_count + 1
				err_subject = "Exception_follow_user_get_2"
				_log(err_subject, err_description)
				sleep(60)
				_follow_user_description()
	_follow_user_list()
	_follow_user_description()



### download ###

def _download(dl_object, download_filepath, retweet_enable, gif_enable, video_enable):
	errcount = 0
	download_filepath = download_directory + download_filepath + "/"
	def _download_file():
		nonlocal errcount
		nonlocal DL_FILENAME
		nonlocal DL_URL
		nonlocal media
		try:
			with open(download_filepath + DL_FILENAME, 'wb') as f:
				dl_file = urllib.request.urlopen(DL_URL).read()
				f.write(dl_file)
		except Exception as err_description:
			if errcount < 2:
				errcount = errcount +1
				err_subject = "Exception_download : " + DL_URL
				_log(err_subject, err_description)
				sleep(60)
				_download_file(type, gif_enable)
			else:
				errcount = 0
		if media["type"] == 'animated_gif' and gif_enable == True:
			gifenc1 = "ffmpeg -i " + download_filepath + DL_FILENAME + " -vf fps=20,palettegen=stats_mode=diff -y " + download_filepath + "palette.png"
			gifenc2 = "ffmpeg -i " + download_filepath + DL_FILENAME + " -i palette.png -lavfi fps=20,paletteuse -y " + download_filepath + os.path.splitext(DL_FILENAME)[0] + ".gif"
			subprocess.call(gifenc1.split(), shell=False)
			subprocess.call(gifenc2.split(), shell=False)
			
	# リツイート判断
	if hasattr(dl_object, 'retweeted_status') == True and retweet_enable == False:
		pass
	else:
		# メディア判断
		if hasattr(dl_object, "extended_entities"):
			if 'media' in dl_object.extended_entities:
				for media in dl_object.extended_entities["media"]:
					if media["type"] == 'photo':
						DL_URL = media["media_url"]
						DL_FILENAME = os.path.basename(DL_URL)
						FILE_CHECK = DL_FILENAME
						DL_URL = DL_URL + ":orig"
					if media["type"] == 'animated_gif' and gif_enable == True:
						DL_URL = media["video_info"]["variants"][0]["url"]
						DL_FILENAME = os.path.basename(DL_URL)
						FILE_CHECK = re.split("[./]", DL_URL)[-2] + ".gif"
					if media["type"] == 'video' and video_enable == True:
						DL_URL = media["video_info"]["variants"][0]["url"]
						if '.m3u8' in DL_URL:
							DL_URL = media["video_info"]["variants"][1]["url"]
						if '?tag=' in DL_URL:
							DL_URL = DL_URL[:-6]
						DL_FILENAME = os.path.basename(DL_URL)
						FILE_CHECK = DL_FILENAME
					if os.path.exists(download_filepath + FILE_CHECK) == False:
						_download_file()



### log ###

def _log(err_subject, err_description):
	print(str(datetime.datetime.now()) + " : " + str(err_subject) + " : " + str(err_description))
	with open(LOGFILE,'a') as f:
		f.write(str(datetime.datetime.now()) + " : " + str(err_subject) + " : " + str(err_description) + "\n")



### show ###

def _show():
	print(json_dict[cmd_args.name])
	sys.exit()


### add query ###

#def _add_query():




### init ###

def init_start():
	if os.path.exists(download_directory) == False:
		print("directory is not found.")
		sys.exit()
	if os.path.exists(DB_file) == False:
		print("json-file is not found.")
		print("Do you want to create a file?(y/n)")
		q = input()
		if q == "y":
			f = open(DB_file,'w+')
			f.close()
			json_dict.append({
				"name":"dummy",
				"TLflag":False,
				"Query":{},
				"Profileflag":False,
				"hashtagflag":False,
				"RTflag":False,
				"videoflag":False,
				"gifflag":False
			})
			print("result: " + str(os.path.exists(DB_file)))
		else:
			sys.exit()
	print("init done.\n")



### Edit json ###

def _edit_json():
	f = open(DB_file,'w')
	json.dump(json_dict, f)
	f.close()



### parser ###

def _parser():
	parser = argparse.ArgumentParser(
		usage=' python3 main.py [json-file]\n\\n\
	python3 main.py [json-file] --addf --name user --tl --gif --video\n\
	python3 main.py [json-file] --addo --name user1 user2 user3 --tl --gif --video\n\\n\
	nohup python3 main.py [json-file] &',
		add_help=True,
		formatter_class=argparse.RawTextHelpFormatter
		)
	parser.add_argument("json_file", help="please set DBfile.json.", type=str, nargs=1, metavar="[json-file]")
	parser.add_argument("--name", help="select object.", type=str, nargs='*', metavar="<object-name>...")
	parser.add_argument("--show", help="show object-list. if select object, show query.\n\n", action="store_true")

	parser.add_argument("--addf", help="add Screen's follow-user.", action="store_true")
	parser.add_argument("--addo", help="add new-screen-object or new-search-object.", action="store_true")
	parser.add_argument("--addq", help="add search-query to object.\n\n", type=str, nargs='*', metavar="<query-name>...")

	#parser.add_argument("--delo", help="del screen-object or search-object.", action="store_true")
	#parser.add_argument("--delq", help="del search-query object.\n\n", action="store_true")

	parser.add_argument("--profile", help="profile-check.", action="store_true")
	parser.add_argument("--hashtag", help="hashtag-check(TL, User-Profile).", action="store_true")
	parser.add_argument("--tl", help="TL-check.", action="store_true")
	parser.add_argument("--rt", help="including Retweets at TL-check.", action="store_true")
	parser.add_argument("--video", help="including video-file at Search,TL-check.", action="store_true")
	parser.add_argument("--gif", help="including gif-file at Search,TL-check.", action="store_true")
	return parser.parse_args()



### main ###

if __name__ == '__main__':
	json_dict = []
	cmd_args = _parser()
	if os.path.dirname(cmd_args.json_file[0]):
		working_directory = os.path.dirname(cmd_args.json_file[0]) + "/"
	else:
		working_directory = os.getcwd() +"/"
	if not os.path.exists(working_directory + "download"):
		os.makedirs(working_directory + "download")
	download_directory = working_directory + "download/"
	DB_file = working_directory + os.path.basename(cmd_args.json_file[0])
	date = datetime.datetime.today().strftime("%Y%m%d_%H%M_%S")
	LOGFILE = working_directory + date + "_log.txt"
	if not os.path.exists(DB_file):
		init_start()
		_edit_json()
	shutil.copyfile(DB_file, DB_file + "_bak")
	f = open(DB_file,'r')
	json_dict = json.load(f)
	f.close()
	api = tweepy_api()

	if cmd_args.addf or cmd_args.addo or cmd_args.addq is not None or cmd_args.show:
		if cmd_args.tl == False:
			add_tl = False
		else:
			add_tl = {"id":"", "date":""}
		if cmd_args.addf:
			if not cmd_args.name or len(cmd_args.name) != 1:
				print("invalid argument '--name'")
			else:
				_follow_user_get(cmd_args.name[0])
		if cmd_args.addo:
			if not cmd_args.name:
				print("invalid argument '--name'")
			else:
				_add_new_object()
		if cmd_args.addq is not None:
			if not cmd_args.name or len(cmd_args.name) != 1:
				print("invalid argument '--name'")
			if len(cmd_args.addq) < 1:
				print("invalid argument '--addq'")
			#else:
			#       _add_query()
		if cmd_args.show:
			if not cmd_args.name or len(cmd_args.name) != 1:
				print("invalid argument '--name'")
			else:
				_show()
		_edit_json()
		sys.exit()
	if len(json_dict) < 2:
		print("please add object.")
		sys.exit()

	_profile()
	_hashtag()
	_TL_search()
	_search()
	_url_get()
	_edit_json()
