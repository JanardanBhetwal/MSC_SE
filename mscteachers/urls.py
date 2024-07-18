from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.urls import path, re_path
from django.views.generic import TemplateView

from college import views




urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    re_path(r'^.*export.*$', views.exportform),
    re_path(r'^.*dumpteachers.*$', views.exportteachers, name='dumpteachers'),
    re_path(r'^.*dumpexperts.*$', views.exportexperts, name='dumpexperts'),
    re_path(r'^.*cloneyear.*$', views.cloneyear, name='cloneyear'),
    re_path(r'^.*about.*$', TemplateView.as_view(template_name='admin/about.html'), name='aboutsystem'),
    re_path(r'^.*docgen/', include(('thesis.urls', 'thesis'))),

]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      re_path(r'^__debug__/', include(debug_toolbar.urls)),
                  ] + urlpatterns
