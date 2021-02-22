# Code examples for simple SEM usage

This folder provides some examples to use SEM with some available resources.

## Download a pipeline

To download a pipeline on you computer, run the following:

`sem download <name_of_resource>`

Where `name_of_resource` is a relative path from the root folder for the
specific kind of resource you wish to download from the
[SEM-resources GitHub repository](https://github.com/YoannDupont/SEM-resources).

For example, if you want to download a pipeline, say the SEM pipeline that uses
the French Treebank (FTB) to provide POS and NER annotations, the name of the
pipeline is `fr/FTB-POS_NER` and its kind is `pipeline`.

The default resource kind is a pipeline, you may download other kinds of
resources, check the help:

`sem download -h`

## Serialize a "master XML file based" pipeline

Serializing allows to centralize everything you need to annotate data instead of
having lots of files sitting around.

Command:

`python ./dump_pipeline.py [input_master_xml_file] [output_file]`

Notice that both are optional. If no input is provided, the program will prompt
you to enter the path to a master XML file.

If `output_file` is not provided, it will just use the stem of the input file
(name without path and without extension).

Example:

`python ./dump_pipeline.py ~/sem_data/resources/master/fr/NER.xml FTB-POS_NER`

If you look into the source code, there is the option to add a license to the
pipeline.

## Load a serialized pipeline

You can see an example of how to load a serialized pipeline in `load_pipeline`.
The command looks like the following:

`python ./load_pipeline.py [pipeline_name] [filename]`

If not given, program will prompt you to enter `pipeline_name`. The pipeline
name is the same as in the __download a pipeline__ section. When loading a
pipeline, SEM will first look from the current directory before looking in the
`sem_data` directory.

You can provide a `filename` if you want to try a pipeline on a specific file,
if not given, it will use a simple sentence instead.
