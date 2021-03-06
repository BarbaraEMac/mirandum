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

import os
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from datetime import datetime
from googaccount.models import CredentialsModel, AppCreds
from fanfunding.models import FanFundingUpdate
from sponsors.models import SponsorUpdate
from youtubesubs.models import YoutubeSubUpdate
from ytsubs.models import SubUpdate
from django.contrib.auth.decorators import login_required
from django.conf import settings
from oauth2client.contrib import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from oauth2client.contrib.django_orm import Storage

from django.shortcuts import render

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), '..', 'client_secrets.json')

FLOW = flow_from_clientsecrets(
    CLIENT_SECRETS,
    scope=['https://www.googleapis.com/auth/youtube'],
    redirect_uri='%sgoogleaccount/oauth2callback' % settings.SERVER_BASE)
FLOW.params['access_type'] = 'offline'
FLOW.params['approval_prompt'] = 'force'

@login_required
def setup(request):
  FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                 request.user.username)
  authorize_url = FLOW.step1_get_authorize_url()
  return HttpResponseRedirect(authorize_url)

@login_required
def auth_return(request):
  if not xsrfutil.validate_token(settings.SECRET_KEY, str(request.GET['state']),
                                 request.user.username):
    return  HttpResponseBadRequest()
  data = {'state': request.GET['state'], 'code': request.GET['code']}
  return render(request, "googaccount/label.html", data)

@login_required
def finalize(request):
  ac = AppCreds(user=request.user, label=request.POST['label'])
  ac.save()
  credential = FLOW.step2_exchange(request.POST)
  internal_label = "%s-%s" % (request.user.id, request.POST['label'])
  storage = Storage(CredentialsModel, 'id', ac, 'credential')
  storage.put(credential)
  return HttpResponseRedirect("/accounts/")

@login_required
def unlink(request, id):
  ac = AppCreds.objects.get(user=request.user, id=id)
  updaters = _get_updaters(request.user, ac)
  data = {'account': ac, 'updaters': updaters}
  return render(request, "googaccount/unlink.html", data)

@login_required
def unlink_confirm(request, id):
  ac = AppCreds.objects.get(user=request.user, id=id)

  # Delete updaters
  updaters = _get_updaters(request.user, ac)
  for updater in updaters:
    updater.delete()

  # Delete credential
  storage = Storage(CredentialsModel, 'id', ac, 'credential')
  storage.delete()

  # Delete AppsCred
  ac.delete()

  return HttpResponseRedirect("/accounts/")

def _get_updaters(user, app_creds):
  # We need to get updaters from each specific class, otherwise we cannot
  # filter by credentials so using Updater.objects.filter would return all
  # the user's updaters.

  updaters = []
  # YouTube subscribers (new)
  updaters.extend(YoutubeSubUpdate.objects.filter(user=user,
                                                  credentials=app_creds))
  # YouTube subscribers (old)
  updaters.extend(SubUpdate.objects.filter(user=user, credentials=app_creds))
  # Sponsors
  updaters.extend(SponsorUpdate.objects.filter(user=user,
                                               credentials=app_creds))
  # Fan funding
  updaters.extend(FanFundingUpdate.objects.filter(user=user,
                                                  credentials=app_creds))
  return updaters
