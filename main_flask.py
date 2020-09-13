# -*- coding: utf-8 -*-

import sys
import os
import json
# data analysis
import pandas as pd
import numpy as np
# request
import grequests
import requests
# parse
from bs4 import BeautifulSoup
import bs4
# cn word split
import jieba
# web service
from flask import Flask
from flask import request
from flask import Response
from flask_cors import *

from server.datetimeManager import datetimeManager

app = Flask(__name__)
CORS(app, supports_credentials=True)

dm = datetimeManager()

folder = os.path.abspath(os.path.dirname(__file__))

# 获取推荐词 20 个
@app.route('/article/api/recommend_words', methods=['GET'])
def api_recommend_words():
    start_ts = dm.getTimeStamp()
    # 请求
    df = get_keyword_from_articles()
    max = len(df)
    idxs = np.random.randint(0, max, size=20)
    df_sub = df[df.index.isin(idxs)]
    results = json.loads(df_sub.to_json(orient='records',force_ascii=False))
    end_ts = dm.getTimeStamp()
    duration = dm.getDuration(start_ts, end_ts)
    data = packDataWithCommonInfo(duration = duration, data = results)
    return Response(data, status=200, mimetype='application/json')

# 获取包含推荐词的文章
@app.route('/article/api/autocomplete/<word>', methods=['GET'])
def api_autocomplete(word):
    start_ts = dm.getTimeStamp()
    keyword = str(word)
    # 请求
    df = get_keyword_from_articles()
    df_sub = df[df.word.str.contains(keyword)]
    results = json.loads(df_sub.to_json(orient='records',force_ascii=False))
    end_ts = dm.getTimeStamp()
    duration = dm.getDuration(start_ts, end_ts)
    data = packDataWithCommonInfo(duration = duration, data = results)
    return Response(data, status=200, mimetype='application/json')

# 获取包含推荐词的文章
@app.route('/article/api/keyword/<word>', methods=['GET'])
def api_keyword(word):
    start_ts = dm.getTimeStamp()
    keyword = str(word)
    # 请求
    df = get_all_articles()
    df_sub = df[df.article.str.contains(keyword)]
    results = json.loads(df_sub.to_json(orient='records',force_ascii=False))
    end_ts = dm.getTimeStamp()
    duration = dm.getDuration(start_ts, end_ts)
    data = packDataWithCommonInfo(duration = duration, data = results)
    return Response(data, status=200, mimetype='application/json')

def get_all_articles(cache_first = True):
    """
    获取所有评论员文章列表页（1 - 16 页）
    """
    file_path = os.path.join(folder, 'all_articles.xlsx')
    if cache_first and os.path.exists(file_path):
        return pd.read_excel(file_path, dtype={'number':np.int64}, index_col=0)
    main_url_holder = u'http://opinion.people.com.cn/GB/8213/49160/49217/index{0}.html'
    tasks = [grequests.get(main_url_holder.format(x)) for x in range(1, 17)]
    reponse_list = grequests.map(tasks, size=5)
    # 从评论员文章列表页获取文章标题和文章链接
    comment_url_prefix = u'http://opinion.people.com.cn'
    links = []
    for resp in reponse_list:
        resp.encoding = u'gbk'
        comment_list_soup = BeautifulSoup(resp.text, 'lxml')
        [links.append(x) for x in comment_list_soup.select('.abl')]
    # print(len(links))
    df_urls = pd.DataFrame([{'title': x.text, 'url': comment_url_prefix + x.get('href')} for x in links])
    # 去重
    df_urls = df_urls.drop_duplicates(subset='url')
    # 并发获取所有新闻段落（同时发送 5 个请求）
    news_urls = df_urls.url.tolist()
    # news_urls
    tasks = [grequests.get(x) for x in news_urls]
    response_list = grequests.map(tasks, size=5)
    articles = []
    for news_resp in response_list:
        # 只要请求成功和没有重定向到失败页面的内容
        if news_resp and 'error' not in news_resp.url:
            news_resp.encoding=u'gbk'
            news_soup = BeautifulSoup(news_resp.text, 'lxml')
            paragraphs = news_soup.select('p')
            i = 1
            for p in paragraphs:
                for line in p.contents:
                    # bs4.element.NavigableString 文本
                    # bs4.element.Tag 标签
                    if isinstance(line, bs4.element.NavigableString) and '。' in line:
                        paragraph = str(line).replace('\n','').replace('\t','')
    #                     text_lists.append(paragraph)
                        articles.append(pd.Series({'url':news_resp.url, 'number':i, 'article':paragraph}))
                        # 文章段落 id
                        i +=1 
    #         break
    df_articles = pd.DataFrame(articles)
    # texts = ' '.join(text_lists)
    # cut_text = jieba.cut(texts)
    # # result = ' '.join(cut_text)
    # s = pd.Series(cut_text, name='word')
    # s.value_counts()
    df = pd.merge(df_urls, df_articles, on='url', how='outer')
    df = df.dropna(subset=['article'])
    df.number = df.number.astype(np.int64)
    df.to_excel(file_path)
    pass

def get_keyword_from_articles(cache_first = True):
    """
    从所有文章中，获取词频列表
    """
    file_path = os.path.join(folder, 'word_frequency.xlsx')
    if cache_first and os.path.exists(file_path):
        return pd.read_excel(file_path, dtype={'freq':np.int64}, index_col=0)
    # 获取所有文章
    df = get_all_articles()
    texts = ' '.join(df.article.values.tolist())
    cut_text = jieba.cut(texts)
    s = pd.Series(cut_text, name='word')
    # 把词频统计，组成 DataFrame
    df_results = pd.DataFrame(s.value_counts())
    df_results.reset_index(drop=False, inplace=True)
    df_results.rename(columns={'index':'word','word':'freq'}, inplace=True)
    # 去掉单字热词
    df_results['word_len'] = df_results.word.apply(lambda x: len(x))
    df_results = df_results[df_results['word_len'] >= 2]
    df_results.drop('word_len', axis=1, inplace=True)
    df_results.reset_index(drop=True, inplace=True)
    df_results.to_excel(file_path)
    return df_results

# 添加公共返回值
def packDataWithCommonInfo(isCache = False, isSuccess = True, msg = "success", duration = '0', data = {}):
    code = 0
    if not isSuccess:
        code = -1
    result = {'code' : code, 'msg' : msg, 'isCache' : False, 'aliyun_date' : datetimeManager().getDateTimeString(), 'data' : data, 'duration' : duration}
    return json.dumps(result, ensure_ascii=False, indent=4)

# debug
if __name__ == '__main__':
    app.run(port=5000, debug=True)
    # df = pa.get_all_articles()

    # df['len'] = df.article.apply(lambda x: len(x))
    # print(df.len.sum())

    # df_sub = df[df.article.str.contains('纳入')]
    # print(df_sub)
    pass
