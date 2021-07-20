# -*- coding: utf-8 -*-
"""
Increment the version of all language add-ons that have changed files (strings.po/langinfo.xml)

usage: increment_version.py {all,<path to files.json>}

positional arguments:
  {all,<path to files.json>}    Increment "all" languages or all languages in the files.json

"""

import json
import os
import re
import sys

GET_VERSION = re.compile(r'''<addon.+?version="(?P<version>[0-9.]+)"''', re.DOTALL)


def increment_version(version):
    """
    Increment the provided version number (micro)
    :param version: version number to increment in format '1.0.0'
    :type version: str
    :return: incremented version number
    :rtype: str
    """
    version = version.split('.')
    version[2] = str(int(version[2]) + 1)
    return '.'.join(version)


def get_language_folders(chg_files):
    """
    Get the language folders from the list of changed files
    :param chg_files: changed files with path
    :type chg_files: list
    :return: languages folders that contained changed files ie. resource.language.en_gb
    :rtype: list
    """
    payload = []
    for chg_file in chg_files:
        if chg_file.startswith('resource.language') and \
                chg_file.endswith(('strings.po', 'langinfo.xml')):
            folder = os.path.split(chg_file)[0]
            payload.append(folder.split('/')[0])

    print('Files were modified in the following languages:')
    for language in payload:
        print('\t{language}'.format(language=language))

    return payload


def update_addon_xmls(lang_folders):
    """
    Update all addon.xml's in language folders
    :param lang_folders: language folders that contained changed files
    :type lang_folders: list
    """
    addon_xmls = ['/'.join(['.', folder, 'addon.xml']) for folder in lang_folders]

    for addon_xml in addon_xmls:
        print('Reading {filename}'.format(filename=addon_xml))
        with open(addon_xml, 'r') as open_file:
            xml_content = open_file.read()

        version_match = GET_VERSION.search(xml_content)
        if not version_match:
            print('Unable to determine current version... skipping.', '')
            continue

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
            continue

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
    if arg.lower() == 'all':
        changed_files = [item + '/resources/strings.po' for item in os.listdir('.')
                         if os.path.isdir(item) and item.startswith('resource.language')]

    elif arg.endswith('.json'):
        with open(arg, 'r') as open_file:
            changed_files = json.load(open_file)

    else:
        print('No valid argument provided, expected "all" or "path to changed files json".')
        exit(0)

    language_folders = get_language_folders(changed_files)
    if not language_folders:
        print('No modified languages found.')
        exit(0)

    print('')

    update_addon_xmls(language_folders)

    print('')


if __name__ == '__main__':
    main()
