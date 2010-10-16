Code for tracking server-side activities on Google App Engine.

It is a single file: ga.py
Call track_page_view(path) to send the request to Google Analytics.

Remember to replace the following lines as appropriate:
ACCOUNT = 'UA-1234567-1'
DOMAIN = 'example.com'

Once the request has been sent, it may take several hours before it shows up in analytics.
