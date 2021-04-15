import pandas as pd
import numpy as np
import sys
import os
import json
import mysql.connector
from itertools import combinations
from math import sqrt
from numpy import dot
from numpy.linalg import norm
import csv

trueHeirarchyFile = "../parent-child-pairs.csv"

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password=""
)

mycursor = mydb.cursor(dictionary=True)

mycursor.execute("use btp")

# getRelationMapping maps all the relations in the restricted dataset to unique integers
def getRelationMapping():
    query = "select binaryRelation from dbpedia_support_size_restricted where size > 0 order by binaryRelation"
    mycursor.execute(query)
    result = mycursor.fetchall()
    rels = []
    for vals in result:
        rels.append(vals['binaryRelation'])
    return rels

# getRelationEmbeddings gets the relation embeddings from the output of TransE
def getRelationEmbeddings():
    res = []
    with open('relation_embeddings.tsv') as tsv_file:
        read_tsv = csv.reader(tsv_file, delimiter="\t")
        for row in read_tsv:
            res.append(np.array(row,dtype=float))
    return res

# getEmbeddingsForRels returns the embeddings for the relations provided
def getEmbeddingsForRels(rels):
    emb = getRelationEmbeddings()
    ret = {}
    i = 0
    for rel in rels:
        ret[rel] = emb[i]
        i = i+1
    return ret

# getSupportSizes returns the support sizes of all the relations
def getSupportSizes():
    query = "select binaryRelation, size from dbpedia_support_size_restricted where size > 0 order by binaryRelation"
    mycursor.execute(query)
    result = mycursor.fetchall()
    rels = {}
    for vals in result:
        rels[vals['binaryRelation']] = vals['size']
    return rels

# getTrueHeirarchy gets the true hierarchy from the csv file
def getTrueHeirarchy(rels):
    data = pd.read_csv(trueHeirarchyFile,header=None)
    heirarchy = [(x,y) for x,y in zip(data[0],data[1]) if x in rels and y in rels]
    return heirarchy

# getHeirarchy creates the hierarchy with the best F1 score given the scores
def getHeirarchy(scores, heirarchy, toPrint):
    allPositives = len(heirarchy)
    truePositives = 0
    totalSet = 0
    prevScore = -1
    bestF1Score = -1
    cutoff = 0
    finalSize = 0
    finalPrecision = 0
    finalRecall = 0
    for (score,rel1,rel2) in scores:
        if score != prevScore and truePositives > 0:
            recall = truePositives/allPositives
            precision = truePositives/totalSet
            # print ("Precision:",precision, "Recall:",recall)
            f1 = 2 * precision * recall / (precision + recall)
            if f1 > bestF1Score:
                bestF1Score = f1
                cutoff = prevScore
                finalSize = totalSet
                finalRecall = recall
                finalPrecision = precision
        if (rel1,rel2) in heirarchy:
            truePositives += 1
        else:
            pass
            # print(rel1 + "," + rel2)
        totalSet += 1
        prevScore = score
    recall = truePositives/allPositives
    precision = truePositives/totalSet
    f1 = 2 * precision * recall / (precision + recall)
    if f1 > bestF1Score:
        bestF1Score = f1
        cutoff = 0
    if toPrint:
        print("Best F1 Score:",bestF1Score)
        print("Cutoff:",cutoff)
        print("Num Relations:",finalSize)
        print("Precision:",finalPrecision)
        print("Recall:",finalRecall)
    return bestF1Score

# getSimilarityBwEmbeddings is used to find the similarity scores between embeddings for all pairs of relations
def getSimilarityBwEmbeddings(rels,embeddings,support):
    simScores = []
    for rel1 in rels:
        for rel2 in rels:
            if rel1 <= rel2:
                continue
            score = 0
            if norm(embeddings[rel1])*norm(embeddings[rel2])!=0:
                score = dot(embeddings[rel1],embeddings[rel2])/(norm(embeddings[rel1])*norm(embeddings[rel2]))
            if support[rel1] < support[rel2]:
                (rel1,rel2) = (rel2,rel1)
            #print(rel1," ",rel2)
            simScores.append((score,rel1,rel2))
    simScores.sort(reverse=True)
    return simScores

rels = getRelationMapping()
heirarchy = getTrueHeirarchy(rels)
embeddings = getEmbeddingsForRels(rels)
support = getSupportSizes()
simScores = getSimilarityBwEmbeddings(rels,embeddings,support)
getHeirarchy(simScores,heirarchy,True)


