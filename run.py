#!/usr/bin/env python
"""
Generate data JSON from APK CSV source.
"""

import copy
import csv
import os
try:
    import ujson as json
except ImportError:
    import json

import glob
import yaml
from argparse import ArgumentParser

from libs.supercell_resource_decoder.lib_csv import decode_file

parser = ArgumentParser(description='Parse CSV files from Brawl Stars')
parser.add_argument('-l', '--language', dest='language')
parser.add_argument('-f', '--files', nargs='*', dest='files')

args = parser.parse_args()


def cleanup(value):
    if isinstance(value, str):
        # Typing
        if value.startswith('TID_'):
            i['raw' + j[0].upper() + j[1:]] = value.replace('TID_', '')

        elif '.' in value:
            try:
                value = float(value)
            except ValueError:
                pass
        else:
            try:
                value = int(value)
            except ValueError:
                pass

        if isinstance(value, str):
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False

    if value == '':
        value = None

    # Clean
    elif isinstance(value, str):
        value = value.strip()

    return value


if __name__ == '__main__':
    TID = {}
    for filename in glob.iglob('csv/csv_client/**/*.csv', recursive=True):
        print('D', filename)
        decode_file(filename)

    for filename in glob.iglob('csv/csv_logic/**/*.csv', recursive=True):
        print('D', filename)
        decode_file(filename)

    with open('csv/decoded/csv_client/texts.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        title = reader.fieldnames
        lang = 'texts'
        if lang == 'texts':
            lang = 'en'

        TID[lang] = {}
        for n, row in enumerate(reader):
            if n == 0:
                continue
            TID[lang][row['TID']] = row[lang.upper()]

    all_data = {i: {} for i in TID}

    try:
        with open('config.yml', encoding='utf-8') as f:
            config = yaml.load(f)
    except FileNotFoundError:
        config = {'id': []}

    csv_files = [('csv/decoded/csv_client/' + i, i) for i in os.listdir('csv/csv_client') if i.endswith('.csv')] + \
                [('csv/decoded/csv_logic/' + i, i) for i in os.listdir('csv/csv_logic') if i.endswith('.csv')]

    for fp, fn in csv_files:
        with open(fp, encoding='utf-8') as f:
            reader = csv.DictReader(f)

            title = reader.fieldnames

            data = []
            for n, row in enumerate(reader):
                if n == 0:
                    continue
                data.append({title[i][:1].lower() + title[i][1:]: row[title[i]] for i in range(len(title))})

            sc_id_index = 0
            for n, i in enumerate(data):
                i_keys = list(i.keys())
                if not i.get('name', True):
                    for j in i_keys:
                        i[j] = cleanup(i[j])
                        if i[j]:
                            offset = 0
                            for k in range(1, n):
                                if data[n - k].get('name'):
                                    offset = n - k
                                    break
                            if isinstance(data[offset][j], list):
                                data[offset][j].append(i[j])
                            else:
                                data[offset][j] = [data[n - 1][j], i[j]]
                            i[j] = None

                if fn in config.get('id', []):
                    i['id'] = config['id'][fn] + n

                if fn in config['scId']:
                    if not i.get('tID') or TID['en'].get(i['tID']):
                        i['scId'] = config['scId'][fn] + sc_id_index
                        sc_id_index += 1
                    else:
                        i['scId'] = 0

                for j in i_keys:
                    i[j] = cleanup(i[j])

            # languages
            for lang in TID:
                if args.language:
                    lang = args.language
                change_data = []
                for i in data:
                    if i.get('name', True):
                        change_data.append(copy.deepcopy(i))
                    else:
                        continue

                    i = change_data[-1]
                    i_keys = list(i.keys())
                    for j in i_keys:
                        if isinstance(i[j], str) and i[j].startswith('TID_'):
                            try:
                                i[j] = TID[lang]['TID_' + i[j][4:]]
                            except KeyError:
                                pass

                if (args.files and fn in args.files) or (not args.files):
                    with open(f"json/{lang}/{fn.replace('.csv', '.json')}", 'w+') as f:
                        json.dump(change_data, f, indent=4)

                all_data[lang][fn.replace('.csv', '')] = copy.deepcopy(change_data)
                if args.language:
                    break
        print('R', fp)

    # tid.json
    if (args.files and 'tid.csv' in args.files) or (not args.files):
        for i in TID:
            if args.language:
                i = args.language
            with open(f'json/{i}/tid.json', 'w+') as f:
                print('R', f'json/{i}/tid.json')
                all_data[i]['tid'] = {j[4:]: TID[i][j] for j in TID[i]}
                json.dump(TID[i], f, indent=4)
            if args.language:
                break

    # all.json
    for i in TID:
        if args.language:
            i = args.language
        with open(f'json/{i}/all.json', 'w+') as f:
            print('R', f'json/{i}/all.json')
            json.dump(all_data[i], f, indent=4)
        if args.language:
            break

    # scid.json

    for i in TID:
        if args.language:
            i = args.language
        with open(f'json/{i}/scid.json', 'w+') as f:
            print('R', f'json/{i}/scid.json')
            tid_data = {}
            for key in all_data[i]:
                try:
                    if 'scId' in all_data[i][key][0].keys():
                        tid_data[key] = all_data[i][key]
                except (IndexError, KeyError):
                    continue

            json.dump(tid_data, f, indent=4)
        if args.language:
            break
