# This file is covered by the BSD license. See LICENSE in the root directory.
from django.urls import include
from django.urls import path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register('references', views.ReferenceViewSet)
router.register('systems', views.SystemViewSet)
router.register('properties', views.PropertyViewSet)
router.register('units', views.UnitViewSet)
router.register('datasets', views.DatasetViewSet)

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
    path('dataset/<int:pk>/verify/<str:view_name>',
         views.verify_dataset, name='verify_dataset'),
    path('add-data', views.AddDataView.as_view(), name='add_data'),
    path('import-data', views.ImportDataView.as_view(), name='import_data'),
    path('submit-data', views.submit_data, name='submit_data'),
    path('reference/<int:pk>', views.ReferenceDetailView.as_view(),
         name='reference'),
    path('autofill-input-data', views.autofill_input_data),
    path('<int:system_pk>/property-all-entries/<int:prop_pk>',
         views.PropertyAllEntriesView.as_view(), name='property_all_entries'),
    path('data-for-chart/<int:pk>', views.data_for_chart,
         name='data_for_chart'),
    path('get-atomic-coordinates/<int:pk>', views.get_atomic_coordinates,
         name='get_atomic_coordinates'),
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
    path('mint-doi/<int:pk>', views.MintDoiView.as_view(), name='mint_doi'),
    path('figshare-callback', views.figshare_callback,
         name='figshare_callback'),
]
