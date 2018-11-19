#!/usr/bin/env bash

######################################################
# Arguments 
######################################################
ltf_source=data/ut_texas/texas_data/ # ltf source file path
file_list=data/ut_texas/texas_data_list
edl_output_dir=data/ut_texas/edl # edl output
edl_tab=${edl_output_dir}merged.tab   # linking tab file path
edl_cs=${edl_output_dir}merged.cs # linking cs filt path
relation_result_dir=data/relation/   # final cs output file path
relation_cs_name=en.rel.cs # final cs output for relation
event_dep_dir=data/dep # dependency parser outout
event_tmp_tdf_dir=data/tdf # text data feeder folder for events
event_no_format_dir=data/event_no_format #unformatted event output
event_result_dir=data/event/ #event output folder
final_output_file=data/en_full.cs # final output of everything

######################################################
# eval configurations, use intermediate format as input
# use the stored model to generate predictions, DO NOT
# change them.
######################################################
relation_tmp_output_dir=aida_relation/temp/  # intermediate file path
dp_name=dp.pkl
eval_path=${relation_tmp_output_dir}AIDA_plain_text.txt
eval_result=${relation_tmp_output_dir}AIDA_results.txt
dp_path=${relation_tmp_output_dir}dp.pkl
event_result_file=${event_result_dir}/events.cs
######################################################
# Relation temp output results directory
######################################################

if [[ ! -d "$relation_tmp_output_dir" ]]; then
    mkdir -p $relation_tmp_output_dir
    echo -e "\ncreat new dir: "$relation_tmp_output_dir" for new run.\nPlease make sure the dir is correct!!!"
else
    echo -e "\nThe output directory is existed, \n "$relation_tmp_output_dir"\n Please double check.\n"
fi

if [[ ! -d "$relation_result_dir" ]]; then
    mkdir -p $relation_result_dir
    echo -e "\ncreat new dir: "$relation_result_dir" for new run.\nPlease make sure the dir is correct!!!"
else
    echo -e "\nThe output directory is existed, \n "$relation_result_dir"\n Please double check.\n"
fi

######################################################
# pipeline
######################################################
# EDL
python aida_edl/edl.py ${ltf_source} ${edl_output_dir}

# Relation
# docker run --runtime=nvidia -it --rm -u `stat -c "%u:%g" ./` -v $PWD:/tmp -w /tmp rpi/relation \
# python aida_relation/utils/aida2inter.py --ltf_data_path ${ltf_source} --edl_result_path ${edl_tab} \
# --output_dir ${relation_tmp_output_dir}

# docker run --runtime=nvidia -it --rm -u `stat -c "%u:%g" ./` -v $PWD:/tmp -w /tmp rpi/relation \
# python aida_relation/utils/feature_extraction_test.py --converted_fpath ${relation_tmp_output_dir}AIDA_plain_text.txt \
# --output_dir ${relation_tmp_output_dir} --dp_name ${dp_name}

# docker run --runtime=nvidia -it --rm -u `stat -c "%u:%g" ./` -v $PWD:/tmp -w /tmp rpi/relation \
# python aida_relation/utils/eval_ere.py --eval_text_path ${eval_path} --dp_path ${dp_path} --eval_results_file ${eval_result}

# docker run --runtime=nvidia -it --rm -u `stat -c "%u:%g" ./` -v $PWD:/tmp -w /tmp rpi/relation \
# python aida_relation/utils/use_patterns.py --eval_path ${relation_tmp_output_dir}

# docker run --runtime=nvidia -it --rm -u `stat -c "%u:%g" ./` -v $PWD:/tmp -w /tmp rpi/relation \
# python aida_relation/utils/post_sponsor_test.py --eval_path ${relation_tmp_output_dir}

# docker run --runtime=nvidia -it --rm -u `stat -c "%u:%g" ./` -v $PWD:/tmp -w /tmp rpi/relation \
# python aida_relation/utils/generate_CS_ere_sh.py --edl_cs ${edl_cs} --aida_plain_text ${relation_tmp_output_dir}AIDA_plain_text.txt \
# --aida_results ${relation_tmp_output_dir}results_post_sponsor.txt --rel_cs ${relation_result_dir}${relation_cs_name}

# Event
# docker run --runtime=nvidia -it --rm -v $PWD:/tmp -w /tmp -u `stat -c "%u:%g" ./` rpi/event python aida_event/pipeline_aida_input.py -t ${event_dep_dir} -f ${ltf_source} -l ${file_list} -o ${event_tmp_tdf_dir}

# docker run --runtime=nvidia -it --rm -v $PWD:/tmp -w /tmp -u `stat -c "%u:%g" ./` rpi/event python aida_event/pipeline_aida_end2end.py -l ${file_list} -f ${ltf_source} -t ${event_tmp_tdf_dir} -e ${edl_output_dir} -o ${event_no_format_dir}

# docker run --runtime=nvidia -it --rm -v $PWD:/tmp -w /tmp -u `stat -c "%u:%g" ./` rpi/event python aida_event/pipeline_aida_end2end_full.py -l ${file_list} -e ${edl_output_dir} -t ${event_tmp_tdf_dir} -f ${event_no_format_dir} -o ${event_result_dir}

# Final Merge
# docker run --runtime=nvidia -it --rm -v $PWD:/tmp -w /tmp -u `stat -c "%u:%g" ./` rpi/event python aida_event/pipeline_merge.py -e ${edl_cs} -r ${relation_result_dir}${relation_cs_name} -v ${event_result_file} -o ${final_output_file}
