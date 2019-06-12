# This file is covered by the BSD license. See LICENSE in the root directory.
from django.urls import include
from django.urls import path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register('properties', views.PropertyViewSet)
router.register('units', views.UnitViewSet)

app_name = 'materials'
urlpatterns = [
    path('', include(router.urls)),
    path('search', views.SearchFormView.as_view(), name='search'),
    path('<int:pk>', views.SystemView.as_view(), name='system'),
    path('dataset/<int:pk>', views.DatasetView.as_view(), name='dataset'),
    path('dataset/<int:pk>/toggle-visibility/<str:view_name>',
         views.toggle_visibility, name='toggle_visibility'),
    path('dataset/<int:pk>/toggle-is-figure/<str:view_name>',
         views.toggle_is_figure, name='toggle_is_figure'),
    path('dataset/<int:pk>/delete/<str:view_name>',
         views.delete_dataset, name='delete_dataset'),
    path('dataset/<int:pk>/files', views.dataset_files, name='dataset_files'),
    path('dataset/<int:pk>/data.txt', views.dataset_data, name='dataset_data'),
    path('dataset/<int:pk>/image.png', views.dataset_image,
         name='dataset_image'),
    path('add-pub', views.AddPubView.as_view(), name='add_reference'),
    path('add-system', views.AddSystemView.as_view(), name='add_system'),
    path('author-count', views.AddAuthorsToReferenceView.as_view(),
         name='author_count'),
    path('add-data', views.AddDataView.as_view(), name='add_data'),
    path('submit-data', views.submit_data, name='submit_data'),
    path('update-system/<int:pk>', views.SystemUpdateView.as_view(),
         name='update_system'),
    path('reference/<int:pk>', views.ReferenceDetailView.as_view(),
         name='reference'),
    path('autofill-input-data', views.autofill_input_data),
    path('<int:system_pk>/property-all-entries/<int:prop_pk>',
         views.PropertyAllEntriesView.as_view(), name='property_all_entries'),
    path('data-for-chart/<int:pk>', views.data_for_chart,
         name='data_for_chart'),
    path('get-atomic-coordinates/<int:pk>', views.get_atomic_coordinates,
         name='get_atomic_coordinates'),
    path('get-dropdown-options/<str:name>', views.get_dropdown_options,
         name='get_dropdown_options'),
    path('get-subset-values/<int:pk>', views.get_subset_values,
         name='get_subset_values'),
    path('get-jsmol-input/<int:pk>', views.get_jsmol_input,
         name='get_jsmol_input'),
    path('report-issue', views.report_issue, name='report_issue'),
    path('extract-k-from-control-in', views.extract_k_from_control_in),
    path('linked-data/<int:pk>', views.LinkedDataView.as_view(),
         name='linked_data'),
    path('prefilled-form/<int:pk>', views.prefilled_form,
         name='prefilled_form'),
]
