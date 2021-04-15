import pandas as pd
import sys
import os
import mysql.connector
from itertools import combinations

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password=""
)

mycursor = mydb.cursor(dictionary=True)

# create the tables if they dont exist
mycursor.execute("use btp")
mycursor.execute("create table if not exists dbpedia_support_size_restricted(binaryRelation varchar(300) PRIMARY KEY, size int);")
mycursor.execute("create table if not exists dbpedia_intersect_size_restricted(binaryRel1 varchar(300),binaryRel2 varchar(300), size int, PRIMARY KEY (binaryRel1, binaryRel2));")
# table to store the restricted entity types
mycursor.execute("create table if not exists dbpedia_restricted_entities select distinct value from dbpedia_types where (typeList like '%Person%' or typeList like '%Organization%' or typelist like '%Location%')")

# getTotalLen finds the size of the support set of the given binary relation if the entity types are restricted
def getTotalLen(binaryRel):
    query = "select count(*) as 'c' from dbpedia_relations where binaryRelation = '"+ binaryRel +"' and lhs in (select * from dbpedia_restricted_entities) and rhs in (select * from dbpedia_restricted_entities)"
    #print(query)
    mycursor.execute(query)
    result = mycursor.fetchall()
    return result[0]['c']

# getSupportSet is used to return the support set of the given binary relation if the entity types are restricted
def getSupportSet(binaryRel):
    query = "select lhs,rhs from dbpedia_relations where binaryRelation = '"+ binaryRel +"' and lhs in (select * from dbpedia_restricted_entities) and rhs in (select * from dbpedia_restricted_entities) order by lhs,rhs"
    #print(query)
    mycursor.execute(query)
    result = mycursor.fetchall()
    supportSet = []
    for vals in result:
        supportSet.append((vals['lhs'],vals['rhs']))
    return supportSet

# getIntersectLen gets the size of the intersection between the two support sets provided.
# It assumes that they are already sorted and uses a 2 pointer approach to find the intersection size.
def getIntersectLen(supportSet1, supportSet2):
    size = 0
    idx1 = 0
    idx2 = 0
    len1 = len(supportSet1)
    len2 = len(supportSet2)
    while idx1 < len1 and idx2 < len2:
        x = compareRel(supportSet1[idx1],supportSet2[idx2])
        if x == 0:
            size = size + 1
            idx1 = idx1 + 1
            idx2 = idx2 + 1
        elif x == 1:
            idx2 = idx2 + 1
        else:
            idx1 = idx1 + 1
    return size

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

# getAllRelations returns all the binaryRelations from the table dbpedia_relations.
def getAllRelations():
    query = "select distinct binaryRelation from dbpedia_relations"
    #print(query)
    mycursor.execute(query)
    result = mycursor.fetchall()
    binaryRels = []
    for vals in result:
        for v in vals.values():
            binaryRels.append(v)
    return binaryRels

allRels = getAllRelations()
print("read all relations")

# storeLen is used to store the size of the restricted support set
def storeLen(binaryRel,size):
    query = "insert into dbpedia_support_size_restricted values ('" + binaryRel + "',"+str(size)+ ")"
    #print(query)
    mycursor.execute(query)

# storeIntersectLen is used to store the size of the intersection of the two binary relations provided.
def storeIntersectLen(binaryRels,size):
    if size == 0:
        return
    query = "insert into dbpedia_intersect_size_restricted values ('" + binaryRels[0] + "','" + binaryRels[1] + "'," +str(size)+ ")"
    #print(query)
    mycursor.execute(query)

storedSS = {}
# get the support sets for all the relations
for rel in allRels:
    storedSS[rel] = getSupportSet(rel)
    print("got the support set of",rel)
   storeLen(rel, getTotalLen(rel))
   mydb.commit()

# store the intersection sizes for all pairs of relations
for pairRel in list(combinations(allRels,2)):
    storeIntersectLen(pairRel,getIntersectLen(storedSS[pairRel[0]],storedSS[pairRel[1]]))
    print(pairRel)
    mydb.commit()

