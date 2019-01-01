#!/usr/bin/env bash

######################################################
# Arguments
######################################################
# input root path
data_root=$1
work_root=/home/lim22/aida_pipeline
api_root=/home/lim22/public_html/aida_api
#data_root = ${${data_root}#${work_root}}
echo ${data_root}
cd ${work_root}
echo $PWD

# ltf source folder path
ltf_source=${data_root}/ltf
# rsd source folder path
rsd_source=${data_root}/rsd
# file list of ltf files (only file names)
#ltf_file_list=${data_root}/ltf_lst
#ls ${ltf_source} > ${ltf_file_list}
# file list of rsd files (absolute paths, this is a temporary file)
rsd_file_list=${data_root}/rsd_lst
readlink -f ${rsd_source}/* > ${rsd_file_list}

# stanford toolbox
core_nlp_tool_path=/data/m1/lim22/env/stanford-corenlp-full-2018-10-05

# edl output
edl_output_dir=${data_root}/edl
#edl_tab=${edl_output_dir}/merged.tab
edl_cs=${edl_output_dir}/merged.cs

# filler output
core_nlp_output_path=${data_root}/corenlp
filler_output_path=${edl_output_dir}/filler_en.cs

# relation output
relation_result_dir=${data_root}/relation   # final cs output file path
#relation_cs_name=en.rel.cs # final cs output for relation
new_relation_output_path=${relation_result_dir}/new_relation_en.cs

######################################################
# pipeline
######################################################
## Fillers and new relation
echo "Extracting fillers and new relation types"

#java -mx5g -cp "${core_nlp_tool_path}/*" edu.stanford.nlp.pipeline.StanfordCoreNLP $* -annotators tokenize,ssplit,pos,lemma,ner,regexner,depparse,entitymentions -outputFormat json -filelist ${rsd_file_list} -outputDirectory ${core_nlp_output_path}
python aida_filler/nlp_utils.py --rsd_list ${rsd_file_list} --corenlp_dir ${core_nlp_output_path}

docker run -it --rm -v ${PWD}:/tmp -w /tmp zhangt13/aida_event \
python aida_filler/filler_generate.py --corenlp_dir ${core_nlp_output_path} \
                                      --edl_path ${edl_cs} \
                                      --text_dir ${rsd_source} \
                                      --filler_path ${filler_output_path}  \
                                      --relation_path ${new_relation_output_path} \
                                      --units_path aida_filler/units_clean.txt

cd ${api_root}