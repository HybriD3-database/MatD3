from django.urls import path
from django.urls import re_path
from materials import views


app_name = 'materials'
urlpatterns = [
    path('', views.SearchFormView.as_view(), name='materials_home'),
    path('<int:pk>', views.SystemDetailView.as_view(),
         name='materials_system'),
    path('<int:sys>/update-band-structure/<int:pk>',
         views.BandStructureUpdateView.as_view(),
         name='update_band_structure'),
    path('<int:sys>/delete-band-structure/<int:pk>',
         views.BandStructureDeleteView.as_view(),
         name='delete_band_structure'),
    path('<int:system_pk>/publish-system/<int:dataset_pk>/<path:return_path>',
         views.toggle_dataset_visibility, name='publish_system'),
    path('<int:system_pk>/toggle-plotted/<int:dataset_pk>/<path:return_path>',
         views.toggle_dataset_plotted, name='toggle_plotted'),
    path('download-dataset-files/<int:pk>', views.download_dataset_files,
         name='download_dataset_files'),
    path('download-input-data-files/<int:pk>', views.download_input_files,
         name='download_input_files'),
    path('<int:system_pk>/delete-dataset/<int:dataset_pk>/<path:return_path>',
         views.delete_dataset_and_files, name='delete_dataset'),
    path('add-pub', views.AddPubView.as_view(), name='add_reference'),
    path('search-pub', views.SearchPubView.as_view(),
         name='search_reference'),
    path('search-system', views.SearchSystemView.as_view(),
         name='search_system'),
    path('add-system', views.AddSystemView.as_view(), name='add_system'),
    path('add-author', views.AddAuthorView.as_view(), name='add_author'),
    path('search-author', views.SearchAuthorView.as_view(),
         name='search_author'),
    path('author-count', views.AddAuthorsToReferenceView.as_view(),
         name='author_count'),
    path('add-band-structure', views.AddBandStructureView.as_view(),
         name='add_band_structure'),
    path('add-data', views.AddDataView.as_view(), name='add_data'),
    path('add-property', views.add_property, name='add_property'),
    path('add-unit', views.add_unit, name='add_unit'),
    path('submit-data', views.submit_data, name='submit_data'),
    path('add-tag', views.AddTagView.as_view(), name='add_tag'),
    re_path(r'^data-dl/(?P<data_type>.*)/(?P<pk>\d+)$', views.data_dl,
            name='data_dl'),
    path('update-system/<int:pk>', views.SystemUpdateView.as_view(),
         name='update_system'),
    path('reference-data/<int:pk>', views.reference_data,
         name='reference_data'),
    path('dataset-<int:pk>/image.png', views.dataset_image,
         name='dataset_image'),
    path('dataset-<int:pk>/data.txt', views.dataset_data, name='dataset_data'),
    path('reference/<int:pk>', views.ReferenceDetailView.as_view(),
         name='reference'),
    path('autofill-input-data', views.autofill_input_data,
         name='autofill_input_data'),
    path('<int:system_pk>/property-all-entries/<int:prop_pk>',
         views.PropertyAllEntriesView.as_view(), name='property_all_entries'),
    path('data-for-chart/<int:pk>', views.data_for_chart,
         name='data_for_chart'),
    path('get-lattice-parameters/<int:pk>', views.get_lattice_parameters,
         name='get_lattice_parameters'),
    path('get-dropdown-options/<str:name>', views.get_dropdown_options,
         name='get_dropdown_options'),
    path('get-series-values/<int:pk>', views.get_series_values,
         name='get_series_values'),
    path('get-jsmol-input/<int:pk>', views.get_jsmol_input,
         name="get_jsmol_input"),
    re_path(r'^(?P<pk>\d+)/(?P<data_type>.*)$', views.all_entries,
            name='all_entries'),
]
