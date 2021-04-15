# DBpedia-Restricted Codes

This directory has the code regarding the experiments ran on DBpedia dataset with restricted entity types.

- `storeScoresRestricted.py` is used to store the restricted entity types, the size of the support sets when the entity types are restricted, and the length of their intersections
- `parent-child-pairs.csv` stores the true hierarchy for the restricted relations.
- `getHeirarchyRestricted.py` runs the PATTY algorithm to create the hierarchy. It outputs the best F1 score among other collected information.
- `getHeirarchyRestricted-Weighted.py` runs the PATTY algorithm with the modification of weighted entities.
- `getHeirarchyRestrictedMixed.py` runs the PATTY algorithm with the modification of an additional signal for the meaning of the relations using glove.
- `mixedOutput.txt` stores the output of running the experiment in `getHeirarchyRestrictedMixed.py`
- `weightedOutput.txt` stores the output of running the experiment in `getHeirarchyRestricted-Weighted.py`