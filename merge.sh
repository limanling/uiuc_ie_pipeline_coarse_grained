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

# event output
event_result_dir=${data_root}/event
event_result_file_with_time=${event_result_dir}/events_tme.cs

# final output
final_output_file=${data_root}/en_full.cs

######################################################
# pipeline
######################################################
## Final Merge
echo "Merging all items"
docker run -it --rm -v ${PWD}:/tmp -w /tmp zhangt13/aida_event \
python aida_utilities/pipeline_merge.py -e ${edl_cs} -f ${filler_output_path} -r ${relation_result_dir}/${relation_cs_name} -n ${new_relation_output_path} -v ${event_result_file_with_time} -o ${final_output_file}
#docker run -it --rm -v ${PWD}:/tmp -w /tmp -u `stat -c "%u:%g" ./` zhangt13/aida_event \
#python aida_event/pipeline_merge.py -e ${edl_cs} -f ${filler_output_path} -r ${relation_result_dir}/${relation_cs_name} -o ${final_output_file}

