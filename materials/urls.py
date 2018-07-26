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
        url(r'^(?P<pk>\d+)_(?P<pk_aa>\d+)_(?P<pk_syn>\d+)_(?P<pk_ee>\d+)_(?P<pk_bs>\d+)$', SpecificSystemView.as_view(), name='specific_materials_system'),
        url(r'^(?P<sys>\d+)/update-atomic-positions/(?P<pk>\d+)$', AtomicPositionsUpdateView.as_view(), name='update_a_pos'),
        url(r'^(?P<sys>\d+)/delete-atomic-positions/(?P<pk>\d+)$', AtomicPositionsDeleteView.as_view(), name='delete_a_pos'),
        url(r'^(?P<sys>\d+)/update-synthesis/(?P<pk>\d+)$', SynthesisMethodUpdateView.as_view(), name='update_synthesis'),
        url(r'^(?P<sys>\d+)/delete-synthesis/(?P<pk>\d+)$', SynthesisMethodDeleteView.as_view(), name='delete_synthesis'),
        url(r'^(?P<sys>\d+)/update-exciton-emission/(?P<pk>\d+)$', ExcitonEmissionUpdateView.as_view(), name='update_exciton_emission'),
        url(r'^(?P<sys>\d+)/delete-exciton-emission/(?P<pk>\d+)$', ExcitonEmissionDeleteView.as_view(), name='delete_exciton_emission'),
        url(r'^(?P<sys>\d+)/update-band-structure/(?P<pk>\d+)$', BandStructureUpdateView.as_view(), name='update_band_structure'),
        url(r'^(?P<sys>\d+)/delete-band-structure/(?P<pk>\d+)$', BandStructureDeleteView.as_view(), name='delete_band_structure'),
        url(r'^(?P<sys>\d+)/update-property/(?P<pk>\d+)$', PropertyUpdateView.as_view(), name='update_property'),
        url(r'^(?P<sys>\d+)/delete-property/(?P<pk>\d+)$', PropertyDeleteView.as_view(), name='delete_property'),
        url(r'^(?P<id>\d+)/all-a-pos$', all_a_pos, name='all_a_pos'),
        url(r'^(?P<id>\d+)/(?P<type>.*)$', all_entries, name='all_entries'),
        url(r'^add-pub$', AddPubView.as_view(), name='add_publication'),
        url(r'^search-pub$', SearchPubView.as_view(), name='search_publication'),
        url(r'^search-system$', SearchSystemView.as_view(), name='search_system'),
        url(r'^add-system$', AddSystemView.as_view(), name='add_system'),
        url(r'^add-author$', AddAuthorView.as_view(), name='add_author'),
        url(r'^search-author$', SearchAuthorView.as_view(), name='search_author'),
        url(r'^author-count$', AddAuthorsToPublicationView.as_view(), name='author_count'),
        url(r'^add-a-pos$', AddAPosView.as_view(), name='add_a_pos'),
        url(r'^add-exciton-emission$', AddExcitonEmissionView.as_view(), name='add_exciton_emission'),
        url(r'^add-synthesis$', AddSynthesisMethodView.as_view(), name='add_synthesis'),
        url(r'^add-band-structure$', AddBandStructureView.as_view(), name='add_band_structure'),
        url(r'^add-material-property$', AddMaterialPropertyView.as_view(), name='add_material_property'),
        url(r'^add-data$', AddDataView.as_view(), name='add_data'),
        url(r'^add-tag$', AddTagView.as_view(), name='add_tag'),
        url(r'^data-dl/(?P<type>.*)/(?P<id>\d+)$', data_dl, name='data_dl'),
        url(r'^update-system/(?P<pk>\d+)$', SystemUpdateView.as_view(), name='update_system')
                ]