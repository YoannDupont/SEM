# SEM v2.4.0
[SEM (Segmenteur-Étiqueteur Markovien)](http://www.lattice.cnrs.fr/sites/itellier/SEM.html) is a free NLP tool relying on Machine Learning technologies, especially CRFs. SEM provides powerful and configurable preprocessing and postprocessing.

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

## latest changes (2.3.4 > 2.4.0)
1. Wapiti changes
   1. now SEM only uses a local version of Wapiti (available in ext) that needs to be compiled.
2. export module changes
   1. export now behaves like segmentation: different export modules are available in obj/exporters
   2. export "flavours" are in obj/exporters
3. tokeniser changes
   1. updated French tokeniser
   2. updated English tokeniser
   3. added support for urls and emails in obj/constants.py
4. Software module changes
   1. removed object oriented "Software" object. Replaced by global variables and methods
   2. SEM information now generated in MarkDown format.
5. unit tests
   1. first unit tests added.
6. correction: added is_boolean switch to list features.

## planned changes (no priority)
1. redo triggered features and sequence features.
2. add lemmatiser.
3. migration to python3 ? (already made for revision 39 by lerela).
4. translate manual in English.
5. update manual.
6. improve pipeline: allow calling a pipeline within a pipeline.
7. make SEM callable modules the same way segmenters and exporters. This would allow better integration in a pipeline.
8. have more unit tests
9. handle CoNLL-formatted input files for tagger module
10. handle HTML input files for tagger module
   1. create specific tokeniser
   2. need to handles cases such as words cut by a HTML tag
11. improve segmentation
   1. handle URLs starting with country indicator (ex: "en.wikipedia.org")
   2. handle URLs starting with subdomain (ex: "blog.[...]")
12. make module objects using the same principle as for tokenisers or exporters.
