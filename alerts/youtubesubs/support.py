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

import json
import httplib2
from youtubesubs.models import *
from googaccount.models import CredentialsModel
from django.contrib.auth.models import User

from oauth2client.contrib.django_orm import Storage
BASE_URL = "https://www.googleapis.com/youtube/v3/"

def run_youtubesubs(ffu):
    added = 0
    storage = Storage(CredentialsModel, 'id', ffu.credentials, 'credential')
    credential = storage.get()
    if credential is None or credential.invalid == True:
        raise Exception("bad creds")
        return added
    http = httplib2.Http()
    http = credential.authorize(http)
    resp, data = http.request("%ssubscriptions?part=subscriberSnippet&myRecentSubscribers=true&maxResults=50" % BASE_URL)
    data = json.loads(data)
    if 'error' in data:
        raise Exception("Error fetching youtubesubs: %s" % json.dumps(data['error']))
    events = []
    if 'items' in data:
        for i in data['items']:
            unique_id = i['subscriberSnippet']['channelId']
            if YoutubeSubEvent.objects.filter(external_id=i['id'], updater=ffu).count() > 0:
                break

            details = json.dumps(i)
            try:
                ffe = YoutubeSubEvent(external_id=i['id'], updater=ffu, details=details)
                events.append(ffe)
            except Exception, E:
                print "Failed in individual youtubesubs run: %s\nData:\n%s" % (E, details)
            added += 1
        for event in reversed(events):
            try:
                event.save()
                added += 1
            except Exception, E:
                print "Failed in individual sponsor run: %s\nData:\n%s" % (E, ffe.details)

    return added
