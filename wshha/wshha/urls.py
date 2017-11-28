"""wshha URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from homeautomation import views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', views.index, name='index'),
    url(r'^test/$', views.test, name='test'),
    url(r'^switch/(?P<lightid>[0-9\w ]+)/(?P<state>\w+)/$', views.switch, name='switch'),
    url(r'^color/(?P<lightid>[\w ]+)/(?P<colortype>\w+)/(?P<x>[0-9]+)/(?P<y>[0-9]+)/(?P<z>[0-9]+)/$', views.color, name='color'),
    url(r'^tv/remote/(?P<command>\w+)/$', views.tv_remote, name='tv_remote'),
    url(r'^plotdata/$', views.plotdata, name='plotdata'),
]
