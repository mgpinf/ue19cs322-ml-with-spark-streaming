import sys
import json
import re
import numpy as np
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.sql import SQLContext, Row
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from sklearn.feature_extraction.text import HashingVectorizer

from pyspark.ml.feature import OneHotEncoder, StringIndexer, VectorAssembler
from pyspark.ml.feature import RegexTokenizer, StopWordsRemover, CountVectorizer
from pyspark.ml.classification import LogisticRegression

from sklearn.naive_bayes import BernoulliNB
from sklearn.linear_model import Perceptron, SGDClassifier
from sklearn.cluster import MiniBatchKMeans

import pickle

# global variable
first_batch = True
tweet_id = 0
sc = None
perceptron_train_model=None
bernoulli_train_model=None
sgd_classifier_train_model=None
mini_batch_kmeans_cluster_train_model=None


sc = SparkContext(master="local[2]", appName="mlss_bd_198_200_367_503")
ssc = StreamingContext(sc, 1)

lines = ssc.socketTextStream("localhost", 6100)

with open('perceptron', 'rb') as perceptron_dbfile:
    perceptron_db = pickle.load(perceptron_dbfile)
with open('bernoulli', 'rb') as bernoulli_dbfile:
    bernoulli_db = pickle.load(bernoulli_dbfile)
with open('sgd_classifier', 'rb') as sgd_classifier_dbfile:
    sgd_classifier_db = pickle.load(sgd_classifier_dbfile)
with open('mini_batch_kmeans_cluster', 'rb') as mini_batch_kmeans_cluster_dbfile:
    mini_batch_kmeans_cluster_db = pickle.load(mini_batch_kmeans_cluster_dbfile)

perceptron_train_model = perceptron_db
bernoulli_train_model = bernoulli_db
sgd_classifier_train_model = sgd_classifier_db
mini_batch_kmeans_cluster_train_model = mini_batch_kmeans_cluster_db

# my_schema = StructType([StructField(name='tweet', dataType=StringType(), nullable=True), StructField(name='sentiment', dataType=IntegerType(), nullable=True)])

row = lines.flatMap(lambda line: json.loads(line))

def p_process(rdd):
    global tweet_id
    global first_batch
    global sc
    global perceptron_train_model
    global bernoulli_train_model
    global sgd_classifier_train_model
    global mini_batch_kmeans_cluster_train_model

    start_index = 0
    list1 = []
    tweet_list = []
    sentiments = []
    col = ["sentiment","tweet"]
    if(not rdd.isEmpty()):
        if first_batch:
            first_batch = False
            start_index = 1
        row = rdd.map(lambda x: Row(sentiment=x[0], tweet=x[1]))
        a = rdd.collect()[start_index:]
        a = list(map(lambda i: i.split(",", 1), a))
        for i in range(len(a)):
            sentiment = int(a[i][0])
            tweet = a[i][1].lstrip().rstrip()
            tweet = re.sub(r'http\S+', '', tweet)
            tweet = tweet.strip('\"').lstrip().rstrip()
            tweet = " ".join(
                filter(lambda x: x[0] != '@', tweet.split())).lstrip().rstrip()
            tweet = " ".join(
                filter(lambda x: x[0] != '#', tweet.split())).lstrip().rstrip()

            # Removing punctuations in string using regex
            tweet = re.sub(r'[^\w\s]', ' ', tweet).lstrip().rstrip()

            # Converting multiple white-spaces into single whitespace
            tweet = re.sub(r' +', ' ', tweet).lstrip().rstrip()

            # converting tweet to lowercase
            tweet = tweet.lower()
            tweet_list.append(tweet)
            sentiments.append(sentiment)

            if len(tweet) != 0:
                list1.append((sentiment, tweet))

        sqlContext = SQLContext(sc)
        df = sqlContext.createDataFrame(list1, col)
        vectorizer=HashingVectorizer(n_features=1000)

        X_test=vectorizer.fit_transform(tweet_list)
        y_test= sentiments

        print("------------------")
        print("perceptron_train_model score", perceptron_train_model.score(X_test, y_test))
        print("bernoulli_train_model score", bernoulli_train_model.score(X_test, y_test))
        print("sgd_classifier_train_model score", sgd_classifier_train_model.score(X_test, y_test))
        print("mini_batch_kmeans_cluster_train_model score", mini_batch_kmeans_cluster_train_model.score(X_test, y_test))
        print("------------------")



row.foreachRDD(p_process)

ssc.start()
ssc.awaitTermination()
ssc.stop()