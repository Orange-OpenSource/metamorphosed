# Changes

## Version 4.6.1
* using `uv` instead of `pyenv`

## Version 4.6.0
* new report for inter annotator agreement
* method to replace parts of a graph (not yet in GUI)

## Version 4.5.0
* possiblity to choose best graph in compare mode (to create a AMR file from mulitple annotations)
* new test

## Version 4.4.0
* use different nodes for identical literals in visualizations
* function to modify a variable
* export visualized graphs: option to highlight concepts
* add metadata to exported graphs (sentence, source file, etc) in json
* new tests

## Version 4.3.1
* minor layout changes

## Version 4.3.0
* show top-node in bold font

## Version 4.2.0
* new edit mode: add graph, a simple possibility to join two graphs (via defined coreferent instances)
* set top from instance modify popup
* new tests

## Version 4.1.0
* AMR search improved: search accepts subgraphs with wildcards
* new tests

## Version 4.0.0
* code oriented in a package (`__init__.py`)
* new help: display the definitions or AMR relations (if existing), with option `--relationsdoc`
* validation data is loaded by default (options `--reifications`, `--relations`, `--relationsdoc` for which the needed files are included)
* server is ow started with `./metamorphosed_server.py ...`
* preparation to install with `pip install .` (to be documented)
* tests updated

## Version 3.5.1
* better capture of regex errors in find functions

## Version 3.5.0
* search function AMR improved: if the search string is a valid PENMAN graph, it will search for graphs which contain the given graph
* documention and HTML tooltips updated
* new tests

## Version 3.4.2
* reject more invalid HTTP requests

## Version 3.4.1
* error in edge click corrected
* new tests
* experimental tests with selenium added (currently Chrome only)

## Version 3.4.0
* integrated Smatch++ (https://github.com/flipz357/smatchpp) into `inter_annotator.py` and `server.py`
* added option `--sortcol` to `inter_annotator.py` to sort colums in TSV report file
* test extended
* smatchpp==1.7.0 added to `requirements.txt`

## Version 3.3.0
* show ARGn definitions as tooltip when mouse hovers over PropBank concepts
* correct search in comments
* added a very basic edge predictor which can be subclassed by a more sophisticated tool. It is used when a new edge is added between two instance to predict the most probably edge label
* tests updated

## Version 3.2.1
* modify sentence id's if duplicate in AMR file
* display f-tags and VerbNet semantic roles in documentation (as documented in PropBank)

## Version 3.2.0
* added a script to calculate the inter-annotator agreement (using Smatch F1 or number of differences)
* new tests
* documentation updated

## Version 3.1.0
* buttons to download AMR graphs as SVG
* menu to download all graphs of the file as SVG, PDF or PNG
* tests updates, new tests
* documentation updated

## Version 3.0.3
* retrieve more information from smatch_pm
* dependencies updated

## Version 3.0.2
* file comparison: reload comparison when compared pair is changed

## Version 3.0.1
* coloring issue in comparison mode corrected

## Version 3.0.0
* comparison of multiple files

## Version 2.8.0
* added options to compare two AMR files (e.g. gold and system)
* new tests

## Version 2.7.0
* added tests and coverage control using tox with flake8 and coverage

## Version 2.6.0
* search in comments
* new tests

## Version 2.5.5
* corrected bug when deleting comments
* new test: deleting comments
* typos in README

## Version 2.5.4
* new tests: git add/commit existing backup file

## Version 2.5.3
* git control check improved

## Version 2.5.2
* editing of files not git controlled: Error if the backup file (file + .2) exists already

## Version 2.5.1
* unselect node if not clicking on a node

## Version 2.5.0
* click two nodes to create a new relation 

## Version 2.4.0
* first public version
