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
#rsd_source=${data_root}/rsd
# file list of ltf files (only file names)
ltf_file_list=${data_root}/ltf_lst
ls ${ltf_source} > ${ltf_file_list}
# file list of rsd files (absolute paths, this is a temporary file)
#rsd_file_list=${data_root}/rsd_lst
#readlink -f ${rsd_source}/* > ${rsd_file_list}

# stanford toolbox
#core_nlp_tool_path=/data/m1/lim22/env/stanford-corenlp-full-2018-10-05

# edl output
edl_output_dir=${data_root}/edl
#edl_tab=${edl_output_dir}/merged.tab
#edl_cs=${edl_output_dir}/merged.cs

# filler output
#core_nlp_output_path=${data_root}/corenlp
filler_output_path=${edl_output_dir}/filler_en.cs

# relation output
#relation_result_dir=${data_root}/relation   # final cs output file path
#relation_cs_name=en.rel.cs # final cs output for relation
#new_relation_output_path=${relation_result_dir}/new_relation_en.cs

# event output
event_result_dir=${data_root}/event
event_result_file_with_time=${event_result_dir}/events_tme.cs

# final output
#final_output_file=${data_root}/en_full.cs

######################################################
# Relation temporary files
######################################################
#relation_tmp_output_dir=aida_relation/temp  # intermediate file path
#dp_name=dp.pkl
#eval_path=${relation_tmp_output_dir}/AIDA_plain_text.txt
#eval_result=${relation_tmp_output_dir}/AIDA_results.txt
#dp_path=${relation_tmp_output_dir}/${dp_name}

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

## Event
echo "Extracting events"
docker run -it --rm -v ${PWD}:/tmp -w /tmp -u `stat -c "%u:%g" ./` zhangt13/aida_event \
python aida_event/pipeline_aida_input.py -t ${event_dep_dir} -f ${ltf_source} -l ${ltf_file_list} -o ${event_tmp_tdf_dir}

docker run -it --rm -v ${PWD}:/tmp -w /tmp -u `stat -c "%u:%g" ./` zhangt13/aida_event \
python aida_event/pipeline_aida_end2end.py -l ${ltf_file_list} -f ${ltf_source} -t ${event_tmp_tdf_dir} -e ${edl_output_dir} -o ${event_no_format_dir}

docker run -it --rm -v ${PWD}:/tmp -w /tmp -u `stat -c "%u:%g" ./` zhangt13/aida_event \
python aida_event/pipeline_aida_end2end_full.py -l ${ltf_file_list} -e ${edl_output_dir} -t ${event_tmp_tdf_dir} -f ${event_no_format_dir} -o ${event_result_dir}

docker run -it --rm -v ${PWD}:/tmp -w /tmp -u `stat -c "%u:%g" ./` zhangt13/aida_event \
python aida_event/pipeline_aida_time_argument.py -l ${ltf_source} -f ${filler_output_path} -i ${event_raw_result_file} -o ${event_result_file_with_time}

cd ${api_root}