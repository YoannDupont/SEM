# Changelog
All notable changes to SEM will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## Unreleased
### Added
- `read_chunks` iterator to read file by chunks
- `r_open` context manager to open a file from path or wrap string with file methods
- `sem/tests/test_workflows.py`: unit tests for SEM workflows
- `extend` method to `sem/storage.corpus.Corpus`
- `read_conll` method in `sem.importers`: iterator over CoNLL-formatted sentences that yields a list of dict at eah iteration
- `conll_file` method in `sem.importers`: read CoNLL-formatted text from a file
- `conll_data` method in `sem.importers`: create a Document from CoNLL-formatted data (SEM `Corpus`)
### Modified
- french tokenizer now uses chunked input for better scaling
- BRAT reader now replaces '\r' characters with '\n'
- When writting SEM-XML, quotes in the name of the document are now escaped
- `append_sentence` method from `sem/storage/corpus.py`: renamed `append`
- `from_tagset` method from `sem/gui/misc.Adder2`: static method with no reference to class ==> moved out of the class
- version-related variables in `__init__.py` were replaced by `__version`
### Removed
- `has_key` from `sem/storage/corpus.py`: using `__contains__` instead
- `from_sentences` method in `sem/storage/corpus.py`: unused
- `iterate_on_sentences` in `sem/storage/corpus.py`: replaced by `__iter__`
- `corpus_to_unicode` and `corpus_to_file` methods from exporters: not used anymore
- `word_bounds` method from `sem/tokenisers/*.py` where `word_span` is implemented
- `Tokeniser` object hierarchy: transformed as modules
- `last_index` method from `sem/misc.py`: unused
- information-related code in `__init__.py` and `__main__.py`: error inducing and `readme.md` is already created and formatted, so it became useless
- `toXML` method from `sem/storage/annotation.py`: unsued
- `toXML` method from `sem/storage/span.py`: unsued
- `from_xml` method from `sem/modules/pipeline.Pipeline`: unused
- `fromlist` method from `sem/storage/coder.Coder`: unused
- `fromXML` method from `sem/storage/span.Span`: unused
- `sem/IO/__init__.py`: not used anymore
- `sem/IO/columnIO.py`: not used anymore, use `read_conll` instead
- `sem/IO/KeyIO.py`: not used anymore, use `read_conll` instead
- `from_conll` method removed from `sem/storage/document.Document`: rewritten (and improved) in `sem.importers`
- `from_file` method removed from `sem/storage/document.Document`: useless and unused
- `sem/information.py`: not used anymore
- `from_conll` method removed from `sem/storage/corpus.Corpus`: not used anymore, use `sem.importers.read_conll` as argument of `__init__` instead

## [SEM v3.3.0](https://github.com/YoannDupont/SEM/releases/tag/v3.3.0)
### Added
- python3 support
- `sem.importers.load` : `tagset_name` keyword argument added, allows to define the name of the tagset when loading BRAT (instead of hard-coded NER), defaults to NER
- `annotation_gui`: a document list may be loaded at startup with `--document` or `-d` option (can take multiple arguments)
- `annotation_gui`: a tag set may be loaded at startup with `--tagset`or `-t` option
- memory usage improvement: added slots in Span and Tag types
- pipeline_mode in pipeline to allow the use of a pipeline in train or label mode (only one workflow for training and labelling)
- install.md file for installation instructions
- SEM may copy a newly trained model into the right folder in sem_data in order to use it immidiately
- support for SEM documents in `chunking_evaluate`
- method `annotation_from_sentence` to generate annotations (used to remove dupes)
- ability to search text added to annotation_gui, supports regular expression and case insensitivity (shortcut: ctrl+f)
- user can now select to train on either top level annotations or bottom level annotations when annotations are nested
- first version of the manual in English
- user can now select language when training from annotation_gui
### Changed
- Entry object moved from informations.py to corpus.py
- most string formatting with "%" now replaced with string.format method
- improving french tokeniser performance on numerous little texts: regexp are now compiled once and for all
- corrected bug in french tokeniser when document only had one token and no spaces
- `chunking_evaluate` now also works for POS => renaming module `evaluate`
- corrected a bug when training in `annotation_gui` that could break annotations in some cases
- improved memory consumption when training a new SEM model
- corrected a bug when there was no french language defined in SEM data
- corrected a bug disallowing user to "save as..." in certain context
### Removed
- Information object removed, its useful parts are now in the sem.modules.enrich.SEMModule object.
- informations.py file removed, it is now part of the enrich module
- code refactoring: removal of duplicated methods for generating Annotation from CoNLL files

