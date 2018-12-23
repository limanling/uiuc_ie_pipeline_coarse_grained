# RPI AIDA Pipeline
One single script to run AIDA pipeline

## Prerequisites
### Packages to install
1. docker
2. docker-nvidia
3. java
4. python=2.7 with requests, jieba, nltk package installed (As most Linux distros deliver by default)

### Download the latest docker images
Docker images will work as services (`mongo`, `panx27/edl` and `elisarpi/elisa-ie`) or runtime environments (`zhangt13/aida_relation`, `zhangt13/aida_event`).
```bash
docker pull mongo
docker pull panx27/edl
docker pull elisarpi/elisa-ie
docker pull zhangt13/aida_relation
docker pull zhangt13/aida_event
```

### Download the latest models
Please download the models for EDL, relation extraction and event extraction.
For entity discovery and linking model:
```bash
cd ./aida_edl
wget https://blender04.cs.rpi.edu/~zhangt13/pipeline/aida_edl_models.tgz
tar -xvf aida_edl_models.tgz
```
For relation extraction model:
```bash
cd ./aida_relation
wget https://blender04.cs.rpi.edu/~zhangt13/pipeline/aida_relation_model.tgz
wget https://blender04.cs.rpi.edu/~zhangt13/pipeline/aida_relation_patch.tgz
tar -xvf aida_relation_model.tgz aida_relation_patch.tgz
```
For event extraction model:
```bash
cd ./aida_event
wget https://blender04.cs.rpi.edu/~zhangt13/pipeline/aida_event_model.tgz
tar -xvf aida_event_model.tgz
```

## Deployment
Please ensure that you are under the root folder of this project, and after each of the following dockers (step 1~3) is started, please open a new terminal to continue with another docker (of course, under the same root folder)

Step 1. Start the EDL mongo database server
```bash
docker run --rm -v ${PWD}/aida_edl/index/db:/data/db --name db mongo
```
Please wait until you see "waiting for connections on port 27017" message appear on the screen.

Step 2. Start the EDL server
```bash
docker run --rm -p 2201:2201 --link db:mongo panx27/edl python ./edl/api/web.py 2201
```

Step 3. Start the name tagger
```bash
docker run --rm -p 3300:3300 --network="host" -v ${PWD}/aida_edl/models/:/usr/src/app/data/name_tagger/pytorch_models -ti elisarpi/elisa-ie /usr/src/app/lorelei_demo/run.py --preload --in_domain
```

Step 4. Prepare Stanford CoreNLP
Download the latest Stanford CoreNLP and the English model file. Unzip the CoreNLP folder and put the model file into the folder. Take a note of the path to the CoreNLP folder.

## Run the codes
* Make sure that you have the LTF files.
* Use the AIDA ltf2rsd tool (LDC2018E62_AIDA_Month_9_Pilot_Eval_Corpus_V1.0/tools/ltf2txt/ltf2rsd.perl) to generate the RSD files. 
* Edit the `.sh` file for your run (including your input LTF/RSD files as well as the CoreNLP folders), then run the shell file. For example.
```bash
sh pipeline_sample.sh
```