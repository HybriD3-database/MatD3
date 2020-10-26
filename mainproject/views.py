from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models import F
from django.db.models import Q
from django.shortcuts import render
from django.template import TemplateDoesNotExist


def index(request):
    try:
        return render(request, 'mainproject/home.html')
    except TemplateDoesNotExist:
        return render(request, 'mainproject/home_default.html')


def contributors(request):
    User = get_user_model()
    num_created = Count('materials_dataset_created_by', distinct=True)
    num_updated_total = Count('materials_dataset_updated_by', distinct=True)
    num_updated_same = Count(
        'materials_dataset_updated_by',
        filter=Q(materials_dataset_updated_by=F(
            'materials_dataset_created_by')), distinct=True)
    num_updated = num_updated_total-num_updated_same
    contributors = User.objects.all().annotate(
        num_created=num_created).annotate(
            num_updated=num_updated).order_by('-num_created', '-num_updated')
    try:
        designers = [
            User.objects.get(username='volkerblum'),
            User.objects.get(username='xd24'),
            User.objects.get(username='raul_l'),
            User.objects.get(username='smj64'),
            User.objects.get(username='matti'),
            User.objects.get(username='cbclayto'),
        ]
    except User.DoesNotExist:
        designers = []
    return render(request, 'mainproject/contributors.html', {
        'designers': designers, 'contributors': contributors,
    })
