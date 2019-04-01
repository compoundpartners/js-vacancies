# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.utils.translation import (
    ugettext as _, get_language_from_request, override)

from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool

from aldryn_apphooks_config.utils import get_app_instance
from aldryn_translation_tools.utils import (
    get_object_from_request,
    get_admin_url,
)

from .models import Vacancy
from .cms_appconfig import VacanciesConfig

from cms.cms_toolbars import ADMIN_MENU_IDENTIFIER, ADMINISTRATION_BREAK


@toolbar_pool.register
class VacanciesToolbar(CMSToolbar):
    # watch_models must be a list, not a tuple
    # see https://github.com/divio/django-cms/issues/4135
    watch_models = [Vacancy, ]
    supported_apps = ('js_vacancies',)

    def get_on_delete_redirect_url(self, vacancy, language):
        with override(language):
            url = reverse(
                '{0}:vacancy-list'.format(vacancy.app_config.namespace))
        return url

    def __get_vacancies_config(self):
        try:
            __, config = get_app_instance(self.request)
            if not isinstance(config, VacanciesConfig):
                # This is not the app_hook you are looking for.
                return None
        except ImproperlyConfigured:
            # There is no app_hook at all.
            return None

        return config

    def populate(self):
        config = self.__get_vacancies_config()
        if not config:
            # Do nothing if there is no vacancies app_config to work with
            return

        user = getattr(self.request, 'user', None)
        try:
            view_name = self.request.resolver_match.view_name
        except AttributeError:
            view_name = None

        if user and view_name:
            language = get_language_from_request(self.request, check_path=True)


            # get existing admin menu
            admin_menu = self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)

            # add new Vacancies item
            admin_menu.add_sideframe_item(_('Vacancies'), url='/admin/js_vacancies/vacancy/', position=0)

            # If we're on an Vacancy detail page, then get the vacancy
            if view_name == '{0}:vacancy-detail'.format(config.namespace):
                vacancy = get_object_from_request(Vacancy, self.request)
            else:
                vacancy = None

            menu = self.toolbar.get_or_create_menu('vacancies-app',
                                                   config.get_app_title())

            change_config_perm = user.has_perm(
                'js_vacancies.change_vacanciesconfig')
            add_config_perm = user.has_perm(
                'js_vacancies.add_vacanciesconfig')
            config_perms = [change_config_perm, add_config_perm]

            change_vacancy_perm = user.has_perm(
                'js_vacancies.change_vacancy')
            delete_vacancy_perm = user.has_perm(
                'js_vacancies.delete_vacancy')
            add_vacancy_perm = user.has_perm('js_vacancies.add_vacancy')
            vacancy_perms = [change_vacancy_perm, add_vacancy_perm,
                             delete_vacancy_perm, ]

            if change_config_perm:
                url_args = {}
                if language:
                    url_args = {'language': language, }
                url = get_admin_url('js_vacancies_vacanciesconfig_change',
                                    [config.pk, ], **url_args)
                menu.add_modal_item(_('Configure addon'), url=url)

            if any(config_perms) and any(vacancy_perms):
                menu.add_break()

            if change_vacancy_perm:
                url_args = {}
                if config:
                    url_args = {'app_config__id__exact': config.pk}
                url = get_admin_url('js_vacancies_vacancy_changelist',
                                    **url_args)
                menu.add_sideframe_item(_('Vacancy list'), url=url)

            if add_vacancy_perm:
                url_args = {'app_config': config.pk, 'owner': user.pk, }
                if language:
                    url_args.update({'language': language, })
                url = get_admin_url('js_vacancies_vacancy_add', **url_args)
                menu.add_modal_item(_('Add new vacancy'), url=url)

            if change_vacancy_perm and vacancy:
                url_args = {}
                if language:
                    url_args = {'language': language, }
                url = get_admin_url('js_vacancies_vacancy_change',
                                    [vacancy.pk, ], **url_args)
                menu.add_modal_item(_('Edit this vacancy'), url=url,
                                    active=True)

            if delete_vacancy_perm and vacancy:
                redirect_url = self.get_on_delete_redirect_url(
                    vacancy, language=language)
                url = get_admin_url('js_vacancies_vacancy_delete',
                                    [vacancy.pk, ])
                menu.add_modal_item(_('Delete this vacancy'), url=url,
                                    on_close=redirect_url)
