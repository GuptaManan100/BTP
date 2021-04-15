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

# getAllRestrictedEntities returns all the entities which are of type person, organization or location
def getAllRestrictedEntities():
    query = "select * from dbpedia_restricted_entities"
    mycursor.execute(query)
    result = mycursor.fetchall()
    ents = {}
    for vals in result:
        ents[vals['value'].lower()] = 0
    return ents

# getAllRelationsToConsider returns all the relations with a non empty support set when the entity types are restricted
def getAllRelationsToConsider():
    query = "select binaryRelation from dbpedia_support_size_restricted where size > 0"
    mycursor.execute(query)
    result = mycursor.fetchall()
    rels = []
    for vals in result:
        rels.append(vals['binaryRelation'])
    return rels

# getSupportSet returns the support set for the binary relation provided as input
def getSupportSet(binaryRel):
    query = "select lhs,rhs from dbpedia_relations where binaryRelation = '"+ binaryRel +"' and lhs in (select * from dbpedia_restricted_entities) and rhs in (select * from dbpedia_restricted_entities) order by lhs,rhs"
    mycursor.execute(query)
    result = mycursor.fetchall()
    supportSet = []
    for vals in result:
        supportSet.append((vals['lhs'].lower(),vals['rhs'].lower()))
    return supportSet

# getTrueHeirarchy gets the true hierarchy from the csv file
def getIntersection(supportSet1, supportSet2):
    intersect = []
    idx1 = 0
    idx2 = 0
    len1 = len(supportSet1)
    len2 = len(supportSet2)
    while idx1 < len1 and idx2 < len2:
        x = compareRel(supportSet1[idx1],supportSet2[idx2])
        if x == 0:
            intersect.append(supportSet1[idx1])
            idx1 = idx1 + 1
            idx2 = idx2 + 1
        elif x == 1:
            idx2 = idx2 + 1
        else:
            idx1 = idx1 + 1
    return intersect

# compareRel is used to find which of the two pair of entities provided is smaller than the other
# 1 => rel1 > rel2
# -1 => rel1 < rel2
# 0 => rel1 == rel2
def compareRel(rel1,rel2):
    st1 = rel1[0].lower()
    st2 = rel2[0].lower()
    if st1 < st2:
        return -1
    if st1 > st2:
        return 1
    st1 = rel1[1].lower()
    st2 = rel2[1].lower()
    if st1 < st2:
        return -1
    if st1 > st2:
        return 1
    return 0

# getScoreSet gets the total weight of a support set given the weight of the entities
def getScoreSet(set1, weightedEnts):
    sumTot = 0
    for val in set1:
        sumTot +=  weightedEnts.get(val[0],1) * weightedEnts.get(val[1],1)
    return sumTot

# getWeightedWilsonScore gets the weight score for the two relations.
def getWeightedWilsonScore(rel1, rel2, weightedEnts):
    # get the support sets and the intersection
    s1 = getSupportSet(rel1)
    s2 = getSupportSet(rel2)
    intersect = getIntersection(s1,s2)
    # get the score of the intersection and the support sets
    # use them to find the wilson score
    intsize = getScoreSet(intersect,weightedEnts)
    totSize = getScoreSet(s1, weightedEnts)
    if totSize == 0:
        print(rel1)
        return 0
    return wilson(intsize/totSize,totSize)

# getAllWeightedWilsonScores gets all the weighted wilson scores for all the pair of relations with non empty intersection
def getAllWeightedWilsonScores(rels, weightedEnts):
    allInters = getAllIntersections()
    relsWithScore = []
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

        score = getWeightedWilsonScore(rel1,rel2,weightedEnts)
        relsWithScore.append((score,rel2,rel1))
    relsWithScore.sort(reverse=True)
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

# getAllWeightedEntities gets all the entities and provides weights to them
def getAllWeightedEntities(rels):
    allEntities = getAllRestrictedEntities()
    for rel in rels:
        query = "select distinct lhs from dbpedia_relations where binaryRelation = '"+rel+"' union distinct select distinct rhs from dbpedia_relations where binaryRelation = '"+ rel + "';"
        mycursor.execute(query)
        result = mycursor.fetchall()
        for vals in result:
            ent = vals['lhs']
            if ent in allEntities:
                allEntities[ent] = allEntities[ent]+1
    tot = len(rels)
    for ent in allEntities.keys():
        allEntities[ent] = (tot - allEntities[ent])/tot
    return allEntities


rels = getAllRelationsToConsider()
weightedEnts = getAllWeightedEntities(rels)
scores = getAllWeightedWilsonScores(rels,weightedEnts)
heirarchy = getTrueHeirarchy(rels)
getHeirarchy(scores,heirarchy, True)