## [SEM v3.2.0](https://github.com/YoannDupont/SEM/releases/tag/v3.2.0)
### Added
- support for "whole word" matching when broadcasting annotation in annotation_gui
- logging in GUI: output directory now logged
- added imports in sem/IO/__init__.py
- module `chunking_evaluate`: a module that will compute various metrics. Will replace the module `chunking_fscore`
- new section in manual: how to train a new model with SEM
- explicit handling of annotated CoNLL files. Use attribute `taggings` for taggins such as POS and `chunkings` for BIO-formatted taggings such as chunking or NER: `<file format="conll" fields="field1,field2,POS,NER" word_field="field1" taggings="POS" chunkings="NER" />`
### Changed
- better matching between annotations and tokens in Document.add_to_corpus method
- corrected a bug when comma was in the middle of a token
- reordered and cleaned file hierarchy for manual
- handling of a too long text when trying to match an abbreviation to a long form
- improved speed when training a SEM model
- corrected a bug when an annotation spanned over multiple sentences
- modified french segmentation: "X." where X is an uppercase is left as is
- corrected some typos in __main__.py
- renamed "KeyIO.py" to "keyIO.py"
- in `label_consistency`, use whole document if no sentence segmentation
- corrected a bug when changing reference segmentation
- SEM can now train wapiti models. Required several changes
- corrected setup: when missing resource file is directory, use copy_tree
- BRAT importer: handling discontinuous annotations. A single annotation is created covering the whole span
- BRAT importer: sorting annotations
- BRAT importer: better handling of annotation information
- GUI: corrected bug when giving pattern file for training SEM
- annotation_gui: user can now export annotated corpus as BRAT, GATE, TEI (Analec and REDEN), json
### Removed
- exporter "dispatch", used to load exporter from name
### Deprecated
- module `chunking_fscore`: will be replaced by `chunking_evaluate` which will be more thorough

## [SEM v3.1.2](https://github.com/YoannDupont/SEM/releases/tag/v3.1.2)
### Added
- Added method "word_spans" in tokenizers to directly produce word spans without first creating "non-word spans"
### Changed
- setup will now ask if user want to remove sem_data folder. If not, it will check for missing files
- corrected a bug in metadata handling in Document
- changed file format handling in module `annotation_gui`

## [SEM v3.1.1](https://github.com/YoannDupont/SEM/releases/tag/v3.1.1)
### Changed
- corrected a bug in exporters that would crash SEM
- corrected a bug in tagger module that would copy the wrong CSS files for HTML exporters
- corrected a bug where output file would not always have ".txt" extension when exporting to BRAT format
- now all master files use a "guess" format
- changed `tei_np` exporter extension to "analec.tei.xml"
### Removed
- removed `master_parser.py` and `pipeline_factory.py` as loading a master file is ensured by method `load_master` in `tagger.py`.

## [SEM v3.1.0](https://github.com/YoannDupont/SEM/releases/tag/v3.1.0)
### Added
- new module: `map_annotations`. Modifies annotations' types given a mapping
- new exporter: `html_inline`. Inserts HTML span tags in the document
- new exporter: `tei_reden`. Generates a [REDEN](https://github.com/cvbrandoe/REDEN) XML TEI file
- new master file `NER-REDEN.xml`.
- new CSS file `default-no_empty_spans.css`. No default highlight with black background and white font
- changelog file `changelog.md`. Clearer than previous "latest changes". Better history too.
- resource file `REDEN-NER-map`. The mapping between SEM and [REDEN](https://github.com/cvbrandoe/REDEN) annotations for NER
- random one-liner when the user types a module for which SEM ha no suggestions.
### Changed
- `export` module improved. Handle multiple data formats
    - some exporters where changed to handle documents without annotations
- `tei` exporter renamed `tei_analec`
- setup:
    - handle the absence of tkinter by not installing GUI modules
    - only ovewrite SEM data folder if forced (TODO: use setuptools install object to add option)
- tagger module: better handle options and output formats
- segmentation module: handle raw HTML by checking MIME type
- document type: added MIME type metadata
- importers: added logging

## [SEM v3.0.0](https://github.com/YoannDupont/SEM/releases/tag/v3.0.0)
### Added
- SEM can now be installed.
    - run `python setup.py install --user`
    - will compile Wapiti
    - will create a sem_data folder in current user
- another GUI created for annotating documents.
- new module: `annotate`. Allows to call python taggers
    - python implementation of Wapiti labeling
    - lexica-based tagger
### Changed
- improved SEM architecture
- updated manual
- more tests
    - tests for features
    - tests for modules

## changes compared to other versions:
- unreleased: https://github.com/YoannDupont/SEM/compare/v3.3.0...HEAD
- 3.3.0: https://github.com/YoannDupont/SEM/compare/v3.2.0...v3.3.0
- 3.2.0: https://github.com/YoannDupont/SEM/compare/v3.1.2...v3.2.0
- 3.1.2: https://github.com/YoannDupont/SEM/compare/v3.1.1...v3.1.2
- 3.1.1: https://github.com/YoannDupont/SEM/compare/v3.1.0...v3.1.1
- 3.1.0: https://github.com/YoannDupont/SEM/compare/v3.0.0...v3.1.0
