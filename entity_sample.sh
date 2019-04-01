#!/usr/bin/env bash

######################################################
# Arguments
######################################################
# input root path, the parent directory of rsd files
data_root=$1

# rsd source folder path
rsd_source=${data_root}/rsd
# ltf source folder path
ltf_source=${data_root}/ltf
mkdir ${ltf_source}
# convert rsd to ltf
python aida_utilities/rsd2ltf.py ${rsd_source} ${ltf_source} --seg_option nltk

# edl output
edl_output_dir=${data_root}/edl
edl_bio=${edl_output_dir}/en.bio
edl_tab=${edl_output_dir}/merged.tab
edl_cs=${edl_output_dir}/merged.cs

# final output
final_output_file=${data_root}/en_full.cs

######################################################
# pipeline
######################################################
## EDL
echo "Extracting entities and linking them to KB"
mkdir -p ${edl_output_dir}
python aida_edl/edl.py ${ltf_source} ${edl_bio} ${edl_output_dir}

# Final Merge
echo "Merging all items"
python aida_utilities/pipeline_merge.py -e ${edl_cs} -o ${final_output_file}

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

echo "Final result in Cold Start Format is in "${final_output_file}
echo "Final result in Turtle Format is in "${data_root}"/ttl"
