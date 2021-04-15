import pandas as pd
import sys
import os
import mysql.connector
from itertools import combinations
import random

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
    binaryRels = {}
    count = 0
    for vals in result:
        binaryRels[vals['binaryRelation']] = count
        count = count+1
    return binaryRels

# getEntityMapping maps all the entities in the restricted dataset to unique integers
def getEntityMapping():
    query = "select * from dbpedia_restricted_entities order by value"
    mycursor.execute(query)
    result = mycursor.fetchall()
    binaryRels = {}
    count = 0
    for vals in result:
        binaryRels[vals['value']] = count
        count = count+1
    return binaryRels

# getSupportSet gets the support set in the restricted dataset for the given binary relation
def getSupportSet(binaryRel):
    query = "select lhs,rhs from dbpedia_relations where binaryRelation = '"+ binaryRel +"' and lhs in (select * from dbpedia_restricted_entities) and rhs in (select * from dbpedia_restricted_entities)"
    mycursor.execute(query)
    result = mycursor.fetchall()
    supportSet = []
    for vals in result:
        supportSet.append((vals['lhs'],vals['rhs']))
    return supportSet


relMap = getRelationMapping()
entityMap = getEntityMapping()

testList = []
trainList = []
validationList = []

# print the relations and entity mappings
with open("./OpenKEfiles/relation2id.txt","w") as f:
   f.write(str(len(relMap))+"\n")
   for rel in relMap:
       f.write(rel+"\t"+str(relMap[rel])+"\n")

with open("./OpenKEfiles/entity2id.txt","w") as f:
   f.write(str(len(entityMap))+"\n")
   for entity in entityMap:
       f.write(entity+"\t"+str(entityMap[entity])+"\n")

# divide the support sets into train, test and validation
for rel in relMap:
    ss = getSupportSet(rel)
    mappedSS = []
    for (lhs,rhs) in ss:
        if lhs in entityMap and rhs in entityMap:
            mappedSS.append((entityMap[lhs],entityMap[rhs],relMap[rel]))
    random.shuffle(mappedSS)
    totalLen = len(mappedSS)
    trainLen = int(80*totalLen/100)
    testLen = int(90*totalLen/100)

    print(totalLen, trainLen, testLen)

    trainList.extend(mappedSS[0:trainLen])
    testList.extend(mappedSS[trainLen:testLen])
    validationList.extend(mappedSS[testLen:])

    print("CummulativeLengths:",len(trainList),len(testList),len(validationList))

# store the results into the files
with open("./OpenKEfiles/test2id.txt","w") as f:
   f.write(str(len(testList))+"\n")
   for (e1,e2,rel) in testList:
       f.write(str(e1)+"\t"+str(e2)+"\t"+str(rel)+"\n")

with open("./OpenKEfiles/train2id.txt","w") as f:
   f.write(str(len(trainList))+"\n")
   for (e1,e2,rel) in trainList:
       f.write(str(e1)+"\t"+str(e2)+"\t"+str(rel)+"\n")

with open("./OpenKEfiles/valid2id.txt","w") as f:
   f.write(str(len(validationList))+"\n")
   for (e1,e2,rel) in validationList:
       f.write(str(e1)+"\t"+str(e2)+"\t"+str(rel)+"\n")


