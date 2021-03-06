import pandas as pd
import numpy as np
import sys
import os
import mysql.connector
from itertools import combinations
from math import sqrt
from numpy import dot
from numpy.linalg import norm

trueHeirarchyFile = "parent-child-pairs.csv"
embeddingSize = 300

# wilson returns the wilson score given the p and n values
def wilson(p,n,z=1.96):
    denominator = 1 + z**2/n
    centre_adj_prob = p + z*z/(2*n)
    adj_std_dev = sqrt((p*(1-p) + z*z/(4*n))/n)
    lower_bound = (centre_adj_prob - z*adj_std_dev)/denominator
    return lower_bound

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password=""
)

mycursor = mydb.cursor(dictionary=True)

mycursor.execute("use btp")

# getAllIntersections returns all the intersection sizes of the pair of relations along with the support sizes of the relations.
# This is accomplished via a join
def getAllIntersections():
    query = "select dbpedia_intersect_size_restricted.size as 'intersectSize', binaryRel1, s1.size as 'size1', binaryRel2, s2.size as 'size2' from dbpedia_intersect_size_restricted, dbpedia_support_size_restricted s1, dbpedia_support_size_restricted s2 where s1.binaryRelation = binaryRel1 and s2.binaryRelation = binaryRel2"
    mycursor.execute(query)
    result = mycursor.fetchall()
    return result

# getAllRelationsToConsider returns all the relations with a non empty support set when the entity types are restricted
def getAllRelationsToConsider():
    query = "select binaryRelation from dbpedia_support_size_restricted where size > 0"
    mycursor.execute(query)
    result = mycursor.fetchall()
    rels = []
    for vals in result:
        rels.append(vals['binaryRelation'])
    return rels

# getAllWilsonScores gets the wilson scores between all the relations that have non zero intersection sizes
def getAllWilsonScores(rels):
    allInters = getAllIntersections()
    relsWithScore = {}
    for row in allInters:
        intersect = row['intersectSize']
        rel1 = row['binaryRel1']
        rel2 = row['binaryRel2']
        size1 = row['size1']
        size2 = row['size2']

        if rel1 not in rels:
            continue
        if rel2 not in rels:
            continue

        if size1 > size2:
            size1,size2 = size2,size1
            rel1,rel2 = rel2,rel1

        score = wilson(intersect/size1,size1)
        relsWithScore[(rel2,rel1)] = score
    return relsWithScore

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

# getWords is used to split the relation name into words
def getWords(rel):
    words = []
    word = ""
    for c in rel:
        if c >='A' and c<='Z':
            words.append(word)
            word = "" + c.lower()
        else:
            word = word + c
    words.append(word)
    return words

# readGloveEmbeddings is used to read the glove embeddings
def readGloveEmbeddings():
    embeddings_index = {}
    with open("../../glove/glove.6B.300d.txt", encoding="utf-8") as f:
        for line in f:
            word, coefs = line.split(maxsplit=1)
            coefs = np.fromstring(coefs, "f", sep=" ")
            embeddings_index[word] = coefs
    print("Found %s word vectors." % len(embeddings_index))
    return embeddings_index

# getEmbeddingsForRels gets the embeddings for all the relations passed. The method is described in the report.
def getEmbeddingsForRels(rels):
    embeddings_index = readGloveEmbeddings()
    embeddings = {}
    for rel in rels:
        words = getWords(rel)
        embedding = np.zeros(embeddingSize)
        for word in words:
            if word in embeddings_index:
                embedding += embeddings_index[word]
        embedding = embedding / len(words)
        embeddings[rel] = embedding
    return embeddings

# getSimilarityBwEmbeddings is used to find the similarity scores between embeddings for all pairs of relations
def getSimilarityBwEmbeddings(rels,embeddings):
    simScores = {}
    for rel1 in rels:
        for rel2 in rels:
            score = 0
            if norm(embeddings[rel1])*norm(embeddings[rel2])!=0:
                score = dot(embeddings[rel1],embeddings[rel2])/(norm(embeddings[rel1])*norm(embeddings[rel2]))
            simScores[(rel1,rel2)] = score
    return simScores

# getHeirarchyMixed is the function that gets the final scores based on the weight to both signals and call getHeirarchy
def getHeirarchyMixed(alpha,scores,simScores, rels, heirarchy, toPrint):
    beta = 1-alpha
    finalScores = []
    for rel1 in rels:
        for rel2 in rels:
            score = beta * simScores[(rel1,rel2)]
            if (rel1,rel2) in scores:
                score += scores[(rel1,rel2)]*alpha
            finalScores.append((score,rel1,rel2))
    finalScores.sort(reverse=True)
    return getHeirarchy(finalScores,heirarchy,toPrint)

# getBestHeirarchy is used to find the best weight of the paramter used to weigh both the signals
def getBestHeirarchy(scores,simScores,rels,heirarchy):
    print("PATTY")
    bestF1 = getHeirarchyMixed(1,scores,simScores,rels,heirarchy,True)
    bestAlpha = 1

    for alpha in np.linspace(0,1,20,endpoint=False):
        f1 = getHeirarchyMixed(alpha,scores,simScores,rels,heirarchy,False)
        if f1 > bestF1:
            bestF1 = f1
            bestAlpha = alpha

    print("Best Mixed")
    print("Alpha",alpha)
    getHeirarchyMixed(bestAlpha,scores,simScores,rels,heirarchy,True)

rels = getAllRelationsToConsider()
scores = getAllWilsonScores(rels)
heirarchy = getTrueHeirarchy(rels)
embeddings = getEmbeddingsForRels(rels)
simScores = getSimilarityBwEmbeddings(rels,embeddings)
getBestHeirarchy(scores,simScores,rels,heirarchy)


