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
edl_tab=${edl_output_dir}/merged.tab
edl_cs=${edl_output_dir}/merged.cs

# filler output
core_nlp_output_path=${data_root}/corenlp
filler_output_path=${edl_output_dir}/filler_en.cs

# relation output
relation_result_dir=${data_root}/relation   # final cs output file path
relation_cs_name=en.rel.cs # final cs output for relation
new_relation_output_path=${relation_result_dir}/new_relation_en.cs

######################################################
# Relation temporary files
######################################################
relation_tmp_output_dir=aida_relation/temp  # intermediate file path
dp_name=dp.pkl
eval_path=${relation_tmp_output_dir}/AIDA_plain_text.txt
eval_result=${relation_tmp_output_dir}/AIDA_results.txt
dp_path=${relation_tmp_output_dir}/${dp_name}

######################################################
# pipeline
######################################################

## Relation
echo "Extracting relations"
if [ -d "$relation_tmp_output_dir" ]
then
    echo "\nThe output directory already exists, \n "$relation_tmp_output_dir"\n Please double check.\n"
else
    mkdir -p $relation_tmp_output_dir
    echo "\ncreated new dir: "$relation_tmp_output_dir" for new run.\nPlease make sure that the dir is correct!!!"
fi

if [ -d "$relation_result_dir" ]
then
    echo "\nThe output directory already exists, \n "$relation_result_dir"\n Please double check.\n"
else
    mkdir -p $relation_result_dir
    echo "\ncreated new dir: "$relation_result_dir" for new run.\nPlease make sure that the dir is correct!!!"
fi

docker run -it --rm -u `stat -c "%u:%g" ./` -v $PWD:/tmp -w /tmp zhangt13/aida_relation \
python aida_relation/utils/aida2inter.py --ltf_data_path ${ltf_source} --edl_result_path ${edl_tab} \
--output_dir ${relation_tmp_output_dir}

docker run -it --rm -u `stat -c "%u:%g" ./` -v $PWD:/tmp -w /tmp zhangt13/aida_relation \
python aida_relation/utils/feature_extraction_test.py --converted_fpath ${relation_tmp_output_dir}/AIDA_plain_text.txt \
--output_dir ${relation_tmp_output_dir} --dp_name ${dp_name}

docker run -it --rm -u `stat -c "%u:%g" ./` -v $PWD:/tmp -w /tmp zhangt13/aida_relation \
python aida_relation/utils/eval_ere.py --eval_text_path ${eval_path} --dp_path ${dp_path} --eval_results_file ${eval_result}

docker run -it --rm -u `stat -c "%u:%g" ./` -v $PWD:/tmp -w /tmp zhangt13/aida_relation \
python aida_relation/utils/use_patterns.py --eval_path ${relation_tmp_output_dir}

docker run -it --rm -u `stat -c "%u:%g" ./` -v $PWD:/tmp -w /tmp zhangt13/aida_relation \
python aida_relation/utils/post_sponsor_test.py --eval_path ${relation_tmp_output_dir}

docker run -it --rm -u `stat -c "%u:%g" ./` -v $PWD:/tmp -w /tmp zhangt13/aida_relation \
python aida_relation/utils/generate_CS_ere_sh.py --edl_cs ${edl_cs} --aida_plain_text ${relation_tmp_output_dir}/AIDA_plain_text.txt \
--aida_results ${relation_tmp_output_dir}/results_post_sponsor.txt --rel_cs ${relation_result_dir}/${relation_cs_name}

# Fillers and new relation
echo "Extracting fillers and new relation types"

java -mx5g -cp "${core_nlp_tool_path}/*" edu.stanford.nlp.pipeline.StanfordCoreNLP $* -annotators tokenize,ssplit,pos,lemma,ner,regexner,depparse,entitymentions -outputFormat json -filelist ${rsd_file_list} -outputDirectory ${core_nlp_output_path}

docker run -it --rm -v ${PWD}:/tmp -w /tmp -u `stat -c "%u:%g" ./` zhangt13/aida_event \
python aida_filler/filler_generate.py --corenlp_dir ${core_nlp_output_path} \
                                      --edl_path ${edl_cs} \
                                      --text_dir ${rsd_source} \
                                      --filler_path ${filler_output_path}  \
                                      --relation_path ${new_relation_output_path} \
                                      --units_path aida_filler/units_clean.txt

cd ${api_root}