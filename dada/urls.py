from app.views import *
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^(?i)question-answer/$', question_answer, name='question-answer'),
    url(r'^(?i)(?P<entry_type>question-answer)/create/$', create_entry, name='create-entry'),
    # AJAX functions:
    url(r'^(?i)x/get-question-answer/$', ajax_get_question_answer, name='ajax-get-question-answer'),
    url(r'^(?i)x/create-entry/$', ajax_create_entry, name='ajax-create-entry'),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
