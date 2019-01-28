# RPI AIDA Pipeline
One single script to run AIDA pipeline. A demo is in [RPI AIDA Pipeline](https://blender04.cs.rpi.edu/~lim22/aida_api/extraction.html).

## Prerequisites
### Packages to install
1. Docker
2. Java
3. Python=2.7 with requests, jieba, nltk package installed (As most Linux distros deliver by default)

Please do not set up RPI AIDA Pipeline in a NAS, as the EDL needs MongoDB, which may lead to permission issues in a NAS.

### Download the latest docker images
Docker images will work as services (`mongo`, `panx27/edl`, `elisarpi/elisa-ie`， `limanling/aida_relation`, `zhangt13/aida_event`,  `dylandilu/event_coreference`, and `wangqy96/aida_nominal_coreference_en`) or runtime environments (`limanling/aida_converter`).
```bash
docker pull mongo
docker pull panx27/edl
docker pull elisarpi/elisa-ie
docker pull limanling/aida_relation
docker pull zhangt13/aida_event
docker pull dylandilu/event_coreference
docker pull limanling/aida_converter
docker pull wangqy96/aida_nominal_coreference_en
```

### Download the latest models
Please download the models for EDL, relation extraction and event extraction.
For entity discovery and linking model:
```bash
cd ./aida_edl
wget https://blender04.cs.rpi.edu/~zhangt13/pipeline/aida_edl_models.tgz
tar -xvf aida_edl_models.tgz
cd ./models
wget https://blender04.cs.rpi.edu/~zhangb8/lorelei/pytorch_models/en-nom.tar.gz
wget https://blender04.cs.rpi.edu/~zhangb8/lorelei/pytorch_models/en-nom_weaveh.tar.gz
tar -zxvf en-nom.tar.gz
tar -zxvf en-nom_weaveh.tar.gz
```

## Deployment
Please ensure that you are under the root folder of this project, and after each of the following dockers (step 1~5) is started, please open a new terminal to continue with another docker (of course, under the same root folder).

Also please reserve the the following ports and ensure that no other programs/services are occupying these ports: `27017`, `2201`, `3300`, `5000`, `5234`, `9000`, `6000`, `6100` and `6200`.

Step 1. Start the EDL mongo database server

Please wait until you see "waiting for connections on port 27017" message appear on the screen.

```bash
docker run --rm -v ${PWD}/aida_edl/index/db:/data/db --name db mongo
```

Step 2. Start the EDL server
```bash
docker run --rm -p 2201:2201 --link db:mongo panx27/edl python ./edl/api/web.py 2201
```

Step 3. Start the nominal coreference server
```bash
docker run -i -t --rm -w /aida_nominal_coreference_en -p 2468:2468 wangqy96/aida_nominal_coreference_en python nominal_backend.py
```

Step 4. Start the name tagger
```bash
docker run --rm -p 3300:3300 --network="host" -v ${PWD}/aida_edl/models/:/usr/src/app/data/name_tagger/pytorch_models -ti elisarpi/elisa-ie /usr/src/app/lorelei_demo/run.py --preload --in_domain
```

Step 5. Start the relation extractor

This step will take a few minutes, you can proceed after you see "Serving Flask app "relation_backend"" message.
```bash
docker run -i -t --rm -w /aida_relation -p 5000:5000 limanling/aida_relation python relation_backend.py
```

Step 6. Start the event extractor

This step will take a few minutes, you can proceed after you see "Serving Flask app ..." message.
```bash
docker run -i -t --rm -w /aida_event -p 5234:5234 zhangt13/aida_event python gail_event.py
```

Step 7. Start the event coreference solution

This step will take a few minutes, you can proceed after you see "Serving Flask app "aida_event_coreference_backen_{eng, rus, ukr}"" message. Notice that the port 6000, 6100 and 6200 are for English, Russian and Ukrainian respectively.
```bash
docker run -i -t --rm -w /event_coreference -p 6000:6000 dylandilu/event_coreference python aida_event_coreference_backen_eng.py
docker run -i -t --rm -w /event_coreference -p 6100:6100 dylandilu/event_coreference python aida_event_coreference_backen_rus.py
docker run -i -t --rm -w /event_coreference -p 6200:6200 dylandilu/event_coreference python aida_event_coreference_backen_ukr.py
```

Step 8. Prepare Stanford CoreNLP

Download the latest Stanford CoreNLP and the English model file. Unzip the CoreNLP folder and put the model file into the folder. Please start the CoreNLP Server under the CoreNLP folder.

```bash
nohup java -mx5g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 9000 -timeout 150000 -annotators tokenize,ssplit,pos,lemma,ner,regexner,depparse,entitymentions -outputFormat json > corenlp.log 2>&1 &
```

Please test the CoreNLP Server is running successfully:
```bash
wget --post-data 'The quick brown fox jumped over the lazy dog.' 'localhost:9000/?properties={"annotators":"tokenize,ssplit,pos,lemma,ner,regexner,depparse,entitymentions","outputFormat":"json"}'
```
<!-- Run Stanford CoreNLP using Docker.
```bash
docker pull graham3333/corenlp-complete
docker run -itd -p 9000:9000 --name corenlp graham3333/corenlp-complete
wget --post-data 'The quick brown fox jumped over the lazy dog.' 'localhost:9000/?properties={"annotators":"tokenize,ssplit,pos,lemma,ner,regexner,depparse,entitymentions","outputFormat":"json"}'
```-->

## Run the codes
* Make sure you have RSD and LTF files. 
	* If you have RSD files, please use the aida_utilities/rsd2ltf.py to generate the LTF files. 
	* If you have LTF files, please use the AIDA ltf2rsd tool (LDC2018E62_AIDA_Month_9_Pilot_Eval_Corpus_V1.0/tools/ltf2txt/ltf2rsd.perl) to generate the RSD files. 
* Edit the `pipeline_sample.sh` for your run, including `data_root` containing a subfolder `ltf` with your input LTF files and a subfolder `rsd` with your input RSD files. Then run the shell file. For example.
```bash
sh pipeline_sample.sh
```
