# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url

from cercanias_api import views

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'cercanias.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^user/', views.UserList.as_view()),
    url(r'^users/(?P<pk>[0-9]+)/$', views.UserDetail.as_view()),
    url(r'^city/(?P<pk>[0-9]+)/$', views.CityDetail.as_view()),
    url(r'^city/', views.CityList.as_view()),
    url(r'^schedule/(?P<nucleo>[0-9]+)/(?P<orig>[0-9]+)/(?P<dst>[0-9]+)/$',
        views.Schedule.as_view()),
)
