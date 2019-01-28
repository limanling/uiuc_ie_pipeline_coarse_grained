def fix_nom(all_str):
    newlines = []
    lines = all_str.strip('\n').split('\n')
    for line in lines:
        if '-NOM_' in line:
            line = line.replace('EN-NOM_MENTION_', 'EN_MENTION_1')
            line = line.replace('EN-NOM_WEAVEH_MENTION_', 'EN_MENTION_2')
            line = line.replace('\tNAM\t', '\tNOM\t')
        newlines.append(line)
    return '\n'.join(newlines) + '\n'