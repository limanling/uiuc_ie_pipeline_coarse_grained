import sys
import os
import requests
import subprocess
PWD=os.path.dirname(os.path.abspath(__file__))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('USAGE: python <ltf input dir> <output dir>')
        exit()
    indir = sys.argv[1]
    outdir = sys.argv[2]
    try:
        os.mkdir(outdir)
    except:
        pass

    # url = 'http://blender02.cs.rpi.edu:3300/elisa_ie/entity_discovery_and_linking/en'
    url = 'http://0.0.0.0:3300/elisa_ie/entity_discovery_and_linking/en'
    for i in os.listdir(indir):
        print('processing %s' % i)
        try:
            data = open('%s/%s' % (indir, i)).read()
            params = {
                'input_format': 'ltf',
                'output_format': 'EvalTab'
            }
            r = requests.post(url, data=data, params=params)
            if r.status_code != 200:
                continue
            with open('%s/%s.tab' % (outdir, i), 'w') as fw:
                fw.write(r.text.encode('utf-8'))

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            msg = 'unexpected error: %s | %s | %s' % \
                (exc_type, exc_obj, exc_tb.tb_lineno)
            print(msg)

    with open('%s/merged.tab' % outdir, 'w') as fw:
        for i in os.listdir(outdir):
            if not i.endswith('.ltf.xml.tab'):
                continue
            tab = open('%s/%s' % (outdir, i), 'r').read()
            if not tab:
                continue
            fw.write(tab)
            # docid = i.replace('.ltf.xml.tab', '')
            # with open('%s/%s' % (outdir, i), 'r') as f:
            #     for line in f:
            #         tmp = line.rstrip('\n').split('\t')
            #         fw.write('%s\n' % '\t'.join(tmp))
    cmd = [
        'rm',
        '%s/*.ltf.xml.tab' % outdir,
    ]
    subprocess.call(' '.join(cmd), shell=True)
    cmd = [
        'python',
        '%s/tab2cs.py' % PWD,
        '%s/merged.tab' % outdir,
        '%s/merged.cs' % outdir,
        'EDL'
    ]
    subprocess.call(' '.join(cmd), shell=True)
