"""BlockchainProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from BlockchainProject.blockchain import views
urlpatterns = [
    path('admin/', admin.site.urls),
    url('^mining$', views.mining, name="mining"),
    url('^get_full_chain$', views.get_full_chain, name="get_full_chain"),
    url('^chain_is_valid$', views.chain_is_valid, name="chain_is_valid"),
    url('^add_new_transaction$', views.add_new_transaction, name="add_new_transaction"),
    url('^connect_new_node$', views.connect_new_node, name="connect_new_node"),
    url('^sync_chain$', views.sync_nodes, name="cync_chain"),
]


