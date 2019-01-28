import requests
import os
import json
import argparse

def get_nominal_corefer(json_string):
    r = requests.post('http://127.0.0.1:2468/aida_nominal_coreference_en', json=json_string)
    if r.status_code == 200:
        print("Succeed coreference")
    else:
        print(r.status_code)

if __name__ == '__main__':
    # Read parameters from command line
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dev", default="data/en.bio",
        help="Input bio location"
    )
    parser.add_argument(
        "--dev_e", default="data/en.linking.tab",
        help="Input edl location"
    )
    parser.add_argument(
        "--out_e", default="en.linking.tab",
        help="Output edl location"
    )
    args = vars(parser.parse_args())
    json_string = json.dumps(args)
    get_nominal_corefer(json_string)