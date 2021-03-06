# -*- coding: utf-8 -*-
# @Time     : 2019/4/29 21:34
# @Author   : gaol
# @Project  : RecommendationSystem
# @File     : MovieRecommend.py

import time
import random
import math
import LFM
import pickle
import os
import sys

from operator import itemgetter

# 将数据划分为训练集和测试集
def SplitData(data, M, k, seed):
    test = {};train = {}
    random.seed(seed)

    for user, item in data:
        if random.randint(0, M) == k:
            if user not in test:
                test[user] = dict()
            if item not in test[user]:
                test[user][item] = 0
            test[user][item] += 1
        else:
            if user not in train:
                train[user] = dict()  # train = {'1':{'1193':1,'661':1,'914':1,...},'2':{'1357':1,...}}
            if item not in train[user]:
                train[user][item] = 0
            train[user][item] += 1

    return train, test


'''
准确率，召回率
'''
def PrecisionRecall(train, test, P, Q, N):
    hit = 0
    p_all = 0
    r_all = 0

    for user in train.keys():
        tu = test.get(user,{})  # 用户user在测试集上喜欢的物品集合，是一个字典

        # if tu:  # 由于|R(u)|=N是人为设定要推荐的物品数，所以此处就没必要为tu为空的user做推荐计算了
        rank_all = LFM.LFMRecommend(train, user, P, Q)    # 给训练集中的user做的和他兴趣相似的所有用户有过行为的全部物品的推荐
        rank_TopN = sorted(rank_all.items(), key=itemgetter(1), reverse=True)[0:N]
        # 推荐给用户user的TopN物品及对应的预测出来的user对该物品的兴趣度

        # for item, pui in rank_all.items():
        for item, pui in rank_TopN:
            if item in tu:
                hit += 1

        p_all += N
        # p_all += len(rank_all)
        r_all += len(tu)

    return hit / p_all, hit / r_all

'''
覆盖率
'''
def Coverge(train, P, Q, N):
    recommend_items = set()
    all_items = set()

    for user in train.keys():
        for item in train[user].keys():
            all_items.add(item)

        rank_all = LFM.LFMRecommend(train, user, P, Q)
        rank_TopN = sorted(rank_all.items(), key=itemgetter(1), reverse=True)[0:N]

        # for item, pui in rank_all.items():
        for item, pui in rank_TopN:
            recommend_items.add(item)

    return len(recommend_items) / len(all_items)

'''
新颖度
'''
# 物品流行数列表
def PopularityNums(train):
    item_popularity_nums = dict()

    for user, items in train.items():
        for item in items.keys():
            if item not in item_popularity_nums:
                item_popularity_nums[item] = 0
            item_popularity_nums[item] += 1

    return item_popularity_nums


# 物品流行度列表
def PopularityRates(item_popularity_nums):
    n = 0
    for item_popularity_num in item_popularity_nums.values():
        n += item_popularity_num

    item_popularity_rates = {k: v / n for k, v in item_popularity_nums.items()}

    return item_popularity_rates


# 新颖度（用平均流行度度量）
def Novelty(train, P, Q, N):
    item_popularity = PopularityNums(train)

    ret = 0
    n = 0  # n=用户数*TopN推荐列表中物品数N（推荐的物品总数）

    for user in train.keys():
        rank_all = LFM.LFMRecommend(train, user, P, Q)
        rank_TopN = sorted(rank_all.items(), key=itemgetter(1), reverse=True)[0:N]

        # for item, pui in rank_all.items():
        for item, pui in rank_TopN:
            ret += math.log(1 + item_popularity[item])
            n += 1

    return ret / n


'''
基尼系数度量覆盖率
'''
def GiniIndex(p):
    j = 1;
    n = len(p);
    G = 0

    for item, weight in sorted(p.items(), key=itemgetter(1)):  # key(p.items())函数
        G += (2 * j - n - 1) * weight
        j += 1

    return G / (n - 1)


'''
Main
'''
def main():
    # 数据集按均匀分布划分为M份，M-1份均为训练集，剩下1份为测试集
    M = 8
    k = 0
    seed = 42   # 随机数种子

    data = [tuple(line.split('::')[:2]) for line in open('G:/master/python/PycharmProjects/RecommendationSystem/LFM/data/ml-1m/ratings.dat').readlines()]  # win10上的ml-1m数据集
    # data = [tuple(line.split(',')[:2]) for line in open('G:/Recommend/User-CF/MovieLens/ml-latest-small/ratings_test.csv').readlines()]		# ml-latest-small数据集

    train, test = SplitData(data, M, k, seed)

    # 训练LFM模型
    F = 100         # 指定隐类个数
    N = 100         # 迭代次数
    alpha = 0.02    # 学习率
    lamda = 0.01    # 正则项参数
    ratio = 20       # 负正样本比例

    training_stime = time.time()
    [P, Q] = LFM.LatentFactorModel(train, F, N, alpha, lamda, ratio)
    training_etime = time.time()
    print('LFM模型训练完成。耗时：{} sec'.format(training_etime - training_stime))

    '''
    fw = open('LFM_pickle','wb')
    fw.write(pickle.dumps([P, Q]))
    fw.close()
    '''

    # 离线指标计算
    precision, recall = PrecisionRecall(train, test, P, Q, 40)
    coverage = Coverge(train, P, Q, 40)
    novelty = Novelty(train, P, Q, 40)
    F1 = 2 * precision * recall / (precision + recall)
    print(f'precision:{precision}\trecall:{recall}\tcoverage:{coverage}\tpopularity:{novelty}\tF1:{F1}')

    '''
    popularity_nums = PopularityNums(train)
    popularity_rates = PopularityRates(popularity_nums)

    gini_index = GiniIndex(popularity_rates)
    print(gini_index)
    '''

if __name__ == '__main__':
    start_time = time.time()
    main()
    print('Time used: {} sec'.format(time.time() - start_time))
