# -*- coding: utf-8 -*-
import argparse
import fnmatch
import json
import os
import re

from datetime import date

TODAY = date.today().isoformat()
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


def modified_languages(chg_files):
    payload = []
    for chg_file in chg_files:
        if 'resource.language.' in chg_file and chg_file.endswith('strings.po'):
            folder = os.path.split(chg_file)[0]
            payload.append(folder.split('/')[-1].replace('resource.language.', ''))

    return ', '.join(payload)


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


def find_changelog():
    for filename in walk('.', 'changelog.txt'):
        print('Found changelog.txt:', filename)
        return filename


def create_changelog_string(version, languages, add_date=False):
    version_string = 'v{version}'.format(version=version)
    if add_date:
        version_string += ' ({today})'.format(today=TODAY)

    return '{version}\nTranslations updates from Weblate\n\t- {languages}\n\n'.format(
        version=version_string,
        languages=languages
    )


def update_changelog(version, chg_files, add_date=False):
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
    print('Reading {filename}'.format(filename=addon_xml))

    with open(addon_xml, 'r') as open_file:
        return open_file.read()


def current_version(xml_content):
    version_match = GET_VERSION.search(xml_content)
    if not version_match:
        print('Unable to determine current version... skipping.', '')
        return

    return version_match.group('version')


def update_addon_xml(addon_xml, xml_content, old_version, new_version):
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
        exit(0)

    modified = is_po_modified(changed_files)
    if not modified:
        print('No modified languages found.')
        exit(0)

    print('')

    addon_xml = find_addon_xml()
    xml_content = read_addon_xml(addon_xml)
    old_version = current_version(xml_content)
    new_version = increment_version(old_version)

    update_addon_xml(addon_xml, xml_content, old_version, new_version)

    if args.update_changelog:
        update_changelog(new_version, changed_files, args.add_date)

    if args.update_news:
        update_news(addon_xml, new_version, changed_files, args.add_date)

    print('')


if __name__ == '__main__':
    main()
