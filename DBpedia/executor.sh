#!/bin/bash
for filename in DBpediaAsTablesCSV/csv/*; do
	python3 dbpedia.py $filename
done