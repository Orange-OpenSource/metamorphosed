# Uniform Meaning Representation (UMR)

Is a multilingual extension to AMR which also annotates semantic links between sentences of a document, temporal sequences and alignments beween tokens and instances. For more information see the UMR project website at https://umr4nlp.github.io/web/.

_metAMoRphosed_ can handle standard UMR files as provided by the UMR project and described in the [UMR Schema reference](https://umr4nlp.github.io/web/UMRSchemaPages/index.html).

The minimal content of a UMR file which _metAMoRphosed_ is the following:

```
################################################################################
# meta-info :: sent_id = u_tree-cs-s1-root
# :: snt1
Index: 1   2    3 4     5      6       7  8           9         10
Words: 200 dead , 1,500 feared missing in Philippines landslide . 

# sentence level graph:
()

# alignment:

# document level annotation:

```

The only data needed is the structure (lines starting with `#`) and the lines `Words:` and `Index:` which contain the tokens of the sentence and the position of the token in the sentence (starting with 1).

The sentence level graph is usually a PENMAN graph like AMR, but with UMR specific relations and variable names which always start with `sN` with `N` being the sentence number which also show in the line `# :: sntN`.

To use _metAMoRphosed_ in UMR mode, the server has to be started with the additional option `--umr`. Since UMR relations differ from AMR relations, the options 
`--relations` and `--relationsdoc` have to be used (the needed files are in `metamorphosed/data`).
For instance:

```
uv run ./metamorphosed_server.py \
    -f </data/>en-0001.umr \
    --umr \
    --relations metamorphosed/data/umr-relations.txt  
    --relationsdoc metamorphosed/data/umr-relations-doc.json
    --port 4567
```

the options `--relations metamorphosed/data/umr-relations.txt`  `--relationsdoc metamorphosed/data/umr-relations-doc.json` are default options, so strictly speaking they are not necessary.

Open your browser on `http://localhost:4567`. In addtion to the tabs already present for the AMS mode, a new tab `edit UMR document annotation` appears, which proposes option to modify the document level annotations.
In addition the graph visualisation shows alignments (if available):


![Main window for UMR editing](doc/umr-main.png)

## Edit the sentence level graph

This works as with AMR files (see [README.md](README.md))

## Edit the alignments

Alignments are correspondances between instances of the sentence level graph and words of the sentence. The alignments are also shown in the graph visualisation, if the button `show alignments` is checked.
There are three ways to add/modify/delete alignments:

### add alignment
* add a new alignment (i.e. for a variable which is not yet aligned with a word, in our example `s6p2` and `s6s`): click on the word in the `Words:` line and than on the instance in the graph. If the variable you click on, has already an alignment, it is overwritten with the new one
* add a new alignment. Choose the variable in the UMR section on the top left (`H) add new alignment`)

### modify alignement

Click on the alignment in the `Alignments:` line and edit it accordingly and click `set`. If the format is incorrect (startposition - endposition), the input is not accepted and an error message is given.

![Modify UMR alignment](doc/modify-UMR-alignment.png)

An empty input field removes all alignments for the given instance. Separate multiple alignments with a comma: `4-4, 6-6`)

## edit Words/Index/Morphemes etc.

Click on the `Words/Tokens/Morphemes` tab and then on the table. This will open a simple editing interface to modify the Words, Indexes, Morphemes, Glosses etc (if present in the `.umr` file)
Hit `update` to save your modifications

![Modify Words/Indexes etc](doc/modify-UMR-glosses.png)


## Edit the document level annotation

Adding new temporal, modal or coref triples use the input fields on the top left (`I) add docgraph ....`

![Add document annotation triples](doc/docgraph-add.png)

In order to edit (or remove) existing triples, click on a triple and edit it the pop-up. An empty field deletes the triple.
Validate by clicking on `set`, cancel by clicking on the circled `X` (top right)

![Add document annotation triples](doc/docgraph-edit.png)

## Graph export

The button `export visualised graphs` opens a menu which allows to download all or a subset of graphs in either SVG, PDF or PNG format.
Choose format and numbers of sentences for which you want the graphic exported (default: all sentences).
You may choose a (comma separated list) of concepts which will be highlighted in the export visualisations. If you check `add alignments` the graphs contain the alignments between tokens and instances of concepts (as in the editor).

![Reified relation ](doc/umr_export_graphs.png)

The images are downloaded in a .zip file which also contains a `metadata.json` metadata file which contains the sentence id and the text which correspond to the graph.

## Import AMR
Files in the standard AMR format (like ARM 3.0) can be transformed into the UMR format using `AMR2UMR.py`. If alignments are present in the AMR file (suffixed version like `(s / shift-01~e.9 ...`) these alignments are import to the UMR file format. However AMR alignments with relations (`:purpose~e.27`) cannot be used in UMR. They are imported only as comments.

```
uv run AMR2UMR.py AMR.file > UMR.file
```

## Limitations

* `Words:` and `Index:` (and `Morphemes:` etc.) lines cannot yet be deleted or added (they have to be present in the `.umr` file)
* Document level annotations constraints are not yet all enforced

* TODO:
  * check whether variables in document level annotations are in document (Subject) or in current sentence (Object)
