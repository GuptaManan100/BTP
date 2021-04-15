import pandas as pd
import sys
import os
import mysql.connector

count = 0

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password=""
)

mycursor = mydb.cursor(dictionary=True)

# create tables if they do not exist
mycursor.execute("use btp")
mycursor.execute("create table if not exists dbpedia_relations(id int primary key AUTO_INCREMENT, lhs varchar(300),binaryRelation varchar(300), rhs varchar(300));")
mycursor.execute("create table if not exists dbpedia_types(id int primary key AUTO_INCREMENT, value varchar(300),typeList varchar(300));")
mycursor.execute("create table if not exists dbpedia_files(id int primary key AUTO_INCREMENT, filename varchar(1000));")

# encode_string is used to escape out strings so that they can be passed in a MySQL query
def encode_string(str):
	ans = ""
	for c in str:
		if c in ['`','"',"'",'\\',]:
			ans += '\\'
		ans += c
	return ans

# insertRelation inserts a triplet into dbpedia_relations table
def insertRelation(lhs, binaryRelation, rhs):
	if type(lhs) != str or type(binaryRelation) != str or type(rhs) != str:
		print(lhs,binaryRelation,rhs)
		return
	query = "insert ignore into dbpedia_relations(lhs,binaryRelation,rhs) values('" + encode_string(lhs) + "','" + encode_string(binaryRelation) + "','" + encode_string(rhs) +"')"
	if len(lhs) > 300 or len(binaryRelation)> 300 or len(rhs) > 300:
		print(query)
	else:
		mycursor.execute(query)

# insertTypes inserts the type list for an entity in the dbpedia_types table
def insertTypes(val, typeList):
	if type(val) != str or type(typeList) != str:
		print(val,typeList)
		return
	query = "insert ignore into dbpedia_types(value,typeList) values('" + encode_string(val) + "','" + encode_string(typeList) +"')"
	if len(val) > 300 or len(typeList)> 300:
		print(query)
	else:
		mycursor.execute(query)

filename = sys.argv[1]
print(filename)

# check if the relations from the file have already been extracted
mycursor.execute("select * from dbpedia_files where filename = "+"'"+ encode_string(filename) +"'")
records = mycursor.fetchall()
isempty = not records

# only iterate if the records are not stored
if isempty:
	# insert the filename into the table so that it is not rerun
	mycursor.execute("insert into dbpedia_files (filename) values ("+"'"+ encode_string(filename) +"')")

	# read the file
	data = pd.read_csv(filename,compression='gzip',dtype=object)
	cols = data.columns

	useColIndexes = []
	useColNames = []
	typeIndex = 0

	idx = 2
	# remove columns that do not correspond to relations
	while idx < len(cols):
		if cols[idx] == '22-rdf-syntax-ns#type_label':
			typeIndex = idx
			break
		if cols[idx].endswith('_label'):
			useColNames.append(cols[idx+1])
			useColIndexes.append(idx)
			idx = idx+2
		else:
			useColNames.append(cols[idx])
			useColIndexes.append(idx)
			idx = idx+1

	# print(useColIndexes,useColNames)
	# print(typeIndex)

	# store all the relations from all the rows
	for index, row in data.iterrows():
		if row['URI'] =='URI' or row['URI'] == 'http://www.w3.org/2002/07/owl#Thing' or pd.isnull(row[1]):
			continue
		elemVal = row[1]
		for x in range(len(useColIndexes)):
			idx = useColIndexes[x]
			name = useColNames[x]
			if pd.isnull(row[idx]):
				continue
			val = row[idx]
			if val[0] == '{':
				for v in (val[1:-1].split('|')):
					insertRelation(elemVal,name,v)
			else:
				insertRelation(elemVal,name,val)

		# insert the type value for the entity
		val = row[typeIndex]
		insertTypes(elemVal,val)
	mydb.commit()
else:
	print(records)
