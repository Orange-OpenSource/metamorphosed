# metAMoRphosED: the AMR editor

* _metAMoRphosED_ is a graphical editor to edit Abstract Meaning Representations graphs (in PENMAN) format easily. _metAMoRphosED_ displays the graph in a graphical format and allows adding/deleting instances, edges, attributes and comments in a simple way.
* _metAMoRphosED_ reads and writes AMR-files as proposed by the principal AMR site (https://amr.isi.edu/) and used in the AMr corpora proposed there and
by LDC (https://catalog.ldc.upenn.edu/LDC2020T02)
* _metAMoRphosED_ runs as a local Web server, an internet browser must be used to navigate through the sentences and modifiy them. If the edited file is under git version control, every modification is automatically commited to the local repository.
* _metAMoRphosED_ can be started in comparison mode in order to compare two AMR files (e.g. a gold file and a system file, see section [AMR file comparison](#amr-file-comparison))
* _metAMoRphosED_ provides to annotate coreferences in AMR graphs of sentences from a single text. See [coref/README.md](coref/README.md) for more information
* _metAMoRphosED_ allows to download the displayed graphs as SVG or to export all graphs in either SVG, PDF or PNG format
* _metAMoRphosED_ provides a script to calculate inter-annotator agreement (see section [Inter-annotator agreement](#inter-annotator-agreement))


Current version 3.3.0 (see [CHANGES.md](CHANGES.md))

## installation

### Linux 
python 3.10

```
apt install graphviz
python3 -m venv VENV
source VENV/bin/activate
pip install -r requirements.txt
git submodule update --init
pushd propbank-frames/frames;
  git checkout ad2bafa4c9c9c58cc1bc89;
  wget https://raw.githubusercontent.com/propbank/propbank-frames/development/frames/AMR-UMR-91-rolesets.xml
popd
```

### Mac
```
brew install graphviz
python3 -m venv VENV
source VENV/bin/activate
pip install -r requirements.txt
git submodule update --init
pushd propbank-frames;  git checkout ad2bafa4c9c9c58cc1bc89; popd
```

Note: For the PropBank frames, we need currently this intermediary version since the main and release-v3.4.1 branches 
do not contain the definition of roles like `be-located-at-91`.

also needed: 
* graphviz (see above `sudo apt install graphviz`)
* https://code.jquery.com/jquery-3.6.0.min.js
* https://cdnjs.cloudflare.com/ajax/libs/jquery-modal/0.9.2/jquery.modal.min.js
* https://cdnjs.cloudflare.com/ajax/libs/jquery-modal/0.9.2/jquery.modal.min.css
* https://jqueryui.com/resources/download/jquery-ui-1.13.2.zip

the latter three must be installed in `gui/lib` via the following commands

```
mkdir -p gui/lib
wget https://code.jquery.com/jquery-3.6.0.min.js -O gui/lib/jquery-3.6.0.min.js
wget https://cdnjs.cloudflare.com/ajax/libs/jquery-modal/0.9.2/jquery.modal.min.js -O gui/lib/jquery.modal-0.9.2.min.js
wget https://cdnjs.cloudflare.com/ajax/libs/jquery-modal/0.9.2/jquery.modal.min.css -O gui/lib/jquery.modal-0.9.2.min.css
wget https://jqueryui.com/resources/download/jquery-ui-1.13.2.zip -O gui/lib/jquery-ui-1.13.2.zip
pushd gui/lib/
unzip jquery-ui-1.13.2.zip
popd
```


## tests

```
pytest unittests.py -vv [-k testname] [-s]
```

For more complete testing use `tox`:

```
pip install -r requirements-test.txt
tox
```


## run

```
<install-path>/server.py -f <amr-file> \
	[-p <port>] \
	[--relations <relations.txt>]
	[--concepts <concepts.txt>]
	[--pbframes <propbank-frames-dir>]
	[--constraints <constraints.yml>]
        [--reifications <reification-table.txt]
        [--readonly]
        [--author 'Name <mail@example.com>']
        [--compare <amr-file2>]
```

use our internet browser as GUI: https://localhost:<port>


* The `relations.txt` file must contain all the relations which are valid in the AMR graphs, the editor will show a warning for each relation found in a graph which is not mentioned in this file. The relations will also used for autocompletion
* If `--concepts concepts.txt` is given, the concepts will be used for autocompletion.
* The option `--reifications` loads a table with relations which can be reified ([reification-able.txt](reification-able.txt))
* `propbank-frames-dir` is the `frames` directory within the directory where `https://github.com/propbank/propbank-frames` has been cloned
* If the edited file is under git version control, every click on `save` will create a git commit. In order to use a different user name, specify the user with `--author 'Name <mail@example.com>'`
* `constraints.yml` a file which defines predicate and object constraints (i.e. no other predicate and object is allowed in a given context. E.g.

```
subjects:
  # name-instances must only have :opN predicates, which have quoted strings as objects (initial _ indicates that the predicated or object is a regex
  name:
    _:op\d:
      - _".*"

  # date-entity instances must only have :month, :day and :year predicates with integer values as objects
  date-entity:
    :month:
      - _\d\d?
    :day:
      - _\d\d?
    :year:
      - _\d\d\d\d

  # (Non AMR) a hotel instances can only have :lieu relation to an address instance or a :starts relation to a hotelclass instance
  hotel:
    :lieu :
      - address
    :stars:
      - hotelclass

  # an and instance dan only have :op1 and :op2 predicates with any object
  and:
    _:op\d:


# constraints for predicates and objects, independent of the subject
predicates:
  :location:
     - city
     - country
  :wiki:
     - _"Q\d+"

  :quant:
     - _\d+
     - _\d\.\d+
```

A predicate with an initial `_` means that the predicate is interpreted as a regex. for example

```
subjects:
...
  and:
    _:op\d:
```

means that an instance of the class `and` may have predicates which match the regex `:op\d`  (":op" followoed by a digit)

Objects with initial `_` means that the object of the predicate is not an instance of a class but a literal which matches the regex.
E.g.

```
predicates:
  :wiki:
     - _"Q\d+"

  :quant:
     - _\d+

```

means that the predicate `:wiki` (starting at any subject) must have a string literal as object which matches `"Q\d+"` (including the quotes!).
The objects of all predicates `:quant` must match `\d+`, i.e. an integer


**Note:** `relations.txt` and `constraints.yml` must not be modified in order not to break the unitary tests. Please use a personalised file.



## Validate AMR files


```
amrdoc.py --validate \
	--rels <relations.txt> \
	--pbframes <propbank-frames-dir> \
	--constraintes <constraints.yml> \
```

if necessary, adapt a copy of `constraints.yml` to your needs.

# Editing

Start the server with an AMR file. The file must have the same format as the official AMR distribution

```
# ::id a sentence id
# ::snt the sentence in plain text
(.... AMR graph in PENMAN notation)

# ::id following id
...
```

After a sentence an empty line must follow. If you start annotating new sentence, the initial PENMAN format must be at least en empty pair of parentheses: `()`

Once the server is up and running click on one of the navigation buttons to load a sentence (`first`, `preceding`, `next`, `last`)
or enter a sentence number and lick `read sentence`. The sentence is shown in PENMAN format and in a graphical visualisation.

If the file being edited is under git control, it will be saved under the same name followed by git add/git commit. Else it is saved using an additional `.2` file suffix. If the edited file is not git controlled and if the file with suffix `.2` exists already, the server exits with an error message.
In this case rename the `.2` file and edit the renamed file.

The graph can be extended/modified by the functions in the `Add concept/edges/names` field:
fill in the fields and hit the add button
* adding new instances /concepts
* adding relations (like `:ARG0` or `:location` between to instances. If the preceded by `/`, the following will be interpreted as a conceptname, so a new instances of this concept will be created first and than used for the new relation. The prefix `//` first tries to find an existing instance of this concept to be used, if this cannot be found, a new instance is created.
* define which instance is the `top instance` (appears on top in the PENMAN notation)
* add a relation and a literal (like `:quant 200`)
* add a name instance and `:op1` etc. to strings
* to download the graphical version as SVG, click on `download image` (see also below section *Export*)

![Main window](doc/main.png)


In order to modify or delete an existing instance or edge, click the instance/edge in the visual graph and use the edit window which opens on the top of the screen

<img src="doc/modify-concept.png" alt="Modify or delete concept"/>

<img src="doc/modify-edge.png" alt="Modify or delete an edge"/>

In oder to attach an edge to another starting instance, just click first on the edge which start point is to be modified (the arrow head turns yellow) and click to the instance/concept note which is the new starting point.
**Note**: literal nodes cannot be the starting point of an edge.

## Search, further info

On the bottom of the main screen propbank definitions for all used concepts is displayed. Clicking on `-` minimizes the sentence/PENMAN/graphics windows.
Basic search is available in the search field

![Minimized sentence/PENMAN/graphics](doc/minimized.png)

The `sentence list` button opens a list of all sentences to choose a particular one.
If the edited file is very large, filters can be applied to shorten the list (which may take too much time to load if not filtered)

![Sentence list](doc/sentencelist.png)

## Reification

If the option `--reificiations` is used, a reifiable relation can be reified (and reversed, if the corresponding concept has no aditional relations. The following graph

![Unreified relation ](doc/unreified.png)

becomes this after reifying `:location`

![Reified relation ](doc/reified.png)

## Graph export

The button `export visualised graphs` opens a menu which allows to download all or a subset of graphs in either SVG, PDF or PNG format.
Choose format and numbers of sentences for which you want the graphic exported (default: all sentences)

![Reified relation ](doc/export_graphs.png)

## Edge prediction

(still Beta)

When creating a new edge (relation) between two instances, _metamorphosed_ tries to guess the most likely label for this relation. The implementation is very simple, if the target instance is of type `name` the guessed relation is `:name`, if the concept of the source instance is `name`, `and` or `or`, the guessed relation is `:op2`, else if the source relations ends with `-01` etc, the guessed relations is `:ARGn`. In moste cases this has to be correct. 
However you can implement or more sophisticated classifier, trained on any data whic is available to you and use your classifier. To do so,
Subclass the class `Basic_EdgePredictor` in [edge_predictor.py](edge_predictor.py) and implement your classifier. You must redefine the method
`predict(self, source_concept, target_concept):`. For instance:

```
from edge_predictor import Basic_EdgePredictor

class Perfect_EdgePredictor(Basic_EdgePredictor):
    def __init__(self, arglist):
        print("initialising my Perfect_EdgePredictor with %s as argument" % arglist[0])
        self.classifier = Perfect_Classifier(arglist[0])

    def predict(self, source_concept, target_concept):
        predicted_label = self.classifier.find(source_concept, target_concept)
        print("predicted label <<<%s>>>" % predicted_label)
	return predicted label
```

In order to use this class and the needed data, create a yaml file `mypredictor.yml`:

```
# __localpath__ is the path where the yaml file is placed in

# filename can also any relative or absolute path
filename: __localpath__/perfect_predictor.py
classname: Perfect_EdgePredictor
args:
  - __localpath__/mydata.dat
```

start _metamorphosed_ with the option `--edge_predictor` (or `-E`):

```
./server.py --edge_predictor mypredictor.yml [other options]
```

# AMR file comparison

If you specify a second AMR file using the option `--compare <amr file>`, _metAMoRphosED_ will show the corresponding graphs of both files side-by-side, highlighting differences (in green) and displaying the [Smatch](https://github.com/snowblink14/smatch) score:

![AMR file comparison ](doc/comparison.png)

It is possible to search in the text, PENAMN and comments as in the edit mode. However, editing is not possible.

To compare several files (for instance the annotations of multiple annotators), specify one of the files using the `-f <amr file 1>` option, and all other with  `--compare <amr file 2> <amr file 3> <amr file 4>`.
_metAMoRphosED_ switches automatically in multifile mode. In order to see the difference (ans Smatch) between two files for the displayed sentence choose the two files to compare with the `comparisons`-selection bar

![AMR file comparison ](doc/comparison-multiple-files.png)

# AMR Coreference editor

see [coref/README.md](coref/README.md)


# Inter-annotator agreement

_metAMoRphosED_ comes with a script which allows to calculate an inter-annotator agreement (IAA) score on 2 or more files containing the same sentences. The metrics used are Smatch F1
or the number if differences between two graphs (each concept or relation which is different or absent in one of the graphs is counted)

The IAA is calculated either by
* for each sentence:
   * calculate a score for each annotator pair and keep the average
   * calculate the average of the score obtained for each sentence
or

* for each annotator pair
   * calculate the score for each sentence and keep the average
   * calculate the average of the score obtained for annotator pair



```
usage: inter_annotator.py [-h] --files FILES [FILES ...] [--sentences] [--debug] [--runs RUNS] [--first FIRST] [--last LAST]

inter-annotator agreement

options:
  -h, --help            show this help message and exit
  --files FILES [FILES ...], -f FILES [FILES ...]
                        AMR files of all annotatoris
  --sentences, -s       sentences are in inner loop
  --debug, -d           debug
  --runs RUNS           run smatch n times to get the best possible match
  --first FIRST         skip first n sentences
  --last LAST           stop after sentences n
  --report, -r REPORT
                        filename for a report in TSV format
```

For instance the for 3 test files provided the IAA can be calculated by
```
inter_annotator.py -f comptest_annot1.txt comptest_annot3.txt comptest_annot4.txt -d
```

which results in:

```
4 sentences read from comptest_annot1.txt
4 sentences read from comptest_annot3.txt
4 sentences read from comptest_annot4.txt
sentence     0: annotator pairs smatch: [69.23, 71.43, 61.54]
                annotator pairs diffs.: [5.0, 4.0, 6.0]
sentence     1: annotator pairs smatch: [66.67, 75.0, 72.73]
                annotator pairs diffs.: [5.0, 4.0, 3.0]
sentence     2: annotator pairs smatch: [40.0, 22.22, 40.0]
                annotator pairs diffs.: [5.0, 6.0, 6.0]
sentence     3: annotator pairs smatch: [62.5, 50.0, 75.0]
                annotator pairs diffs.: [3.0, 4.0, 2.0]
averages for 4 sentences (smatch): [67.4, 71.46, 34.07, 62.5]
                          (diffs): [5.0, 4.0, 5.67, 3.0]
annotator pair inter-annotator agreement Smatch F1: 58.86 differences: 4.4167
```


Using the option `-s` loops on annotator pairs

```
inter_annotator.py -f comptest_annot1.txt comptest_annot3.txt comptest_annot4.txt -d -s
```


which results in:

```
4 sentences read from comptest_annot1.txt
4 sentences read from comptest_annot3.txt
4 sentences read from comptest_annot4.txt
annotators 0/1: sentence comparison smatch: [69.23, 66.67, 40.0, 62.5]
                sentence comparison diffs.: [5.0, 5.0, 5.0, 3.0]
annotators 0/2: sentence comparison smatch: [71.43, 75.0, 22.22, 50.0]
                sentence comparison diffs.: [4.0, 4.0, 6.0, 4.0]
annotators 1/2: sentence comparison smatch: [61.54, 72.73, 40.0, 75.0]
                sentence comparison diffs.: [6.0, 3.0, 6.0, 2.0]
averages for 3 annotator pairs (smatch): [59.6, 54.66, 62.32]
                                (diffs): [4.5, 4.5, 4.25]
sentence inter-annotator agreement Smatch F1: 58.86 differences: 4.4167
```

# License

* This software is under the [3-Clause BSD License](LICENSE)


# Reference

* Johannes Heinecke (2023) metAMoRphosED: a graphical editor for Abstract Meaning Representation. In ISA19 at International Workshop on Computational Semantics. Nancy

```
@inproceedings{heinecke2023,
  author = {Heinecke, Johannes},
  title = {{metAMoRphosED: a graphical editor for Abstract Meaning Representation}},
  year = {2023},
  booktitle = {{19th Joint ACL - ISO Workshop on Interoperable Semantic Annotation}},
  address = {Nancy},
  url = {https://github.com/Orange-OpenSource/metamorphosed/}
}
```
