#  Copyright 2016 Google Inc. All Rights Reserved.
#  
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  
#      http://www.apache.org/licenses/LICENSE-2.0
#  
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License. 

from datetime import  datetime
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from twitchfollows.models import TwitchFollowUpdate, TwitchFollowAlertConfig 
from twitchaccount.models import TwitchAppCreds
from django.shortcuts import render
from twitchfollows.signals import config_to_alert
import django.forms as forms
from django.forms import ModelForm
from main.support import ac
from twitchaccount.forms import CredsChoices, creds_form
MODULE_NAME = "twitchfollows"

@login_required
def home(request):
    ffconfigs = TwitchFollowUpdate.objects.filter(credentials__user=request.user)
    alerts = TwitchFollowAlertConfig.objects.filter(user=request.user)
    return render(request, "twitchfollows/home.html", {'configs': ffconfigs,
        'alerts': alerts})

@login_required
def setup(request):
    CredsForm = creds_form(request.user)
    
    if request.POST:
        f = CredsForm(request.POST)
        if f.is_valid():
            creds = f.cleaned_data['account']
            ffu = TwitchFollowUpdate(credentials=creds, type="twitchfollows", user=request.user)
            ffu.save()
            return HttpResponseRedirect("/twitchfollows/")
    else:
        f = CredsForm()
    return render(request, "twitchfollows/setup.html", {'form': f})

@login_required
def test_alert(request, alert_id=None):
    ac = TwitchFollowAlertConfig.objects.get(pk=int(alert_id), user=request.user)
    config_to_alert(ac, {'name': 'Livestream Alerts'}, test=True)
    if request.GET.get('ret') == 'alerts':
        return HttpResponseRedirect("/alert_page")
    return HttpResponseRedirect("/twitchfollows/")

class AlertForm(ModelForm):
    class Meta:
        model = TwitchFollowAlertConfig
        fields = ['image_url', 'sound_url', 'alert_text', 'blacklist', 'font', 'font_size', 'font_color', 'layout', 'animation_in', 'animation_out', 'font_effect']
        widgets = {
            'image_url': forms.TextInput(attrs={'size': 50}),
            'sound_url': forms.TextInput(attrs={'size': 50}),
            'alert_text': forms.TextInput(attrs={'size': 50}),
        }

alert_config = ac(
    MODULE_NAME,
    AlertForm,
    TwitchFollowAlertConfig,
    {"alert_text": "[[name]] has followed!"})
