#!/usr/bin/env bash

######################################################
# Arguments
######################################################
lang="en"
# input root path
data_root=data/testdata/${lang}_small
#data_root=$1
parent_child_tab_path=$2
raw_id_column=$3
rename_id_column=$4
use_nominal_corefer=1

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
edl_bio=${edl_output_dir}/${lang}.bio
edl_tab_nam=${edl_output_dir}/${lang}.nam.tagged.tab
edl_tab_nom=${edl_output_dir}/${lang}.nom.tagged.tab
edl_tab_pro=${edl_output_dir}/${lang}.pro.tagged.tab
edl_tab_link=${edl_output_dir}/${lang}.linking.tab
edl_tab_link_fb=${edl_output_dir}/${lang}.linking.freebase.tab
edl_tab_final=${edl_output_dir}/merged_final.tab
edl_cs_coarse=${edl_output_dir}/merged.cs
fine_grain_model=${edl_output_dir}/merged_fine.tsv
edl_cs_fine=${edl_output_dir}/merged_fine.cs

# filler output
core_nlp_output_path=${data_root}/corenlp
filler_coarse=${edl_output_dir}/filler_en.cs
filler_fine=${edl_output_dir}/filler_fine.cs

# relation output
relation_result_dir=${data_root}/relation   # final cs output file path
relation_cs_coarse=en.rel.cs # final cs output for relation
relation_cs_fine=en.rel.cs # final cs output for relation
new_relation_output_path=${relation_result_dir}/new_relation_en.cs

#docker run -v `pwd`:`pwd` -w `pwd` -i -t limanling/uiuc_ie_m18 \
#    /opt/conda/envs/aida_relation_coarse/bin/python \
#    ./aida_pipeline_m18/test/test_env.py
#
#docker run -v `pwd`:`pwd` -w `pwd` -i -t limanling/uiuc_ie_m18 \
#    /opt/conda/envs/py27/bin/python \
#    ./aida_pipeline_m18/test/test_readdata.py ${datapath}

#docker run -v `pwd`:`pwd` -w `pwd` -i -t --network="host" limanling/uiuc_ie_m18 \
#    /opt/conda/envs/aida_entity/bin/python \
#    ./aida_pipeline_m18/test/test_entity.py \
#    ${lang} ${data_root}


## EDL
echo "** Extracting entities **"
docker run --user "$(id -u):$(id -g)" --rm -v `pwd`:`pwd` -w `pwd` -i -t --network="host" limanling/uiuc_ie_m18 \
    /opt/conda/envs/py36/bin/python \
    ./aida_pipeline_m18/aida_edl/edl.py \
    ${ltf_source} ${rsd_source} ${lang} ${edl_output_dir} \
    ${edl_bio} ${edl_tab_nam} ${edl_tab_nom} ${edl_tab_pro} \
    ${fine_grain_model}
