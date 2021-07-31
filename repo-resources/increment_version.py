# -*- coding: utf-8 -*-
"""
Increment the version of all add-ons that have changed language files (strings.po/langinfo.xml)

usage: increment_version.py [-h] [-bv] [-c] [-d] [-n] json

positional arguments:
  json                  Path to files.json

optional arguments:
  -h, --help            show this help message and exit
  -bv, --bold-version   Add bold tags to version in changelog ie. "[B]v1.0.1 (2021-7-17)[/B]"
  -c, --update-changelog
                        Update changelog with translation changes
  -d, --add-date        Add date to version number in changelog and news. ie. "v1.0.1 (2021-7-17)"
  -n, --update-news     Update addon.xml news with translation changes

"""

import argparse
import json
import os
import re

from datetime import date

GET_VERSION = re.compile(r'''<addon.+?version="(?P<version>[0-9.]+)"''', re.DOTALL)
TODAY = date.today().isoformat()


def files_json(string):
    """
    Check if string is a files.json files, raise FileExistsError if not
    Used by argparse to validate json argument
    :param string: string to check if it's a files.json file
    :type string: str
    :return: provided string
    :rtype: str
    """

    if os.path.isfile(string) and string.endswith('.json'):
        return string

    raise FileExistsError(string)


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


def get_addon_folders(chg_files):
    """
    Get the addon folders from the list of changed files
    :param chg_files: changed files with path
    :type chg_files: list
    :return: addon folders that contained changed files ie. resource.language.en_gb or metadata.universal
    :rtype: list
    """
    payload = []
    for chg_file in chg_files:
        if 'resource.language.' in chg_file and \
                chg_file.endswith(('strings.po', 'langinfo.xml')):
            folder = os.path.split(chg_file)[0]
            payload.append(folder.split('/')[0])

    payload = list(set(payload))

    print('Files were modified in the following add-ons:')
    for addon in payload:
        print('\t{addon}'.format(addon=addon))

    return payload


def create_changelog_string(version, add_date=False, bold_version=False):
    """
    Create the string that will be added to the changelog
    :param version: version number being created
    :type version: str
    :param add_date: add date to the version number. ie. v1.0.0 (2021-7-19)
    :type add_date: bool
    :param bold_version: wrap version in bold tags. ie. [B]v1.0.0 (2021-7-19)[/B]
    :type bold_version: bool
    :return: formatted string for the changelog
    :rtype: str
    """
    version_string = 'v{version}'.format(version=version)
    if add_date:
        version_string += ' ({today})'.format(today=TODAY)
    if bold_version:
        version_string = '[B]{string}[/B]'.format(string=version_string)

    return '{version}\n- Translations updates from Weblate\n\n'.format(
        version=version_string
    )


def update_changelogs(addon_folders, add_date=False, bold_version=False):
    """
    Update changelog with changes
    :param addon_folders: addon folders that contained changed files
    :type addon_folders: list
    :param add_date: add date to the version number. ie. v1.0.0 (2021-7-19)
    :type add_date: bool
    :param bold_version: wrap version in bold tags. ie. [B]v1.0.0 (2021-7-19)[/B]
    :type bold_version: bool
    """

    addon_folders = [os.path.join('.', folder) for folder in addon_folders]

    for folder in addon_folders:
        addon_xml = os.path.join(folder, 'addon.xml')
        changelog = os.path.join(folder, 'changelog.txt')

        print('Reading {filename}'.format(filename=addon_xml))
        with open(addon_xml, 'r') as open_file:
            xml_content = open_file.read()

        version_match = GET_VERSION.search(xml_content)
        if not version_match:
            print('Unable to determine current version... skipping.', '')
            continue

        version = version_match.group('version')

        changelog_string = create_changelog_string(version, add_date, bold_version)

        print('Writing changelog.txt:\n\'\'\'\n{lines}\'\'\''.format(lines=changelog_string))
        with open(changelog, 'r+') as f:
            content = f.read()
            f.seek(0, 0)
            f.write(changelog_string + content)

        print('')


def update_news(addon_folders, add_date=False, bold_version=False):
    """
    Update the news element of the addon.xml with a formatted version of the provided information
    :param addon_folders: addon folders that contained changed files
    :type addon_folders: list
    :param add_date: add date to the version number. ie. v1.0.0 (2021-7-19)
    :type add_date: bool
    :param bold_version: wrap version in bold tags. ie. [B]v1.0.0 (2021-7-19)[/B]
    :type bold_version: bool
    """
    addon_xmls = [os.path.join('.', folder, 'addon.xml') for folder in addon_folders]

    for addon_xml in addon_xmls:
        print('Reading {filename}'.format(filename=addon_xml))
        with open(addon_xml, 'r') as open_file:
            xml_content = open_file.read()

        version_match = GET_VERSION.search(xml_content)
        if not version_match:
            print('Unable to determine current version... skipping.', '')
            continue

        version = version_match.group('version')

        changelog_string = create_changelog_string(version, add_date, bold_version)

        print('Writing news to addon.xml:\n\'\'\'\n{lines}\'\'\''.format(lines=changelog_string))

        new_xml_content = xml_content.replace('<news>', '<news>\n{lines}'.format(
            lines=changelog_string
        ))

        new_xml_content = new_xml_content.replace('\n\n\n', '\n\n')

        if xml_content == new_xml_content:
            print('XML was unmodified... skipping.', '')
            continue

        print('Writing {filename}'.format(filename=addon_xml))
        with open(addon_xml, 'w') as open_file:
            open_file.write(new_xml_content)

        print('')


def update_addon_versions(addon_folders):
    """
    Update the version all addon.xml's in addon folders
    :param addon_folders: addon folders that contained changed files
    :type addon_folders: list
    """
    addon_xmls = [os.path.join('.', folder, 'addon.xml') for folder in addon_folders]

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
    parser = argparse.ArgumentParser()
    parser.add_argument('json', type=files_json, help='Path to files.json')

    parser.add_argument('-bv', '--bold-version', action='store_true',
                        help='Add bold tags to version in changelog ie. "[B]v1.0.1 (2021-7-17)[/B]"')

    parser.add_argument('-c', '--update-changelog', action='store_true',
                        help='Update changelog with translation changes')

    parser.add_argument('-d', '--add-date', action='store_true',
                        help='Add date to version number in changelog and news. ie. "v1.0.1 (2021-7-17)"')

    parser.add_argument('-n', '--update-news', action='store_true',
                        help='Update addon.xml news with translation changes')

    args = parser.parse_args()

    with open(args.json, 'r') as open_file:
        changed_files = json.load(open_file)

    addon_folders = get_addon_folders(changed_files)
    if not addon_folders:
        print('No modified add-ons found.')
        exit(0)

    print('')

    update_addon_versions(addon_folders)

    if args.update_changelog:
        update_changelogs(addon_folders, args.add_date, args.bold_version)

    if args.update_news:
        update_news(addon_folders, args.add_date, args.bold_version)

    print('')


if __name__ == '__main__':
    main()
