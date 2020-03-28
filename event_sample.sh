#!/usr/bin/env bash

# data root path
data_root=data/test
echo ${data_root}

######################################################
# input
######################################################
# rsd source folder path
rsd_source=${data_root}/rsd
# ltf source folder path
ltf_source=${data_root}/ltf
# file list of ltf files (only file names)
ltf_file_list=${data_root}/ltf_lst
ls ${ltf_source} > ${ltf_file_list}
# edl input
edl_output_dir=${data_root}/edl
edl_tab=${edl_output_dir}/merged_corefer.tab
edl_cs=${edl_output_dir}/merged.cs
filler_output_path=${edl_output_dir}/filler_en.cs

######################################################
# output
######################################################
# event output
event_result_dir=${data_root}/event
event_result_file_with_time=${event_result_dir}/events_tme.cs

######################################################
# Event Extraction
######################################################
echo "Extracting events"
ls ${ltf_source} > ${ltf_file_list}
mkdir ${event_result_dir}

python aida_event/gail_event_test.py -l ${ltf_file_list} -f ${ltf_source} -e ${edl_cs} -t ${edl_tab} -i ${filler_output_path} -o ${event_result_file_with_time}
echo "event extraction result in Cold Start Format is in "${event_result_file_with_time}