import pandas as pd
import sys
import os
import mysql.connector
from itertools import combinations
import random
import json
import csv

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
    with open('/home/manan/BTP/checkpoint/dbpedia/restricted/transe.embedding.vec.json') as f:
        data = json.load(f)
    return data['rel_embeddings.weight']

relNames = getRelationMapping()
relEmbeddings = getRelationEmbeddings()

with open('relation_embeddings.tsv', 'w', encoding='utf8', newline='') as tsv_file:
   tsv_writer = csv.writer(tsv_file, delimiter='\t', lineterminator='\n')
   for emb in relEmbeddings:
       tsv_writer.writerow(emb)

with open('relation_names.tsv', 'w', encoding='utf8', newline='') as tsv_file:
    for rel in relNames:
        tsv_file.write(rel+"\n")

