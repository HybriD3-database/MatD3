# -*- coding: utf-8 -*-


from django.conf.urls import url
from .views import *

app_name="materials"
# Create your tests here.
urlpatterns = [
        url(r'^$', SearchFormView.as_view(), name='materials_home'),
        # url(r'^all$', materials, name='materials'),
        # url(r'^ajax-search$', search_entries, name='ajax_search'),
        # url(r'^$', TestSearchFormView.as_view(), name='materials_home'),
        url(r'^(?P<pk>\d+)$', SystemView.as_view(), name='materials_system'),
        url(r'^(?P<pk>\d+)_(?P<pk_aa>\d+)_(?P<pk_ee>\d+)_(?P<pk_bs>\d+)$', SpecificSystemView.as_view(), name='specific_materials_system'),
        url(r'^(?P<id>\d+)/all-a-pos$', all_a_pos, name='all_a_pos'),
        url(r'^(?P<id>\d+)/(?P<type>.*)$', all_entries, name='all_entries'),
        url(r'^add-pub$', AddPubView.as_view(), name='add_publication'),
        url(r'^search-pub$', SearchPubView.as_view(), name='search_publication'),
        url(r'^search-system$', SearchSystemView.as_view(), name='search_system'),
        url(r'^add-system$', AddSystemView.as_view(), name='add_system'),
        url(r'^add-author$', AddAuthorView.as_view(), name='add_author'),
        url(r'^search-author$', SearchAuthorView.as_view(), name='search_author'),
        url(r'^add-a-pos$', AddAPosView.as_view(), name='add_a_pos'),
        url(r'^add-exciton-emission$', AddExcitonEmissionView.as_view(), name='add_exciton_emission'),
        url(r'^add-band-gap$', AddBandGapView.as_view(), name='add_band_gap'),
        url(r'^add-band-structure$', AddBandStructureView.as_view(), name='add_band_structure'),
        url(r'^data-dl/(?P<type>.*)/(?P<id>\d+)$', data_dl, name='data_dl')
                ]
