# -*- coding: utf-8 -*-

from django.conf import settings

VACANCIES_SUMMARY_RICHTEXT = getattr(
    settings,
    'VACANCIES_SUMMARY_RICHTEXT',
    False,
)
