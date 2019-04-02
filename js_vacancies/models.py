# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from aldryn_apphooks_config.fields import AppHookConfigField
from aldryn_categories.models import Category
from aldryn_categories.fields import CategoryManyToManyField
from aldryn_translation_tools.models import TranslatedAutoSlugifyMixin, TranslationHelperMixin
from cms.models.fields import PlaceholderField
from cms.models.pluginmodel import CMSPlugin
from cms.utils.i18n import get_current_language, get_redirect_on_fallback
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db import connection, models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import override, ugettext
from djangocms_text_ckeditor.fields import HTMLField
from sortedm2m.fields import SortedManyToManyField
from filer.fields.image import FilerImageField
from parler.models import TranslatableModel, TranslatedFields
from aldryn_newsblog.utils import get_plugin_index_data, get_request, strip_tags
from js_locations.models import Location

from .cms_appconfig import VacanciesConfig
from .managers import RelatedManager

try:
    from django.utils.encoding import force_unicode
except ImportError:
    from django.utils.encoding import force_text as force_unicode


@python_2_unicode_compatible
class Vacancy(TranslatedAutoSlugifyMixin,
              TranslationHelperMixin,
              TranslatableModel):

    # TranslatedAutoSlugifyMixin options
    slug_source_field_name = 'title'
    slug_default = _('untitled-vacancy')
    # when True, updates the vacancy's search_data field
    # whenever the vacancy is saved or a plugin is saved
    # on the vacancy's content placeholder.
    update_search_on_save = getattr(
        settings,
        'VACANCIES_UPDATE_SEARCH_DATA_ON_SAVE',
        False
    )

    translations = TranslatedFields(
        title=models.CharField(_('title'), max_length=234),
        slug=models.SlugField(
            verbose_name=_('slug'),
            max_length=255,
            db_index=True,
            blank=True,
            help_text=_(
                'Used in the URL. If changed, the URL will change. '
                'Clear it to have it re-created automatically.'),
        ),
        lead_in=HTMLField(
            verbose_name=_('Summary'), default='',
            help_text=_(
                'The Summary gives the reader the main idea of the story, this '
                'is useful in overviews, lists or as an introduction to your '
                'vacancy.'
            ),
            blank=True,
        ),
        meta_title=models.CharField(
            max_length=255, verbose_name=_('meta title'),
            blank=True, default=''),
        meta_description=models.TextField(
            verbose_name=_('meta description'), blank=True, default=''),
        meta_keywords=models.TextField(
            verbose_name=_('meta keywords'), blank=True, default=''),
        meta={'unique_together': (('language_code', 'slug', ), )},

        search_data=models.TextField(blank=True, editable=False)
    )

    content = PlaceholderField('Vacancy content',
        related_name='vacancy_content')
    app_config = AppHookConfigField(
        VacanciesConfig,
        verbose_name=_('Section'),
        help_text='',)
    location = models.ForeignKey(Location,
        verbose_name=_('location'),
        blank=True, null=True)
    companies = SortedManyToManyField('js_companies.Company',
        verbose_name=_('companies'), blank=True)
    vacancy_type = models.CharField(_('type'),
        max_length=255, default='', blank=True)
    closing_date = models.DateField(_('closing date'),
        null=True, blank=True)
    external_link = models.CharField(_('external link'),
        max_length=255, default='', blank=True)
    categories = CategoryManyToManyField(Category,
        verbose_name=_('categories'),
        blank=True)
    publishing_date = models.DateTimeField(_('publishing date'),
        default=now)
    is_published = models.BooleanField(_('is published'), default=False,
        db_index=True)
    is_featured = models.BooleanField(_('is featured'), default=False,
        db_index=True)
    featured_image = FilerImageField(
        verbose_name=_('featured image'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL)

    services = SortedManyToManyField('js_services.Service',
        verbose_name=_('services'), blank=True)

    objects = RelatedManager()

    class Meta:
        ordering = ['-publishing_date']
        verbose_name = _('Vacancy')
        verbose_name_plural = _('Vacancies')

    def get_class(self):
        '''Return class name'''
        return self.__class__.__name__

    @property
    def type(self):
        '''Vacancy Type / Section.'''
        return self.app_config

    @property
    def type_slug(self):
        '''Vacancy Type / Section Machine Name'''
        return self.app_config.namespace

    @property
    def published(self):
        """
        Returns True only if the vacancy (is_published == True) AND has a
        published_date that has passed.
        """
        return (self.is_published and self.publishing_date <= now())

    @property
    def future(self):
        """
        Returns True if the vacancy is published but is scheduled for a
        future date/time.
        """
        return (self.is_published and self.publishing_date > now())

    def get_absolute_url(self, language=None):
        """Returns the url for this Vacancy in the selected permalink format."""
        if not language:
            language = get_current_language()
        kwargs = {}
        permalink_type = self.app_config.permalink_type
        if 'y' in permalink_type:
            kwargs.update(year=self.publishing_date.year)
        if 'm' in permalink_type:
            kwargs.update(month="%02d" % self.publishing_date.month)
        if 'd' in permalink_type:
            kwargs.update(day="%02d" % self.publishing_date.day)
        if 'i' in permalink_type:
            kwargs.update(pk=self.pk)
        if 's' in permalink_type:
            slug, lang = self.known_translation_getter(
                'slug', default=None, language_code=language)
            if slug and lang:
                site_id = getattr(settings, 'SITE_ID', None)
                if get_redirect_on_fallback(language, site_id):
                    language = lang
                kwargs.update(slug=slug)

        if self.app_config and self.app_config.namespace:
            namespace = '{0}:'.format(self.app_config.namespace)
        else:
            namespace = ''

        with override(language):
            return reverse('{0}vacancy-detail'.format(namespace), kwargs=kwargs)

    def get_search_data(self, language=None, request=None):
        """
        Provides an index for use with Haystack, or, for populating
        Vacancy.translations.search_data.
        """
        if not self.pk:
            return ''
        if language is None:
            language = get_current_language()
        if request is None:
            request = get_request(language=language)
        description = self.safe_translation_getter('lead_in', '')
        text_bits = [strip_tags(description)]
        for category in self.categories.all():
            text_bits.append(
                force_unicode(category.safe_translation_getter('name')))
        for tag in self.tags.all():
            text_bits.append(force_unicode(tag.name))
        if self.content:
            plugins = self.content.cmsplugin_set.filter(language=language)
            for base_plugin in plugins:
                plugin_text_content = ' '.join(
                    get_plugin_index_data(base_plugin, request))
                text_bits.append(plugin_text_content)
        return ' '.join(text_bits)

    def save(self, *args, **kwargs):
        # Update the search index
        if self.update_search_on_save:
            self.search_data = self.get_search_data()

        # slug would be generated by TranslatedAutoSlugifyMixin
        super(Vacancy, self).save(*args, **kwargs)

    def __str__(self):
        return self.safe_translation_getter('title', any_language=True)


@receiver(post_save, dispatch_uid='vacancy_update_search_data')
def update_search_data(sender, instance, **kwargs):
    """
    Upon detecting changes in a plugin used in an vacancy's content
    (PlaceholderField), update the vacancy's search_index so that we can
    perform simple searches even without Haystack, etc.
    """
    is_cms_plugin = issubclass(instance.__class__, CMSPlugin)

    if Vacancy.update_search_on_save and is_cms_plugin:
        placeholder = (getattr(instance, '_placeholder_cache', None) or
                       instance.placeholder)
        if hasattr(placeholder, '_attached_model_cache'):
            if placeholder._attached_model_cache == Vacancy:
                vacancy = placeholder._attached_model_cache.objects.language(
                    instance.language).get(content=placeholder.pk)
                vacancy.search_data = vacancy.get_search_data(instance.language)
                vacancy.save()
