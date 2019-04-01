# -*- coding: utf-8 -*-

from __future__ import unicode_literals

try:
    from collections import Counter
except ImportError:
    from backport_collections import Counter

import datetime
from operator import attrgetter

from django.db import models
from django.utils.timezone import now

from aldryn_apphooks_config.managers.base import ManagerMixin, QuerySetMixin
from parler.managers import TranslatableManager, TranslatableQuerySet


class VacancyQuerySet(QuerySetMixin, TranslatableQuerySet):
    def published(self):
        """
        Returns Vacancies that are published AND have a publishing_date that
        has actually passed.
        """
        return self.filter(is_published=True, publishing_date__lte=now())


class RelatedManager(ManagerMixin, TranslatableManager):
    def get_queryset(self):
        qs = VacancyQuerySet(self.model, using=self.db)
        return qs.select_related('featured_image')

    def published(self):
        return self.get_queryset().published()

    def get_months(self, request, namespace):
        """
        Get months and years with Vacancies count for given request and namespace
        string. This means how many Vacancies there are in each month.

        The request is required, because logged-in content managers may get
        different counts.

        Return list of dictionaries ordered by Vacancy publishing date of the
        following format:
        [
            {
                'date': date(YEAR, MONTH, ARBITRARY_DAY),
                'num_vacancies': NUM_VACANCIES
            },
            ...
        ]
        """

        # TODO: check if this limitation still exists in Django 1.6+
        # This is done in a naive way as Django is having tough time while
        # aggregating on date fields
        if (request and hasattr(request, 'toolbar') and
                request.toolbar and request.toolbar.edit_mode):
            vacancies = self.namespace(namespace)
        else:
            vacancies = self.published().namespace(namespace)
        dates = vacancies.values_list('publishing_date', flat=True)
        dates = [(x.year, x.month) for x in dates]
        date_counter = Counter(dates)
        dates = set(dates)
        dates = sorted(dates, reverse=True)
        months = [
            # Use day=3 to make sure timezone won't affect this hacks'
            # month value. There are UTC+14 and UTC-12 timezones!
            {'date': datetime.date(year=year, month=month, day=3),
             'num_vacancies': date_counter[(year, month)]}
            for year, month in dates]
        return months
