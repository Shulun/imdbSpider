#coding:utf-8

from urllib import request
from bs4 import BeautifulSoup as bs
import re
import wordsegment as ws
import pandas as pd
import numpy
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['figure.figsize'] = (20.0, 10.0)
import matplotlib.pyplot as plt
# %matplotlib inline
from wordcloud import WordCloud
import itertools
import time

def getNowPlayingMovieList(url):
	resp = request.urlopen(url)
	html_data = resp.read().decode('latin-1')
	soup = bs(html_data, 'html.parser')
	nowplaying_movie = soup.find_all('h4', itemprop='name')
	nowplaying_movie_list = []
	for item in nowplaying_movie:
		nowplaying_movie_list.append(item.a)
	nowplaying_list = []
	for item in nowplaying_movie_list:
		nowplaying_dict = {}
		nowplaying_dict['name'] = item['title']
		nowplaying_dict['id'] = item.get('href').split('/')[2]
		# nowplaying_dict['id'] = item['href'].split('/')[2]
		nowplaying_list.append(nowplaying_dict)
	# print(nowplaying_list)
	return nowplaying_list

def getReviewsById(movieId, reviewNum, url):
	reviewList = []
	rem = reviewNum % 10
	for i in range(0, reviewNum-rem, 10):
		requrl = url + movieId + '/reviews?start=' + str(i)
		resp = request.urlopen(requrl)
		html_data = resp.read().decode('latin-1')
		soup = bs(html_data, 'html.parser')
		review_data = soup.find_all('p', class_=None)
		review_data_cleaned = []
		for rev in review_data:
			if not rev.a and not rev.b:
				review_data_cleaned.append(rev)
		review_data_cleaned = review_data_cleaned[:-1]
		reviewList.append(review_data_cleaned)
	if rem:
		requrl = url + movieId + '/reviews?start=' + str(reviewNum-rem)
		resp = request.urlopen(requrl)
		html_data = resp.read().decode('latin-1')
		soup = bs(html_data, 'html.parser')
		review_data = soup.find_all('p', class_=None)
		review_data_rem = []
		for rev in review_data:
			if not rev.a and not rev.b:
				review_data_rem.append(rev)
		review_data_rem = review_data_rem[:rem]
		reviewList.append(review_data_rem)
	reviewList = list(itertools.chain.from_iterable(reviewList))
	# print(reviewList)
	# print(len(reviewList))
	return reviewList

def processReviews(revList):
	reviews = ''
	for rev in revList:
		reviews += str(rev).strip()
	reviews = re.sub('<.*?>', '', reviews)
	pattern = re.compile(r'[a-zA-Z]')
	data = re.findall(pattern, reviews)
	processed_reviews = ''.join(data)
	return processed_reviews

def main():
	url = 'http://www.imdb.com/movies-in-theaters/'
	url1 = 'http://www.imdb.com/title/'
	now_movie_list = getNowPlayingMovieList(url)

	# Get latest 100 reviews of the movie
	movie_id = now_movie_list[14]['id']
	movie_reviews = getReviewsById(movie_id, 100, url1)

	processed_reviews = processReviews(movie_reviews)
	segment = ws.segment(processed_reviews)

	words_df = pd.DataFrame({'segment':segment})
	stopwords = pd.read_csv('stopwords.txt', index_col=False, quoting=3, sep='\t', names=['stopword'], encoding='utf-8')
	words_df = words_df[~words_df.segment.isin(stopwords.stopword)]

	words_stat = words_df.groupby(by=['segment'])['segment'].agg({'count':numpy.size})
	words_stat = words_stat.reset_index().sort_values(by=['count'], ascending=False)

	wordcloud = WordCloud(font_path='simhei.ttf', background_color='white', max_font_size=100)
	word_frequency = {x[0]:x[1] for x in words_stat.head(500).values}

	wordcloud = wordcloud.fit_words(word_frequency)
	plt.imshow(wordcloud)
	plt.axis('off')
	plt.savefig('wordcloud.tiff', bbox_inches='tight', dpi=300)

if __name__ == '__main__':
	start = time.clock()
	main()
	print('Program finishes in', time.clock()-start, 'seconds')