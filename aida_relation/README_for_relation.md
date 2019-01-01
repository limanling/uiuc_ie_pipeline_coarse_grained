# Explanation
This docker accept input as a json with following contents
* File content of EDL cs file (with 'edl_cs' key)
* File content of EDL tab file (with 'edl_tab' key)
* Contents of ltf xml files (under 'input'-><file_id>->'ltf') (Also, file id comes from LTF list file, so they are `xxxx.ltf.xml`).

The output (response) will be file content of event output with cs format, simply write it with `open().write()`.