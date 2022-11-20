from django.shortcuts import render


# Create your views here.
# /goods/index
def index(request):
    """首页"""
    return render(request, 'index.html')
