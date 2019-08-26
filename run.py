#!/usr/bin/env python
"""
Generate data JSON from APK CSV source.
"""

import copy
import csv
import os
import sys
try:
    import ujson as json
except ImportError:
    import json

import glob
import requests
import yaml
from argparse import ArgumentParser

from libs.supercell_resource_decoder.lib_csv import decode_file

parser = ArgumentParser(description='Parse CSV files from Brawl Stars')
parser.add_argument('-l', '--language', dest='language')
parser.add_argument('-f', '--files', nargs='*', dest='files')

args = parser.parse_args()

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
                if fn in config['id']:
                    i['id'] = config['id'][fn] + n
                if fn in config['scId']:
                    if i.get('name', True):
                        i['scId'] = config['scId'][fn] + sc_id_index
                        sc_id_index += 1
                i_keys = list(i.keys())
                for j in i_keys:
                    if isinstance(i[j], str):
                        # Typing
                        if i[j].startswith('TID_'):
                            i['raw' + j[0].upper() + j[1:]] = i[j].replace('TID_', '')

                        elif '.' in i[j]:
                            try:
                                i[j] = float(i[j])
                            except ValueError:
                                pass
                        else:
                            try:
                                i[j] = int(i[j])
                            except ValueError:
                                pass

                        if isinstance(i[j], str):
                            if i[j].lower() == 'true':
                                i[j] = True
                            elif i[j].lower() == 'false':
                                i[j] = False

                    if i[j] == '':
                        i[j] = None

                    # Clean
                    elif isinstance(i[j], str):
                        i[j] = i[j].strip()

            # languages
            for lang in TID:
                if args.language:
                    lang = args.language
                change_data = copy.deepcopy(data)  # might be able to remove
                for n, i in enumerate(change_data):
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