## linking
echo "** Linking entities to KB **"
link_dir=edl_data/test
mkdir -p ${PWD}/${link_dir}/input
cp -r ${edl_output_dir}/* ${PWD}/${link_dir}/input/
docker run --user "$(id -u):$(id -g)" --rm -v ${PWD}/edl_data:/data  --link db:mongo panx27/edl \
    python ./projs/docker_aida19/aida19.py \
    ${lang} /data/test/input /data/test/output
docker run --user "$(id -u):$(id -g)" --rm -v `pwd`:`pwd` -w `pwd` -i -t limanling/uiuc_ie_m18 \
    cp ${link_dir}/output/* ${edl_output_dir}/
docker run --user "$(id -u):$(id -g)" --rm -v `pwd`:`pwd` -w `pwd` -i -t limanling/uiuc_ie_m18 \
    rm -rf ${link_dir}
## nominal coreference
echo "** Starting nominal coreference **"
docker run --user "$(id -u):$(id -g)" --rm -v `pwd`:`pwd` -w `pwd` -i -t --network="host" limanling/uiuc_ie_m18 \
    /opt/conda/envs/py36/bin/python \
    ./aida_pipeline_m18/aida_edl/nominal_corefer_en.py \
    --dev ${edl_bio} \
    --dev_e ${edl_tab_link} \
    --dev_f ${edl_tab_link_fb} \
    --out_e ${edl_tab_final} \
    --use_nominal_corefer ${use_nominal_corefer}
## tab2cs
docker run --user "$(id -u):$(id -g)" --rm -v `pwd`:`pwd` -w `pwd`  -i -t limanling/uiuc_ie_m18 \
    /opt/conda/envs/py36/bin/python \
    ./aida_pipeline_m18/aida_edl/tab2cs.py \
    ${edl_tab_final} ${edl_cs_coarse} 'EDL'

echo "** Extraction relations **"
## Relation Extraction (coarse)
docker run --user "$(id -u):$(id -g)" --rm -v `pwd`:`pwd` -w `pwd` -i -t limanling/uiuc_ie_m18 \
    /opt/conda/envs/aida_relation_coarse/bin/python \
    -u /relation/CoarseRelationExtraction/exec_relation_extraction.py \
    -i ${lang} \
    -l ${ltf_file_list} \
    -f ${ltf_source} \
    -e ${edl_cs_coarse} \
    -t ${edl_tab_final} \
    -o ${relation_cs_coarse}

### Relation Extraction (fine)
#docker run -v `pwd`:`pwd` -w `pwd` -i -t limanling/uiuc_ie_m18 \
#    /opt/conda/envs/py36/bin/python \
#    -u /relation/FineRelationExtraction/EVALfine_grained_relations.py \
#    --lang_id ${lang} \
#    --ltf_dir ${ltf_source} \
#    --rsd_dir ${rsd_source} \
#    --cs_fnames ${edl_cs_coarse} ${filler_coarse} ${relation_cs_coarse} \
#    --fine_ent_type_tab "path/to/finegrained_entity_file.tab" \
#    --fine_ent_type_json "path/to/finegrained_entity_file.json" \
#    --outdir ${relation_result_dir} \
#    --fine_grained
###   --reuse_cache \
###    --use_gpu \
#
## Filler Extraction & new relation
#docker run -v `pwd`:`pwd` -w `pwd` -i -t limanling/uiuc_ie_m18 \
#    /opt/conda/envs/py36/bin/python \
#    ./aida_pipeline_m18/aida_filler/nlp_utils.py \
#    --rsd_list ${rsd_file_list} --corenlp_dir ${core_nlp_output_path}
#
## Fine-grained Entity
#docker run --user "$(id -u):$(id -g)" --rm -v `pwd`:`pwd` -w `pwd` -i -t limanling/uiuc_ie_m18 \
#    /opt/conda/envs/aida_entity/bin/python \
#    ./aida_pipeline_m18/aida_edl/fine_grained_entity.py \
#    ${lang} ${fine_grain_model} ${edl_cs_coarse} ${edl_cs_fine} ${filler_fine} \
#    --filler_coarse ${filler_coarse} --hard_parent_constraint
#
## Event (Coarse)
#echo "** Extracting events **"
#docker run --user "$(id -u):$(id -g)" --rm -v `pwd`:`pwd` -w `pwd` -i -t limanling/uiuc_ie_m18 \
#    /opt/conda/envs/aida_entity/bin/python \
#    ./aida_pipeline_m18/aida_event/gail_event_test.py \
#    -l ${ltf_file_list} \
#    -f ${ltf_source} \
#    -e ${edl_cs} \
#    -t ${edl_tab} \
#    -i ${filler_coarse} \
#    -o ${event_result_file_with_time}
#
## Event (Fine-grained)
#echo "** Event fine-grained typing **"
#docker run --user "$(id -u):$(id -g)" --rm -v `pwd`:`pwd` -w `pwd` -i -t limanling/uiuc_ie_m18 \
#    /opt/conda/envs/aida_entity/bin/python \
#    ./aida_pipeline_m18/aida_event/fine_grained/fine_grained_events.py \
#    ${lang}${source} ${ltf_dir} ${entity_finegrain} ${entity_freebase_tab} \
#    ${entity_coarse_cs} ${event_coarse} ${event_fine} ${visual_path_fine} \
#    --filler_coarse ${filler_coarse} \
#    --entity_finegrain_aida ${output_edl_all}
#
#
## Event coreference
#python aida_event_coreference/gail_event_coreference_test_en.py -i ${event_result_file_with_time} -o ${event_result_file_corefer} -r ${rsd_source} -x
#
### Final Merge
#echo "Merging all items"
#docker run -it --rm -v ${PWD}:/tmp -w /tmp charlesztt/aida_event \
#python aida_utilities/pipeline_merge.py -e ${entity_fine} -f ${filler_fine} -r ${relation_result_dir}/${relation_cs_name} -n ${new_relation_output_path} -v ${event_result_file_corefer} -o ${final_output_file}
#
#echo "Final result in Cold Start Format is in "${data_root}"/en_full.cs"

