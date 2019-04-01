from django.conf.urls import url

from .views import (
    VacancyDetail, VacancyList, CategoryVacancyList,
    YearVacancyList, MonthVacancyList, DayVacancyList,
    VacancySearchResultsList)
from .feeds import LatestVacanciesFeed, CategoryFeed

urlpatterns = [
    url(r'^$',
        VacancyList.as_view(), name='vacancy-list'),
    url(r'^feed/$', LatestVacanciesFeed(), name='vacancy-list-feed'),

    url(r'^search/$',
        VacancySearchResultsList.as_view(), name='vacancy-search'),

    url(r'^(?P<year>\d{4})/$',
        YearVacancyList.as_view(), name='vacancy-list-by-year'),
    url(r'^(?P<year>\d{4})/(?P<month>\d{1,2})/$',
        MonthVacancyList.as_view(), name='vacancy-list-by-month'),
    url(r'^(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/$',
        DayVacancyList.as_view(), name='vacancy-list-by-day'),

    # Various permalink styles that we support
    # ----------------------------------------
    # This supports permalinks with <vacancy_pk>
    # NOTE: We cannot support /year/month/pk, /year/pk, or /pk, since these
    # patterns collide with the list/archive views, which we'd prefer to
    # continue to support.
    url(r'^(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<pk>\d+)/$',
        VacancyDetail.as_view(), name='vacancy-detail'),
    # These support permalinks with <vacancy_slug>
    url(r'^(?P<slug>\w[-\w]*)/$',
        VacancyDetail.as_view(), name='vacancy-detail'),
    url(r'^(?P<year>\d{4})/(?P<slug>\w[-\w]*)/$',
        VacancyDetail.as_view(), name='vacancy-detail'),
    url(r'^(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<slug>\w[-\w]*)/$',
        VacancyDetail.as_view(), name='vacancy-detail'),
    url(r'^(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<slug>\w[-\w]*)/$',  # flake8: NOQA
        VacancyDetail.as_view(), name='vacancy-detail'),

    url(r'^category/(?P<category>\w[-\w]*)/$',
        CategoryVacancyList.as_view(), name='vacancy-list-by-category'),
    url(r'^category/(?P<category>\w[-\w]*)/feed/$',
        CategoryFeed(), name='vacancy-list-by-category-feed'),
]
