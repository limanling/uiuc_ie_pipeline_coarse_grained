import requests
import os
import json
import argparse
import io

def get_nominal_corefer(dev, dev_e, out_e):
    print('Loading tagged docs from %s...' % dev)
    dev = io.open(dev, 'r').read().split("\n")
    while len(dev[-1]) == 0:
        dev = dev[:-1]
    print('Loading edl mentions from %s...' % dev_e)
    dev_e = io.open(dev_e, 'r').read().split("\n")
    while len(dev_e[-1]) == 0:
        dev_e = dev_e[:-1]
    result = {'dev': dev, 'dev_e': dev_e}
    json_string = json.dumps(result)
    r = requests.post('http://127.0.0.1:2468/aida_nominal_coreference_en', json=json_string)
    if r.status_code == 200:
        print("Succeed coreference")
        f = io.open(out_e, 'w')
        f.write(r.text)
        f.close()
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
    args = parser.parse_args()
    get_nominal_corefer(args.dev, args.dev_e, args.out_e)
