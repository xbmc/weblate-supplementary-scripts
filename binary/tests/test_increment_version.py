# -*- coding: utf-8 -*-
"""
    Copyright (C) 2021 TeamKodi

    This file is part of sync_addon_metadata_translations

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.

"""

import json
import os
import pytest

from .. import increment_version as target

FIXTURES_PATH = os.path.join(os.getcwd(), 'tests', 'fixtures')
CHANGELOG_STRING_TEMPLATE = '{version}\nTranslations updates from Weblate\n\t- {languages}\n\n'

@pytest.fixture(scope='class')
def staging(request):
    with open(os.path.join(FIXTURES_PATH, 'files.json'), 'r') as file_handle:
        request.cls.files_json = json.load(file_handle)

    with open(os.path.join(FIXTURES_PATH, 'pvr.binary.example',
                           'pvr.binary.example', 'addon.xml.in'), 'r') as open_file:
        request.cls.addon_xml = open_file.read()

    with open(os.path.join(FIXTURES_PATH, 'pvr.binary.example',
                           'pvr.binary.example', 'changelog.txt'), 'r') as open_file:
        request.cls.changelog = open_file.read()


@pytest.mark.usefixtures('staging')
class TestIncrementVersion:

    def test_increment_version(self):
        initial_version = '1.0.0'
        expected_version = '1.0.1'
        micro_version = target.increment_version(initial_version)
        assert micro_version == expected_version, \
            'Version mismatch: Expected: {expected}, Actual: {actual}' \
                .format(expected=expected_version, actual=micro_version)

    def test_is_po_modified(self):
        result = target.is_po_modified(self.files_json)
        assert result is True, 'Expected: True, Actual: {actual}'.format(actual=result)

    def test_modified_languages(self):
        expected = 'en_au, en_gb, en_nz, en_us'
        result = target.modified_languages(self.files_json)
        assert result == expected, 'Expected: {expected}, Actual: {actual}' \
            .format(expected=expected, actual=result)

    def test_walk(self):
        base_path = os.path.join(FIXTURES_PATH, 'pvr.binary.example', 'pvr.binary.example')
        language_path = os.path.join(base_path, 'resources', 'language')

        expected_files_xml = [
            os.path.join(base_path, 'addon.xml.in')
        ]
        expected_files_po = [
            os.path.join(language_path, 'resource.language.en_au', 'strings.po'),
            os.path.join(language_path, 'resource.language.en_gb', 'strings.po'),
            os.path.join(language_path, 'resource.language.en_nz', 'strings.po'),
            os.path.join(language_path, 'resource.language.en_us', 'strings.po'),
        ]

        result_files_xml = list(target.walk(FIXTURES_PATH, '*.xml.in'))
        result_files_po = list(target.walk(FIXTURES_PATH, '*.po'))

        assert expected_files_xml == result_files_xml, 'Expected: {expected}, Actual: {actual}' \
            .format(expected=expected_files_xml, actual=result_files_xml)
        assert expected_files_po == result_files_po, 'Expected: {expected}, Actual: {actual}' \
            .format(expected=expected_files_po, actual=result_files_po)

    def test_find_addon_xml(self):
        expected_path = os.path.join('pvr.binary.example', 'pvr.binary.example', 'addon.xml.in')
        addon_xml_path = target.find_addon_xml()
        assert addon_xml_path.endswith(expected_path) is True, \
            'Expected actual to end with: {expected}, Actual: {actual}' \
                .format(expected=expected_path, actual=addon_xml_path)

    def test_find_changelog(self):
        expected_path = os.path.join('pvr.binary.example', 'pvr.binary.example', 'changelog.txt')
        addon_xml_path = target.find_changelog()
        assert addon_xml_path.endswith(expected_path) is True, \
            'Expected actual to end with: {expected}, Actual: {actual}' \
                .format(expected=expected_path, actual=addon_xml_path)

    def test_create_changelog_string(self):
        version = '1.0.0'
        languages = 'en_au, en_gb, en_nz, en_us'
        version_string = 'v' + version

        expected = CHANGELOG_STRING_TEMPLATE.format(
            version=version_string,
            languages=languages
        )

        actual = target.create_changelog_string(version, languages, add_date=False)
        assert expected == actual, 'Expected: {expected}, Actual: {actual}' \
            .format(expected=expected, actual=actual)

        version_string += ' ({today})'.format(today=target.TODAY)

        expected = CHANGELOG_STRING_TEMPLATE.format(
            version=version_string,
            languages=languages
        )

        actual = target.create_changelog_string(version, languages, add_date=True)
        assert expected == actual, 'Expected: {expected}, Actual: {actual}' \
            .format(expected=expected, actual=actual)

    def test_read_addon_xml(self):
        expected = self.addon_xml
        actual = target.read_addon_xml(target.find_addon_xml())
        assert expected == actual, 'Expected: {expected}, Actual: {actual}' \
            .format(expected=expected, actual=actual)

    def test_current_version(self):
        expected = '7.19.1'
        actual = target.current_version(self.addon_xml)
        assert expected == actual, 'Expected: {expected}, Actual: {actual}' \
            .format(expected=expected, actual=actual)

    def test_update_xml_version(self):
        version_template = 'version="{version}"'
        old_version = '7.19.1'
        new_version = '7.19.2'
        expected = self.addon_xml.replace(version_template.format(version=old_version),
                                          version_template.format(version=new_version))
        actual = target.update_xml_version(self.addon_xml, old_version, new_version)
        assert expected == actual, 'Expected: {expected}, Actual: {actual}' \
            .format(expected=expected, actual=actual)

    def test_update_changelog(self):
        changelog = os.path.join(FIXTURES_PATH, 'pvr.binary.example',
                                 'pvr.binary.example', 'changelog.txt')
        version = '7.19.2'
        languages = 'en_au, en_gb, en_nz, en_us'
        version_string = 'v' + version

        expected = CHANGELOG_STRING_TEMPLATE.format(
            version=version_string,
            languages=languages
        )
        expected += self.changelog
        actual = target.update_changelog(changelog, version, self.files_json, add_date=False)

        assert expected == actual, 'Expected: {expected}, Actual: {actual}' \
            .format(expected=expected, actual=actual)

        version_string += ' ({today})'.format(today=target.TODAY)

        expected = CHANGELOG_STRING_TEMPLATE.format(
            version=version_string,
            languages=languages
        )
        expected += self.changelog
        actual = target.update_changelog(changelog, version, self.files_json, add_date=True)

        assert expected == actual, 'Expected: {expected}, Actual: {actual}' \
            .format(expected=expected, actual=actual)

    def test_update_news(self):
        changelog = os.path.join(FIXTURES_PATH, 'pvr.binary.example',
                                 'pvr.binary.example', 'changelog.txt')
        version = '7.19.2'
        languages = 'en_au, en_gb, en_nz, en_us'
        version_string = 'v' + version

        changelog_string = CHANGELOG_STRING_TEMPLATE.format(
            version=version_string,
            languages=languages
        )

        expected = self.addon_xml.replace('<news>', '<news>\n{lines}'.format(
            lines=changelog_string
        ))
        expected = expected.replace('\n\n\n', '\n\n')
        actual = target.update_news(self.addon_xml, version, self.files_json, add_date=False)

        assert expected == actual, 'Expected: {expected}, Actual: {actual}' \
            .format(expected=expected, actual=actual)

        version_string += ' ({today})'.format(today=target.TODAY)

        changelog_string = CHANGELOG_STRING_TEMPLATE.format(
            version=version_string,
            languages=languages
        )

        expected = self.addon_xml.replace('<news>', '<news>\n{lines}'.format(
            lines=changelog_string
        ))
        expected = expected.replace('\n\n\n', '\n\n')
        actual = target.update_news(self.addon_xml, version, self.files_json, add_date=True)

        assert expected == actual, 'Expected: {expected}, Actual: {actual}' \
            .format(expected=expected, actual=actual)
