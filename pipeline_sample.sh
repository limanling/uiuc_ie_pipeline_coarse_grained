#!/usr/bin/env bash

######################################################
# Arguments
######################################################
# input root path
data_root=data/test

# ltf source folder path
ltf_source=${data_root}/ltf
# rsd source folder path
rsd_source=${data_root}/rsd
# file list of ltf files (only file names)
ltf_file_list=${data_root}/ltf_lst
ls ${ltf_source} > ${ltf_file_list}
# file list of rsd files (absolute paths, this is a temporary file)
rsd_file_list=${data_root}/rsd_lst
readlink -f ${rsd_source}/* > ${rsd_file_list}

# edl output
edl_output_dir=${data_root}/edl
edl_bio=${edl_output_dir}/en.bio
edl_tab_nocorefer=${edl_output_dir}/merged.tab
edl_tab=${edl_output_dir}/merged_corefer.tab
edl_cs=${edl_output_dir}/merged.cs

# filler output
core_nlp_output_path=${data_root}/corenlp
filler_output_path=${edl_output_dir}/filler_en.cs

# relation output
relation_result_dir=${data_root}/relation   # final cs output file path
relation_cs_name=en.rel.cs # final cs output for relation
new_relation_output_path=${relation_result_dir}/new_relation_en.cs

# event output
event_result_dir=${data_root}/event
event_result_file_with_time=${event_result_dir}/events_tme.cs
event_result_file_corefer=${event_result_dir}/events_corefer.cs

# final output
final_output_file=${data_root}/en_full.cs

######################################################
# Relation temporary files
######################################################
relation_tmp_output_dir=${relation_result_dir}/temp  # intermediate file path
dp_name=dp.pkl
eval_path=${relation_tmp_output_dir}/AIDA_plain_text.txt
eval_result=${relation_tmp_output_dir}/AIDA_results.txt
dp_path=${relation_tmp_output_dir}/${dp_name}

######################################################
# Event temporary files
######################################################
event_dep_dir=${data_root}/dep
event_tmp_tdf_dir=${data_root}/tdf
event_no_format_dir=${data_root}/event_no_format
event_raw_result_file=${event_result_dir}/events_raw.cs

######################################################
# pipeline
######################################################
## EDL
echo "Extracting entities and linking them to KB"
mkdir -p ${edl_output_dir}
python aida_utilities/ltf2bio.py ${ltf_source} ${edl_bio}
python aida_edl/edl.py ${ltf_source} ${edl_bio} ${edl_output_dir}

## Relation Extraction
echo "Extracting relations"
### Create folders
if [ -d "$relation_tmp_output_dir" ]
then
    echo "The output directory already exists, "$relation_tmp_output_dir". Please double check. "
else
    mkdir -p $relation_tmp_output_dir
    echo "Created new dir: "$relation_tmp_output_dir" for new run. Please make sure that the dir is correct!!!"
fi

if [ -d "$relation_result_dir" ]
then
    echo "The output directory already exists, "$relation_result_dir". Please double check."
else
    mkdir -p $relation_result_dir
    echo "Created new dir: "$relation_result_dir" for new run. Please make sure that the dir is correct!!!"
fi
### Run relation extractir
python aida_relation/gail_relation_test.py -l ${ltf_file_list} -f ${ltf_source} -e ${edl_cs} -t ${edl_tab} -o ${relation_result_dir}/${relation_cs_name}

### Fillers and new relation
echo "Extracting fillers and new relation types"

python aida_filler/nlp_utils.py --rsd_list ${rsd_file_list} --corenlp_dir ${core_nlp_output_path}

docker run -it --rm -v ${PWD}:/tmp -w /tmp zhangt13/aida_event \
python aida_filler/filler_generate.py --corenlp_dir ${core_nlp_output_path} \
                                      --edl_path ${edl_cs} \
                                      --text_dir ${rsd_source} \
                                      --filler_path ${filler_output_path}  \
                                      --relation_path ${new_relation_output_path} \
                                      --units_path aida_filler/units_clean.txt

## Event Extraction
echo "Extracting events"

### Create folders
#mkdir ${event_result_dir}
if [ -d "$event_result_dir" ]
then
    echo "The output directory already exists, "${event_result_dir}". Please double check."
else
    mkdir -p ${event_result_dir}
    echo "Created new dir: "${event_result_dir}" for new run. Please make sure that the dir is correct!!!"
fi
### Run event extractor
python aida_event/gail_event_test.py -l ${ltf_file_list} -f ${ltf_source} -e ${edl_cs} -t ${edl_tab} -i ${filler_output_path} -o ${event_result_file_with_time}

### Event coreference
python aida_event_coreference/gail_event_coreference_test_en.py -i ${event_result_file_with_time} -o ${event_result_file_corefer}

## Final Merge
echo "Merging all items"
docker run -it --rm -v ${PWD}:/tmp -w /tmp zhangt13/aida_event \
python aida_utilities/pipeline_merge.py -e ${edl_cs} -f ${filler_output_path} -r ${relation_result_dir}/${relation_cs_name} -n ${new_relation_output_path} -v ${event_result_file_corefer} -o ${final_output_file}

## ColdStart Format to AIF Format
echo "Generating AIF format"
### Generating parameter file
echo "inputKBFile: /AIDA-Interchange-Format-master/sample_params/"${final_output_file} > ${data_root}/rpi_params
echo "baseURI: http://www.isi.edu/gaia" >> ${data_root}/rpi_params
echo "systemURI: http://www.rpi.edu" >> ${data_root}/rpi_params
echo "mode: SHATTER" >> ${data_root}/rpi_params
echo "ontology: /AIDA-Interchange-Format-master/src/main/resources/edu/isi/gaia/SeedlingOntology" >> ${data_root}/rpi_params
echo "relationArgsFile: /AIDA-Interchange-Format-master/src/main/resources/edu/isi/gaia/seedling_relation_args.csv" >> ${data_root}/rpi_params
echo "outputAIFDirectory: /AIDA-Interchange-Format-master/sample_params/"${data_root}"/ttl/" >> ${data_root}/rpi_params
### Running converter
docker run -i -t --rm -v ${PWD}:/AIDA-Interchange-Format-master/sample_params -w /AIDA-Interchange-Format-master limanling/aida_converter \
./target/appassembler/bin/coldstart2AidaInterchange ./sample_params/${data_root}/rpi_params

echo "Final result in Cold Start Format is in "${data_root}"/en_full.cs"
echo "Final result in Turtle Format is in "${data_root}"/ttl"
