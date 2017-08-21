# SEM v2.5.4
[SEM (Segmenteur-Étiqueteur Markovien)](http://www.lattice.cnrs.fr/sites/itellier/SEM.html) is a free NLP tool relying on Machine Learning technologies, especially CRFs. SEM provides powerful and configurable preprocessing and postprocessing. [SEM also has an online version](http://apps.lattice.cnrs.fr/sem/index).

## Main SEM features
1. A GUI for easier use (requires TkInter)
   1. On Linux: double-clic on sem_gui.sh (or launch "bash ./sem_gui.sh" in a terminal)
   2. On Windows: double-clic on sem_gui.bat (or launch ".\sem_gui.bat" in a terminal)
2. segmentation
   1. segmentation for: French, English
   2. easy creation and integration of new tokenisers
3. feature generation
   1. XML file to write features without coding them
   2. single-token and multi-token dictionary features
   3. Regular expression features
   4. sequenced features
   5. train/label mode
   6. display option for features that are useful for generation, but not needed in output
4. exporting output
   1. supported export formats: CoNLL, text, HTML (from plain text), two XML-TEI (one specific to NP-chunks and another one for the rest)
   2. easy creation and integration of new exporters
5. extension of existing features
   1. automatic integration of new segmenters and exporters
   2. semi automatic integration of new feature functions
   3. easy creation of new CSS formats for HTML exports

## First steps before using SEM
1. make Wapiti
   1. uncompress ext/wapitiXXX.tar.gz (where XXX is an optional version number)
   2. open a terminal in ext/wapiti
   3. type "make" (".\make.bat wapiti" on Windows) without quotes. Note for Windows: if compilation fails, check you use the right gcc (see in make.bat)
   4. note: on Windows, either install [POSIX threads for Windows](https://sourceforge.net/p/pthreads4w/wiki/Home/) or disable them as explained in ext/src/wapiti.h
2. run tests
   1. python sem --test
3. run SEM
   1. run GUI (see "main features" above) and annotate "non-regression/fr/in/segmentation.txt"
   2. OR: run ```python sem tagger resources/master/fr/NER.xml ./non-regression/fr/in/segmentation.txt -o sem_output```

## External resources used by SEM
1. [French Treebank](http://www.llf.cnrs.fr/fr/Gens/Abeille/French-Treebank-fr.php) by [Abeillé et al. (2003)](http://link.springer.com/chapter/10.1007%2F978-94-010-0201-1_10): corpus used for POS and chunking.
2. NER annotated French Treebank by [Sagot et al. (2012)](https://halshs.archives-ouvertes.fr/file/index/docid/703108/filename/taln12ftbne.pdf): corpus used for NER.
3. [Lexique des Formes Fléchies du Français (LeFFF)](http://alpage.inria.fr/~sagot/lefff.html) by [Clément et al. (2004)](http://www.labri.fr/perso/clement/lefff/public/lrec04ClementLangSagot-1.0.pdf): french lexicon of inflected forms with various informations, such as their POS tag and lemmatization.
4. [Wapiti](http://wapiti.limsi.fr) by [Lavergne et al. (2010)](http://www.aclweb.org/anthology/P10-1052): linear-chain CRF library.
5. Windows only: [MinGW64](https://sourceforge.net/projects/mingw-w64/?source=navbar): used to compile Wapiti on Windows.
6. Windows only: [POSIX threads for Windows](https://sourceforge.net/p/pthreads4w/wiki/Home/): if you want to multithread Wapiti on Windows.
7. GUI-specific: [TkInter](https://wiki.python.org/moin/TkInter): if you want to launch SEM's GUI.

## Latest changes (2.4.0 > 2.5.4)
1. Corrected bug in text exporter. It required all POS, chunking and NER fields. It is no longer the case
2. Added a GUI
   1. On Linux: double-clic on sem_gui.sh (or launch "bash ./sem_gui.sh" in a terminal)
   2. On Windows: double-clic on sem_gui.bat (or launch ".\sem_gui.bat" in a terminal)
3. Improved model for NER
4. Models are now automatically extracted using tagger module
5. Output directory now automatically created for tagger module
6. Added "ontology" feature
   1. an ontology is just a set of dictionaries that will all be matched on the same column.
7. Improved readme.md
   1. more details left and right.
8. tagger module now handles CoNLL-like files again! Hooray!
   1. in master file, within the options section: ```<file format="conll" fields="your,fields,separated,by,commas,the_field_where_words_are_supposed_to_be" word_field="the_field_where_words_are_supposed_to_be">```
9. chunking_fscore module created to evaluate tasks like named entities.
   1. only works for IOB tagging scheme for now.

## Planned changes (no priority)
1. Add a tutorial.
2. redo triggered features and sequence features.
3. add lemmatiser.
4. migration to python3 ? (already made for revision 39 by lerela).
5. translate manual in English.
6. update manual.
7. improve pipeline: allow calling a pipeline within a pipeline.
8. make SEM callable modules the same way segmenters and exporters. This would allow better integration in a pipeline.
9. have more unit tests
10. handle HTML input files for tagger module
   1. create specific tokeniser
   2. need to handles cases such as words cut by a HTML tag
11. improve segmentation
   1. handle URLs starting with country indicator (ex: "en.wikipedia.org")
   2. handle URLs starting with subdomain (ex: "blog.[...]")
12. create tagger modules
   1. Translate wapiti tagging part to python. No call to executable, no api, no make.
13. use real python package architecture

## SEM references (with task[s] of interest)
1. [TELLIER, Isabelle, DUCHIER, Denys, ESHKOL, Iris, et al. Apprentissage automatique d'un chunker pour le français. In : TALN2012. 2012. p. 431–438.](https://hal.archives-ouvertes.fr/hal-01174591/document)
   1. Chunking
2. [TELLIER, Isabelle, DUPONT, Yoann, et COURMET, Arnaud. Un segmenteur-étiqueteur et un chunker pour le français. JEP-TALN-RECITAL 2012](http://anthology.aclweb.org/F/F12/F12-5.pdf#page=27)
   1. Part-Of-Speech Tagging
   2. chunking
3. (best RECITAL paper award) [DUPONT, Yoann. Exploration de traits pour la reconnaissance d’entités nommées du Français par apprentissage automatique. RECITAL, 2017, p. 42.](http://taln2017.cnrs.fr/wp-content/uploads/2017/06/actes_RECITAL_2017.pdf#page=52)
   1. Named Entity Recognition (new, please use this one)
4. [DUPONT, Yoann et PLANCQ, Clément. Un étiqueteur en ligne du Français. session démonstration de TALN-RECITAL, 2017, p. 15.](http://taln2017.cnrs.fr/wp-content/uploads/2017/06/actes_TALN_2017-vol3.pdf#page=25)
   1. Online interface
5. [DUPONT, Yoann et TELLIER, Isabelle. Un reconnaisseur d’entités nommées du Français. session démonstration de TALN, 2014, p. 40.](http://www.aclweb.org/anthology/F/F14/F14-3.pdf#page=42)
   1. Named Entity Recognition (old, please do not use)
