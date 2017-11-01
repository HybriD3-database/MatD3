from django.shortcuts import render

# Create your views here.

def index(request):
	return render(request, 'materialstest/home.html')

def contact(request):
	return render(request, 'materialstest/basic.html', {'content': ['contact me at:', 'xd24@duke.edu']})
