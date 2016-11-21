# SEM v2.4.2
[SEM (Segmenteur-Étiqueteur Markovien)](http://www.lattice.cnrs.fr/sites/itellier/SEM.html) is a free NLP tool relying on Machine Learning technologies, especially CRFs. SEM provides powerful and configurable preprocessing and postprocessing. [SEM also has an online version](http://apps.lattice.cnrs.fr/sem/index).

## Main SEM features
1. segmentation
   1. segmentation for: French, English
   2. easy creation and integration of new tokenisers
2. feature generation
   1. XML file to write features without coding them
   2. single-token and multi-token dictionary features
   3. Regular expression features
   4. sequenced features
   5. train/label mode
   6. display option for features that are useful for generation, but not needed in output
3. exporting output
   1. supported export formats: CoNLL, text, HTML (from plain text)
   2. easy creation and integration of new exporters
4. extension of existing features
   1. automatic integration of new segmenters and exporters
   2. semi automatic integration of new feature functions
   3. easy creation of new CSS formats for HTML exports

## first steps before using SEM
1. make Wapiti
   1. open a terminal in ext/
   2. type "make" (".\make.bat" on Windows) without quotes
   3. note: on Windows, either install [POSIX threads for Windows](https://sourceforge.net/p/pthreads4w/wiki/Home/) or disable them as explained in ext/src/wapiti.h
2. uncompress models in resources/models/*
3. run tests
   1. python sem --test

## External resources used by SEM
1. [French Treebank](http://www.llf.cnrs.fr/fr/Gens/Abeille/French-Treebank-fr.php) by [Abeillé et al. (2003)](http://link.springer.com/chapter/10.1007%2F978-94-010-0201-1_10): corpus used for POS and chunking.
2. NER annotated French Treebank by [Sagot et al. (2012)](https://halshs.archives-ouvertes.fr/file/index/docid/703108/filename/taln12ftbne.pdf): corpus used for NER.
3. [Lexique des Formes Fléchies du Français (LeFFF)](http://alpage.inria.fr/~sagot/lefff.html) by [Clément et al. (2004)](http://www.labri.fr/perso/clement/lefff/public/lrec04ClementLangSagot-1.0.pdf): french lexicon of inflected forms with various informations, such as their POS tag and lemmatization.
4. [Wapiti](http://wapiti.limsi.fr) by [Lavergne et al. (2010)](http://www.aclweb.org/anthology/P10-1052): linear-chain CRF library.
5. Windows only: [MinGW64](https://sourceforge.net/projects/mingw-w64/?source=navbar): used to compile Wapiti on Windows.
6. Windows only: [POSIX threads for Windows](https://sourceforge.net/p/pthreads4w/wiki/Home/): if you want to multithread Wapiti on Windows.

## latest changes (2.4.0 > 2.4.2)
1. Added sources for manual
2. Improved readme.md
   1. added first steps and external resources
   2. added link to online version
3. tagger module now handles CoNLL-like files again! Hooray!
   1. in master file, within the options section: <file format="conll" fields="your,fields,separated,by,commas,the_field_where_words_are_supposed_to_be" word_field="the_field_where_words_are_supposed_to_be">
4. Wapiti changes
   1. now SEM only uses a local version of Wapiti (available in ext) that needs to be compiled.

## planned changes (no priority)
1. redo triggered features and sequence features.
2. add lemmatiser.
3. migration to python3 ? (already made for revision 39 by lerela).
4. translate manual in English.
5. update manual.
6. improve pipeline: allow calling a pipeline within a pipeline.
7. make SEM callable modules the same way segmenters and exporters. This would allow better integration in a pipeline.
8. have more unit tests
9. handle HTML input files for tagger module
   1. create specific tokeniser
   2. need to handles cases such as words cut by a HTML tag
10. improve segmentation
   1. handle URLs starting with country indicator (ex: "en.wikipedia.org")
   2. handle URLs starting with subdomain (ex: "blog.[...]")
