This file is for event API only, and will be removed after main README file is finalized.

# Deployment of event docker
* Download the docker
```bash
docker pull zhangt13/aida_event
```
* Deploy the docker, it will take a few minutes, you can proceed after you see "Serving Flask app ..." message.
```bash
docker run -i -t --rm -w /aida_event -p 5234:5234 zhangt13/aida_event python gail_event.py
```
* Use the docker
Check `event_sample.sh`.

# Explanation
This docker accept input as a json with following contents
* File content of EDL cs file (with 'edl_cs' key)
* File content of EDL tab file (with 'edl_tab' key)
* File content of filler cs file (with 'filler_cs' key)
* Contents of ltf xml files (under 'input'-><file_id>->'ltf') (Also, file id comes from LTF file list file, so they are `xxxx.ltf.xml`).

The output (response) will be file content of event output with cs format, simply write it with `open().write()`.