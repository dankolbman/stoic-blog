import os
import json
import jwt
import unittest
from blog import create_app, db
from flask import url_for


class FlaskTestCase(unittest.TestCase):
    """ Contains base logic for setting up a Flask app """

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _api_headers(self, username=None):
        """
        Returns headers for a json request along with a JWT for authenticating
        as a given user
        """
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        if username:
            auth = jwt.encode({"identity": {"username": username},
                               "nbf": 1493862425,
                               "exp": 9999999999,
                               "iat": 1493862425},
                              'secret', algorithm='HS256')
            headers['Authorization'] = 'JWT ' + auth.decode('utf-8')
        return headers

    def _post_posts(self, n=1, username='Dan', trip_id=1, **kwargs):
        """ posts a bunch of posts """
        for i in range(n):
            post = {'username': username,
                    'trip_id': trip_id,
                    'title': 'Hello World',
                    'content': 'Lorem ipsum'}
            post.update(kwargs)
            post = json.dumps(post)

            resp = self.client.post(
                    url_for('blog_post_by_trip',
                            username=username,
                            trip_id=trip_id),
                    headers=self._api_headers(username=username),
                    data=post)
