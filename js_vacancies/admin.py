# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from aldryn_apphooks_config.admin import BaseAppHookConfig, ModelAppHookConfig
from aldryn_people.models import Person
from aldryn_translation_tools.admin import AllTranslationsMixin
from cms.admin.placeholderadmin import FrontendEditableAdminMixin
from cms.admin.placeholderadmin import PlaceholderAdminMixin
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.forms import widgets
from parler.admin import TranslatableAdmin
from parler.forms import TranslatableModelForm
from sortedm2m_filter_horizontal_widget.forms import SortedFilteredSelectMultiple

from . import models

from .constants import (
    VACANCIES_SUMMARY_RICHTEXT,
)

def make_published(modeladmin, request, queryset):
    queryset.update(is_published=True)


make_published.short_description = _(
    "Mark selected vacancies as published")


def make_unpublished(modeladmin, request, queryset):
    queryset.update(is_published=False)


make_unpublished.short_description = _(
    "Mark selected vacancies as not published")


def make_featured(modeladmin, request, queryset):
    queryset.update(is_featured=True)


make_featured.short_description = _(
    "Mark selected vacancies as featured")


def make_not_featured(modeladmin, request, queryset):
    queryset.update(is_featured=False)


make_not_featured.short_description = _(
    "Mark selected vacancies as not featured")


class VacancyAdminForm(TranslatableModelForm):

    class Meta:
        model = models.Vacancy
        fields = [
            'app_config',
            'categories',
            'closing_date',
            'external_link',
            'featured_image',
            'is_featured',
            'is_published',
            'lead_in',
            'location',
            'meta_description',
            'meta_keywords',
            'meta_title',
            'slug',
            'services',
            'title',
            'vacancy_type',
        ]

    def __init__(self, *args, **kwargs):
        super(VacancyAdminForm, self).__init__(*args, **kwargs)

        qs = models.Vacancy.objects
        if self.instance.app_config_id:
            qs = models.Vacancy.objects.filter(
                app_config=self.instance.app_config)
        elif 'initial' in kwargs and 'app_config' in kwargs['initial']:
            qs = models.Vacancy.objects.filter(
                app_config=kwargs['initial']['app_config'])

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        # Don't allow app_configs to be added here. The correct way to add an
        # apphook-config is to create an apphook on a cms Page.
        self.fields['app_config'].widget.can_add_related = False
        if not VACANCIES_SUMMARY_RICHTEXT:
            self.fields['lead_in'].widget = widgets.Textarea()


class VacancyAdmin(
    AllTranslationsMixin,
    PlaceholderAdminMixin,
    FrontendEditableAdminMixin,
    ModelAppHookConfig,
    TranslatableAdmin
):
    form = VacancyAdminForm
    list_display = ('title', 'app_config', 'location', 'is_featured',
                    'is_published')
    list_filter = [
        'app_config',
        'location',
        'categories',
        'services',
        'companies',
    ]
    actions = (
        make_featured, make_not_featured,
        make_published, make_unpublished,
    )


    advanced_settings_fields = (
        'categories',
        'services',
        'companies',
        'app_config',
    )

    fieldsets = (
        (None, {
            'fields': (
                'title',
                'location',
                'vacancy_type',
                'closing_date',
                'external_link',
                'publishing_date',
                'is_published',
                'is_featured',
                'featured_image',
                'lead_in',
            )
        }),
        (_('Meta Options'), {
            'classes': ('collapse',),
            'fields': (
                'slug',
                'meta_title',
                'meta_description',
                'meta_keywords',
            )
        }),
        (_('Advanced Settings'), {
            'classes': ('collapse',),
            'fields': advanced_settings_fields,
        }),
    )



    filter_horizontal = [
        'categories',
    ]
    app_config_values = {
        'default_published': 'is_published'
    }
    app_config_selection_title = ''
    app_config_selection_desc = ''

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'services':
            kwargs['widget'] = SortedFilteredSelectMultiple(attrs={'verbose_name': 'service', 'verbose_name_plural': 'services'})
        if db_field.name == 'companies':
            kwargs['widget'] = SortedFilteredSelectMultiple(attrs={'verbose_name': 'company', 'verbose_name_plural': 'companies'})
        return super(VacancyAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)


admin.site.register(models.Vacancy, VacancyAdmin)


class VacanciesConfigAdmin(
    AllTranslationsMixin,
    PlaceholderAdminMixin,
    BaseAppHookConfig,
    TranslatableAdmin
):
    def get_config_fields(self):
        return (
            'app_title', 'permalink_type', 'non_permalink_handling',
            'template_prefix', 'paginate_by', 'pagination_pages_start',
            'pagination_pages_visible', 'exclude_featured',
            'search_indexed', 'config.default_published',)


admin.site.register(models.VacanciesConfig, VacanciesConfigAdmin)
