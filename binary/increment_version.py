# -*- coding: utf-8 -*-
"""
Update the changelog, news (optionally) and increment the version of a binary add-on when language files are changed

usage: increment_version.py [-h] [-c] [-d] [-n] json

positional arguments:
  json                  Path to files.json

optional arguments:
  -h, --help            show this help message and exit
  -c, --update-changelog
                        Update changelog with translation changes
  -d, --add-date        Add date to version number in changelog and news. ie.
                        "v1.0.1 (2021-7-17)"
  -n, --update-news     Update addon.xml.in news with translation changes

"""

import argparse
import fnmatch
import json
import os
import re

from datetime import date

TODAY = date.today().isoformat()
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


def is_po_modified(chg_files):
    """
    Check if any po files were modified
    :param chg_files: changed files
    :type chg_files: list
    :return: whether a po file was in the list of changed files
    :rtype: bool
    """
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


def modified_languages(chg_files):
    """
    Get the languages that were modified from the list of changed files
    :param chg_files: changed files with path
    :type chg_files: list
    :return: comma delimited string of languages that were modified ie. en_gb, en_us
    :rtype: str
    """
    payload = []
    for chg_file in chg_files:
        if 'resource.language.' in chg_file and chg_file.endswith('strings.po'):
            folder = os.path.split(chg_file)[0]
            payload.append(folder.split('/')[-1].replace('resource.language.', ''))

    return ', '.join(payload)


def walk(directory, pattern):
    """
    Generator to walk the provided directory and yield files matching the pattern
    :param directory: directory to recursively walk
    :type directory: str
    :param pattern: glob pattern, https://docs.python.org/3/library/fnmatch.html
    :type pattern: str
    :return: filenames (with path) matching pattern
    :rtype: str
    """
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                fname = os.path.join(root, basename)
                yield fname


def find_addon_xml():
    """
    Find the addon.xml.in path
    :return: path with filename to addon.xml.in
    :rtype: str
    """
    for filename in walk('.', 'addon.xml.in'):
        print('Found addon.xml.in:', filename)
        return filename


def find_changelog():
    """
    Find the changelog.txt path
    :return: path with filename to changelog.txt
    :rtype: str
    """
    for filename in walk('.', 'changelog.txt'):
        print('Found changelog.txt:', filename)
        return filename


def create_changelog_string(version, languages, add_date=False):
    """
    Create the string that will be added to the changelog
    :param version: version number being created
    :type version: str
    :param languages: comma delimited string of languages that were modified ie. en_gb, en_us
    :type languages: str
    :param add_date: add date to the version number. ie. v1.0.0 (2021-7-19)
    :type add_date: bool
    :return: formatted string for the changelog
    :rtype: str
    """
    version_string = 'v{version}'.format(version=version)
    if add_date:
        version_string += ' ({today})'.format(today=TODAY)

    return '{version}\nTranslations updates from Weblate\n\t- {languages}\n\n'.format(
        version=version_string,
        languages=languages
    )


def update_changelog(version, chg_files, add_date=False):
    """
    Update the changelog.txt with a formatted version of the provided information
    :param version: version number being created
    :type version: str
    :param chg_files: changed files with path
    :type chg_files: list
    :param add_date: add date to the version number. ie. v1.0.0 (2021-7-19)
    :type add_date: bool
    """
    changelog = find_changelog()
    if not changelog:
        return

    updated_languages = modified_languages(chg_files)

    changelog_string = create_changelog_string(version, updated_languages, add_date)

    print('Writing changelog.txt:\n\'\'\'\n{lines}\'\'\''.format(lines=changelog_string))
    with open(changelog, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(changelog_string + content)


def update_news(addon_xml, version, chg_files, add_date=False):
    """
    Update the news element of the addon.xml.in with a formatted version of the provided information
    :param addon_xml: path with filename to the addon.xml.in
    :type addon_xml: str
    :param version: version number being created
    :type version: str
    :param chg_files: changed files with path
    :type chg_files: list
    :param add_date: add date to the version number. ie. v1.0.0 (2021-7-19)
    :type add_date: bool
    """
    xml_content = read_addon_xml(addon_xml)

    updated_languages = modified_languages(chg_files)

    changelog_string = create_changelog_string(version, updated_languages, add_date)

    print('Writing news to addon.xml.in:\n\'\'\'\n{lines}\'\'\''.format(lines=changelog_string))

    new_xml_content = xml_content.replace('<news>', '<news>\n{lines}'.format(
        lines=changelog_string
    ))

    new_xml_content = new_xml_content.replace('\n\n\n', '\n\n')

    with open(addon_xml, 'w') as open_file:
        open_file.write(new_xml_content)

    print('')


def read_addon_xml(addon_xml):
    """
    Read the addon.xml.in
    :param addon_xml: path with filename to the addon.xml.in
    :type addon_xml: str
    :return: contents of the addon.xml.in
    :rtype: str
    """
    print('Reading {filename}'.format(filename=addon_xml))

    with open(addon_xml, 'r') as open_file:
        return open_file.read()


def current_version(xml_content):
    """
    Get the current version from the addon.xml.in
    :param xml_content: contents of the addon.xml.in
    :type xml_content: str
    :return: the current version
    :rtype: str
    """
    version_match = GET_VERSION.search(xml_content)
    if not version_match:
        print('Unable to determine current version... skipping.', '')
        return ''

    return version_match.group('version')


def update_addon_xml(addon_xml, xml_content, old_version, new_version):
    """
    Update the version in the addon.xml.in contents
    :param addon_xml: path with filename to the addon.xml.in
    :type addon_xml: str
    :param xml_content: contents of the addon.xml.in
    :type xml_content: str
    :param old_version: the old/current version number
    :type old_version: str
    :param new_version: the new version number
    :type new_version: str
    """
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
    parser = argparse.ArgumentParser()
    parser.add_argument('json', type=str, help='Path to files.json')

    parser.add_argument('-c', '--update-changelog', action='store_true',
                        help='Update changelog with translation changes')

    parser.add_argument('-d', '--add-date', action='store_true',
                        help='Add date to version number in changelog and news. ie. "v1.0.1 (2021-7-17)"')

    parser.add_argument('-n', '--update-news', action='store_true',
                        help='Update addon.xml.in news with translation changes')

    args = parser.parse_args()

    if args.json.endswith('.json'):
        with open(args.json, 'r') as open_file:
            changed_files = json.load(open_file)

    else:
        print('No valid argument provided, expected a path to changed files json.')
        exit(1)

    modified = is_po_modified(changed_files)
    if not modified:
        print('No modified languages found.')
        exit(0)

    print('')

    addon_xml = find_addon_xml()
    xml_content = read_addon_xml(addon_xml)

    old_version = current_version(xml_content)
    if not old_version:
        print('Unable to determine the current version. exiting...')
        exit(1)

    new_version = increment_version(old_version)

    update_addon_xml(addon_xml, xml_content, old_version, new_version)

    if args.update_changelog:
        update_changelog(new_version, changed_files, args.add_date)

    if args.update_news:
        update_news(addon_xml, new_version, changed_files, args.add_date)

    print('')


if __name__ == '__main__':
    main()
