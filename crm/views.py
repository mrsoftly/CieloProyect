from django.shortcuts import render

# Create your views here.
def crm_view(request):
    return render(request,'basecrm.html')