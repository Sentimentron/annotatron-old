"""annotatron URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
import control.views
import corpora.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^control/setup/user', control.views.InitialSetupUserView.as_view(), name='setup-user'),
    url(r'^control/setup/faas', control.views.InitialSetupFaasView.as_view(), name='setup-faas'),

    url(r'^v1/control/setup', control.views.RequiresSetupView.as_view(), name='v1-setup-required'),

    url(r'^v1/corpora/$', corpora.views.CorpusView.as_view()),
    url(r'^v1/corpora/(?P<corpus>[-\_\w]+)/(?P<asset>[-\_\w]+)/$', corpora.views.AssetContentView.as_view()),
    url(r'^v1/corpora/(?P<corpus>[-\_\w]+)/$', corpora.views.AssetView.as_view()),

    url(r'^v1/debug/hello', control.views.DebugSayHelloAPIView.as_view()),
    url(r'^v1/debug/users/$', control.views.DebugUserCreateView.as_view(), name='debug-user'),
    url(r'^v1/debug/users/remove', control.views.DebugUserDeleteView.as_view(), name='debug-user-delete'),
    url(r'^v1/debug/assets/remove', corpora.views.DebugRemoveAssetsView.as_view(), name='debug-assets-delete'),
    url(r'^v1/debug/corpora/remove', corpora.views.DebugRemoveCorporaView.as_view(), name='debug-corpora-delete'),

    url(r'^v1/auth', include('rest_auth.urls')),

    url(r'^$', control.views.IndexView.as_view(), name='home')
]
