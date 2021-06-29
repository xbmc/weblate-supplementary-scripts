# -*- coding: utf-8 -*-
import fnmatch
import json
import os
import re
import sys

GET_VERSION = re.compile(r'''<addon.+?version="(?P<version>[0-9.]+)"''', re.DOTALL)


def increment_version(version):
    version = version.split('.')
    version[2] = str(int(version[2]) + 1)
    return '.'.join(version)


def is_po_modified(chg_files):
    payload = []
    for chg_file in chg_files:
        if 'resource.language.' in chg_file and chg_file.endswith('strings.po'):
            folder = os.path.split(chg_file)[0]
            payload.append(folder.split('/')[-1])

    if payload:
        print('Files were modified in the following languages:')
        for language in payload:
            print('\t{language}'.format(language=language))

    return payload != []


def walk(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                fname = os.path.join(root, basename)
                yield fname


def find_addon_xml():
    for filename in walk('.', 'addon.xml.in'):
        print('Found addon.xml.in:', filename)
        return filename


def update_addon_xml():
    addon_xml = find_addon_xml()

    print('Reading {filename}'.format(filename=addon_xml))
    with open(addon_xml, 'r') as open_file:
        xml_content = open_file.read()

    version_match = GET_VERSION.search(xml_content)
    if not version_match:
        print('Unable to determine current version... skipping.', '')
        return

    old_version = version_match.group('version')
    new_version = increment_version(old_version)
    print('\tOld Version: {version}'.format(version=old_version))
    print('\tNew Version: {version}'.format(version=new_version))

    new_xml_content = xml_content.replace(
        'version="{version}"'.format(version=old_version),
        'version="{version}"'.format(version=new_version),
    )

    if xml_content == new_xml_content:
        print('XML was unmodified... skipping.', '')
        return

    print('Writing {filename}'.format(filename=addon_xml))
    with open(addon_xml, 'w') as open_file:
        open_file.write(new_xml_content)

    print('')


def main():
    argv = sys.argv
    if len(argv) == 1:
        print('No argument provided.')
        exit(0)

    arg = argv[1]

    if arg.endswith('.json'):
        with open(arg, 'r') as open_file:
            changed_files = json.load(open_file)

    else:
        print('No valid argument provided, expected "path to changed files json".')
        exit(0)

    modified = is_po_modified(changed_files)
    if not modified:
        print('No modified languages found.')
        exit(0)

    print('')

    update_addon_xml()

    print('')


if __name__ == '__main__':
    main()
