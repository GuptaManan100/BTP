# DBpedia Codes

This directory has the code regarding the experiments ran on DBpedia dataset.

- `DBpediaAsTablesCSV` directory is downloaded from https://wiki.dbpedia.org/DBpediaAsTables#h347-2 and contains the DBpedia tables in CSV form.
- `dbpedia.py` takes in 1 argument which is the CSV file to use. It stores all the relations from it in a MySQL database. Refer to the paper for details regarding the structure of the tables.
- `executor.sh` is a driver script that called dbpedia.py with all the files from DBpedia.
- `Restricted` directory contains code regarding the experiments on the restricted dataset with entities from location, organization and person.