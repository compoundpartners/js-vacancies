# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.core.urlresolvers import NoReverseMatch
from django.utils.translation import (
    get_language_from_request,
    ugettext_lazy as _,
)

from cms.menu_bases import CMSAttachMenu
from cms.apphook_pool import apphook_pool
from menus.base import NavigationNode
from menus.menu_pool import menu_pool

from .models import Vacancy


class VacanciesMenu(CMSAttachMenu):
    name = _('Vacancies Menu')

    def get_queryset(self, request):
        """Returns base queryset with support for preview-mode."""
        queryset = Vacancy.objects
        if not (request.toolbar and request.toolbar.edit_mode):
            queryset = queryset.published()
        return queryset

    def get_nodes(self, request):
        nodes = []
        language = get_language_from_request(request, check_path=True)
        vacancies = self.get_queryset(request).active_translations(language)

        if hasattr(self, 'instance') and self.instance:
            app = apphook_pool.get_apphook(self.instance.application_urls)
            config = app.get_config(self.instance.application_namespace)
            if config:
                vacancies = vacancies.filter(app_config=config)

        for vacancy in vacancies:
            try:
                url = vacancy.get_absolute_url(language=language)
            except NoReverseMatch:
                url = None

            if url:
                node = NavigationNode(vacancy.safe_translation_getter(
                    'title', language_code=language), url, vacancy.pk)
                nodes.append(node)
        return nodes


menu_pool.register_menu(VacanciesMenu)
