# DBpedia-Restricted-GNN

This directory has the code regarding the experiments ran on DBpedia dataset with restricted entity types with TransE algorithm.

- `generateFilesForOpenKE.py` is used to populate the `OpenKEfiles` directory with the inputs for the TransE algorithm. The implementation of the algorithm that we use is at http://openke.thunlp.org/
- `train_dbpedia.py` contains the code to run the OpenKE package with the input files.
- `job_dbpedia_restricted_transe.yaml` contains the code used to sumbit the job on kubernetes for getting the OpenKE output
- `visualizeRelations.py` is used to get 2 TSV files which can be used to visualize the embeddings for the relations outputed from TransE on https://projector.tensorflow.org/
- `getHeirarchyRestrictedGNN.py` is used to get the heirarchy for restricted dataset with the best F1 score using the similarity-based approach with TransE embeddings
- `simScoresOutput.txt` stores the output for running the similarity-based approach with TransE embeddings
- `getHeirarchyRestrictedGNNml.py` is used to get the heirarchy for restricted dataset with the best F1 score using the machine-learning-based approach with TransE embeddings
- `Mloutput.txt` stores the output for running the machine-learning-based approach with TransE embeddings