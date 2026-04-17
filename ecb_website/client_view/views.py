from django.shortcuts import render


def home(request):
    return render(request, 'client_view/home.html')



def about(request):
    return render(request, 'client_view/about.html')



def contact(request):
    return render(request, 'client_view/contact.html')