# RPI AIDA Pipeline
One single script to run AIDA pipeline

## Prerequisites
### Packages to install
docker
docker-nvidia
### Download the latest docker (for packages or servers)
```bash
docker pull mongo
docker pull panx27/edl
docker pull elisarpi/elisa-ie
docker pull zhangt13/aida_relation
docker pull zhangt13/aida_event
```
## Deployment
Please ensure that you are under the root folder of this project, and after each of the following dockers (step 1~3) is started, please open a new terminal to continue with another docker (of course, under the same root folder)

Step 1. Start the EDL mongo database server
```bash
docker run --rm -v ${PWD}/aida_edl/index/db:/data/db --name db mongo
```

Step 2. Start the EDL server
```bash
docker run --rm -p 2201:2201 --link db:mongo panx27/edl python ./edl/api/web.py 2201
```

Step 3. Start the name tagger
```bash
docker run -p 3300:3300 --network="host" -v ${PWD}/aida_edl/models/:/usr/src/app/data/name_tagger/pytorch_models -ti elisarpi/elisa-ie /usr/src/app/lorelei_demo/run.py --preload --in_domain
```
### Run the codes
