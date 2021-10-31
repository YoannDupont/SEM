# SEM: a free NLP tool to tag and create annotated data

[SEM (Segmenteur-Étiqueteur Markovien)](http://www.lattice.cnrs.fr/sites/itellier/SEM.html) is a free NLP tool relying on Machine Learning technologies, especially CRFs. SEM provides powerful and configurable preprocessing and postprocessing. [SEM also has an online version](http://apps.lattice.cnrs.fr/sem/index).

## Main SEM features

1. A GUI for manual annotation (requires TkInter)
   1. from terminal: run `sem annotation_gui`
   2. fast annotation: keyboard shortcuts and document-wide annotation broadcast
   3. can load pre-annotated files
   4. support for hierarchical tags (dot-separated, eg: "noun.common")
   5. handles multiple input format
   6. export in different formats
2. A GUI for easier use (requires TkInter)
   1. on Linux: double-clic on sem_gui.sh
   2. on Windows: double-clic on sem_gui.bat
   3. from terminal: run `sem gui`
3. segmentation
   1. segmentation for: French, English
   2. easy creation and integration of new tokenisers
4. feature generation
   1. XML file to write features without coding them
   2. single-token and multi-token dictionary features
   3. Regular expression features
   4. sequenced features
   5. train/label mode
   6. display option for features that are useful for generation, but not needed in output
5. exporting output
   1. supported export formats: CoNLL, text, HTML (from plain text), two XML-TEI (one specific to NP-chunks and another one for the rest)
   2. easy creation and integration of new exporters
6. extension of existing features
   1. automatic integration of new segmenters and exporters
   2. semi automatic integration of new feature functions
   3. easy creation of new CSS formats for HTML exports

## First steps with SEM

1. install SEM
   1. see [install.md](install.md)
   2. It will compile Wapiti and create necessary directories. Currently, SEM datas are located in `~/sem_data`
2. run tests
   1. run `sem --test` in a terminal
3. run SEM
   1. run GUI (see "main features" above) and annotate "non-regression/fr/in/segmentation.txt"
   2. or run: `sem tagger resources/master/fr/NER.xml ./non-regression/fr/in/segmentation.txt -o sem_output`
4. (optional) go through the [SEM tutorial](https://github.com/YoannDupont/SEM-tutorial)
5. (optional) go through some of the examples given in the `examples` folder.

## External resources used by SEM

1. [French Treebank](http://www.llf.cnrs.fr/fr/Gens/Abeille/French-Treebank-fr.php) by [Abeillé et al. (2003)](http://link.springer.com/chapter/10.1007%2F978-94-010-0201-1_10): corpus used for POS and chunking.
2. NER annotated French Treebank by [Sagot et al. (2012)](https://halshs.archives-ouvertes.fr/file/index/docid/703108/filename/taln12ftbne.pdf): corpus used for NER.
3. [Lexique des Formes Fléchies du Français (LeFFF)](http://alpage.inria.fr/~sagot/lefff.html) by [Clément et al. (2004)](http://www.labri.fr/perso/clement/lefff/public/lrec04ClementLangSagot-1.0.pdf): french lexicon of inflected forms with various informations, such as their POS tag and lemmatization.
4. [Wapiti](http://wapiti.limsi.fr) by [Lavergne et al. (2010)](http://www.aclweb.org/anthology/P10-1052): linear-chain CRF library.
5. [setuptools](https://pypi.python.org/pypi/setuptools): to install SEM.
6. [Tkinter](https://wiki.python.org/moin/TkInter): for GUI modules (they will not be installed if Tkinter is not present).
7. Windows only: [MinGW64](https://sourceforge.net/projects/mingw-w64/?source=navbar): used to compile Wapiti on Windows.
8. Windows only: [POSIX threads for Windows](https://sourceforge.net/p/pthreads4w/wiki/Home/): if you want to multithread Wapiti on Windows.

## SEM source code vs SEM resources

While SEM source code is released under the MIT licence, the resources present in this repository (including but not limited to lexica and models) have each their own licence which may (usually does) differ. SEM provides them for research, teaching and personal use, they may not be used for any other reason. If you wish to create your own models, you will have to provide your own lexica, annotate your own data (or use data annotated under a permissive licence) and train your models yourself. You have to to check every resource licence and its compatibility for your project.

SEM resources are being moved to a specific repository: [SEM-resources](https://github.com/YoannDupont/SEM-resources). SEM will provide means to download them on your computer.

## Planned changes (for latest changes, see changelog.md)

1. add lemmatiser
2. have more unit tests
3. publish some benchmarks

## SEM references (with task[s] of interest)

1. [DUPONT, Yoann et PLANCQ, Clément. Un étiqueteur en ligne du Français. session démonstration de TALN-RECITAL, 2017, p. 15.](http://taln2017.cnrs.fr/wp-content/uploads/2017/06/actes_TALN_2017-vol3.pdf#page=25)
   1. Online interface
2. (best RECITAL paper award) [DUPONT, Yoann. Exploration de traits pour la reconnaissance d’entités nommées du Français par apprentissage automatique. RECITAL, 2017, p. 42.](http://taln2017.cnrs.fr/wp-content/uploads/2017/06/actes_RECITAL_2017.pdf#page=52)
   1. Named Entity Recognition (new, please use this one)
3. [TELLIER, Isabelle, DUCHIER, Denys, ESHKOL, Iris, et al. Apprentissage automatique d'un chunker pour le français. In : TALN2012. 2012. p. 431–438.](https://hal.archives-ouvertes.fr/hal-01174591/document)
   1. Chunking
4. [TELLIER, Isabelle, DUPONT, Yoann, et COURMET, Arnaud. Un segmenteur-étiqueteur et un chunker pour le français. JEP-TALN-RECITAL 2012](http://anthology.aclweb.org/F/F12/F12-5.pdf#page=27)
   1. Part-Of-Speech Tagging
   2. chunking
5. [DUPONT, Yoann et TELLIER, Isabelle. Un reconnaisseur d’entités nommées du Français. session démonstration de TALN, 2014, p. 40.](http://www.aclweb.org/anthology/F/F14/F14-3.pdf#page=42)
   1. Named Entity Recognition (old, please do not use)

## SEM references (bibtex format)

1. 
```latex
@inproceedings{dupont2017etiqueteur,
    title={Un {'e}tiqueteur en ligne du fran{\c{c}}ais},
    author={Dupont, Yoann and Plancq, Cl{'e}ment},
    booktitle={24e Conf{'e}rence sur le Traitement Automatique des Langues Naturelles (TALN)},
    pages={15--16},
    year={2017}
}
```
2. 
```latex
@inproceedings{dupont2017exploration,
  title={Exploration de traits pour la reconnaissance d’entit{'e}s nomm{'e}es du Fran{\c{c}}ais par apprentissage automatique},
  author={Dupont, Yoann},
  booktitle={24e Conf{'e}rence sur le Traitement Automatique des Langues Naturelles (TALN)},
  pages={42},
  year={2017}
}
```
3. 
```latex
@inproceedings{tellier2012apprentissage,
  title={Apprentissage automatique d'un chunker pour le fran{\c{c}}ais},
  author={Tellier, Isabelle and Duchier, Denys and Eshkol, Iris and Courmet, Arnaud and Martinet, Mathieu},
  booktitle={TALN2012},
  volume={2},
  pages={431--438},
  year={2012}
}
```
4. 
```latex
@inproceedings{tellier2012segmenteur,
  title={Un segmenteur-{'e}tiqueteur et un chunker pour le fran{\c{c}}ais (A Segmenter-POS Labeller and a Chunker for French)[in French]},
  author={Tellier, Isabelle and Dupont, Yoann and Courmet, Arnaud},
  booktitle={Proceedings of the Joint Conference JEP-TALN-RECITAL 2012, volume 5: Software Demonstrations},
  pages={7--8},
  year={2012}
}
```
5. 
```latex
@article{dupont2014reconnaisseur,
  title={Un reconnaisseur d’entit{'e}s nomm{'e}es du Fran{\c{c}}ais (A Named Entity recognizer for French)[in French]},
  author={Dupont, Yoann and Tellier, Isabelle},
  journal={Proceedings of TALN 2014 (Volume 3: System Demonstrations)},
  volume={3},
  pages={40--41},
  year={2014}
}
```
