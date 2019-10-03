# Create your views here.
# -*- coding: utf-8 -*-
# Create your views here.

import MeCab
import requests
from django.shortcuts import render

mecab = MeCab.Tagger("-Ochasen")
from math import log
import pandas as pd
import regex
from gensim.models import word2vec
import numpy as np

mt = MeCab.Tagger()
mt.parse('')
model = word2vec.Word2Vec.load("lod_challenge/wiki.model")

pd.options.display.float_format = '{:.10f}'.format
SINGLE_SIGN_PTN = regex.compile(r'\p{Han}{1}')


def match(word):
    if not word:
        return False
    if len(word) > 1:
        is_not_num = not word.isnumeric()
        is_not_nom = not word.isalpha()
        return is_not_num
    else:
        if SINGLE_SIGN_PTN.match(word):
            return True
        else:
            return False

def tf(t, d):
    return d.count(t) / (len(d) + 1)

def idf(t, text, N):
    df = 0
    for doc in text:
        df += t in doc
    return log(N / df) + 1

def tfidf(t, d, text, N):
    return tf(t, d) * idf(t, text, N)

def get_data_from_GURUNAVI(params, text, name, data_lag, data_lng):
    temp = []
    url = "https://api.gnavi.co.jp/RestSearchAPI/v3/"
    result_api = requests.get(url, params)
    result_api = result_api.json()

    # print(result_api)

    if 'rest' in result_api:

        hit = len(result_api['rest'])

        for i in range(hit):
            data_lag.append(result_api['rest'][i]['latitude'])
            data_lng.append(result_api['rest'][i]['longitude'])

        for i in range(hit):
            url = "https://api.gnavi.co.jp/PhotoSearchAPI/v3/"
            params = {}

            params["keyid"] = "9e8a6bd19506af1ac20c950beb84f1c9"# 取得したアクセスキー
            # params["keyid"] = "70d998c61bcc7986a5b49b271b9973eb"
            # params["keyid"] = "6495faf2f01041db54e8c71ae232dfae"

            params["shop_id"] = result_api['rest'][i]['id']
            result = requests.get(url, params)
            result = result.json()
            if not 'gnavi' in result:
                hit_com = result['response']['total_hit_count']
                hit_com = int(hit_com)
                for j in range(hit_com):
                    num = str(j)
                    if num in result['response']:
                        result_m = mecab.parse(result['response'][num]['photo']["comment"])
                        lines = result_m.split('\n')
                        for line in lines:
                            feature = line.split('\t')
                            if len(feature) >= 2:  # 'EOS'と''を省く
                                info = feature[3].split(',')
                                hinshi = info[0]
                                info_tango = feature[2].split(',')
                                tango = info_tango[0]
                                if '名詞' in hinshi:
                                    if not '数' in hinshi:
                                        if not '接尾' in hinshi:
                                            if not '接頭' in hinshi:
                                                if not '非' in hinshi:
                                                    if not '代' in hinshi:
                                                        if match(tango):
                                                            temp.append(tango)
                                if '形容詞' in hinshi:
                                    temp.append(tango)
                text.append(temp)
                temp = []
                name.append(result_api['rest'][i]['name'])
    return text, name, data_lag, data_lng

def get_vector(text):
    sum_vec = np.zeros(200)
    word_count = 0
    node = mt.parseToNode(text)
    while node:
        fields = node.feature.split(",")
        if fields[0] == '名詞' or fields[0] == '動詞' or fields[0] == '形容詞':
            sum_vec += model.wv[node.surface]
            word_count += 1
        node = node.next
    return sum_vec / word_count

def cos_sim(v, v1):
    return np.dot(v, v1) / (np.linalg.norm(v) * np.linalg.norm(v1))

def get_max_name(v1_cos, v2_cos, v3_cos, taste, service, cost, name, word, temp):
    value = name + "：" + word

    if max(v1_cos, v2_cos, v3_cos) <= 0:
        # value_tag = word + "：その他"
        # temp.append(value_tag)
        pass
    elif max(v1_cos, v2_cos, v3_cos) == v1_cos:
        taste.append(value)
        value_tag = word + "：味・風味"
        temp.append(value_tag)
    elif max(v1_cos, v2_cos, v3_cos) == v2_cos:
        service.append(value)
        value_tag = word + "：店員・サービス"
        temp.append(value_tag)
    else:
        cost.append(value)
        value_tag = word + "：値段"
        temp.append(value_tag)

def lod(request):
    point = ""
    freeword = ""

    point = request.POST.get('point', False)
    freeword = request.POST.get('freeword', False)

    if freeword == False:
        # return render(request, 'lod.html', {})
        a = "35.6811673"
        b = "139.7670516"
        return render(request, 'lod.html', {'lat': b}, {'lng': a})

    else:
        point = point.strip("("")")
        point = point.split(',')
        point = tuple(point)

        print(point[0], point[1])

        params = {}

        params["keyid"] = "9e8a6bd19506af1ac20c950beb84f1c9"  # 取得したアクセスキー
        # params["keyid"] = "70d998c61bcc7986a5b49b271b9973eb"
        # params["keyid"] = "6495faf2f01041db54e8c71ae232dfae"

        # point = "(34.7024854, 135.49595060000001)"

        params["latitude"] = point[0]
        params["longitude"] = point[1]
        params["freeword"] = freeword

        params["hit_per_page"] = 30

        text = []
        name = []

        data_lag = []
        data_lng = []

        get_data_from_GURUNAVI(params, text, name, data_lag, data_lng)

        words = list(set(w for doc in text for w in doc))
        words.sort()

        N = len(text)
        print(N)

        for i in range(N):
            for j in range(len(text[i])):
                match(text[i][j])

        for i in range(len(words)):
            for j in range(len(words[i])):
                match(words[i][j])

        result = []

        for i in range(N):
            result.append([])
            d = text[i]
            for j in range(len(words)):
                t = words[j]

                result[-1].append(tf(t, d))

        tf_ = pd.DataFrame(result, columns=words)

        result = []
        for j in range(len(words)):
            t = words[j]
            result.append(idf(t, text, N))

        idf_ = pd.DataFrame(result, index=words, columns=["IDF"])

        result = []
        for i in range(N):
            result.append([])
            d = text[i]
            for j in range(len(words)):
                t = words[j]
                result[-1].append(tfidf(t, d, text, N))

        tfidf_ = pd.DataFrame(result, columns=words)

        df = tfidf_.T
        l_index = list(tfidf_.index)

        taste = []
        service = []
        cost = []

        tag = []

        for i in range(len(l_index)):
            df = df.sort_values(by=l_index[i], ascending=False)
            temp = []
            for j in range(5):
                # if __name__ == "__main__":

                try:
                    v = get_vector(df.index[j])
                    v1 = get_vector('風味 味　味わい')
                    v2 = get_vector('店員　対応')
                    v3 = get_vector('値段　価格')

                    v1_cos = cos_sim(v, v1)
                    v2_cos = cos_sim(v, v2)
                    v3_cos = cos_sim(v, v3)

                    get_max_name(v1_cos, v2_cos, v3_cos, taste, service, cost, name[i], df.index[j], temp)

                except KeyError:
                    pass

            tag.append(temp)
            tag[i].insert(0, name[i])

        a=point[0]
        b=point[1]
        b = b.replace(" ","")

        a=float(a)
        b=float(b)

        return render(request, 'lod.html', {'lat': a, 'lng': b, 'tag':tag , 'name': name, 'taste': taste, 'servce': service, 'cost': cost, 'data_lag':data_lag , 'data_lng':data_lng})