import os
import json
import time
from datetime import datetime
from flask import current_app, url_for

from blog.model import Post

from test.utils import FlaskTestCase


class PostTestCase(FlaskTestCase):

    def test_status(self):
        """
        Test post status endpoint
        """
        response = self.client.get(url_for('blog_status'))
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 200)
        response = self.client.get(url_for('status'))
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 200)
        self.assertEqual(len(json_response['version']), 7)

    def test_new_post(self):
        """
        Test post creation via REST API
        """
        post = {'username': 'Dan',
                'trip_id': 1,
                'title': 'Hello world',
                'content': 'Lorem ipsum dolor sit amet'}
        response = self.client.post(
                            url_for('blog_post_by_trip',
                                    username='Dan',
                                    trip_id=1),
                            headers=self._api_headers(username='Dan'),
                            data=json.dumps(post))
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIn('post', json_response)
        p = json_response['post']
        self.assertEqual(p['title'], 'Hello world')
        self.assertEqual(p['trip_id'], 1)
        self.assertEqual(p['username'], 'Dan')
        self.assertEqual(Post.query.count(), 1)
        self.assertEqual(Post.query.first().to_json(), p)

    def test_get_by_trip(self):
        """
        Test getting posts from /username/trip_id
        """
        self._post_posts(n=4)
        self.assertEqual(Post.query.count(), 4)
        resp = self.client.get('/blog/Dan/1')
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertIn('posts', json_resp)
        self.assertEqual(json_resp['total'], 4)
        posts = json_resp['posts']
        self.assertEqual(len(posts), 4)
        self.assertLess(posts[-1]['created_at'], posts[0]['created_at'])

    def test_get_by_user(self):
        """
        Test getting posts from /username
        """
        self._post_posts(n=4)
        self._post_posts(n=2, trip_id=2)
        self._post_posts(n=1, trip_id=3)
        self._post_posts(n=4, trip_id=4, username='Bob')
        self.assertEqual(Post.query.count(), 11)
        resp = self.client.get('/blog/Dan')
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(json_resp['total'], 7)

    def test_size(self):
        """
        Test size param
        """
        self._post_posts(n=14)
        self.assertEqual(Post.query.count(), 14)
        resp = self.client.get('/blog/Dan/1')
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(json_resp['total'], 14)
        self.assertEqual(len(json_resp['posts']), 10)

        resp = self.client.get('/blog/Dan/1?size=3')
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(json_resp['total'], 14)
        self.assertEqual(len(json_resp['posts']), 3)

    def test_before(self):
        """
        Test before param
        """
        self._post_posts(n=2)
        self._post_posts(n=1, trip_id=2)
        now = datetime.utcnow().isoformat()
        self._post_posts(n=4)
        self._post_posts(n=2, trip_id=2)

        self.assertEqual(Post.query.count(), 9)

        resp = self.client.get('/blog/Dan/1')
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(json_resp['total'], 6)
        self.assertEqual(len(json_resp['posts']), 6)

        resp = self.client.get('/blog/Dan/1?before={}'.format(now))
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(json_resp['total'], 2)
        self.assertEqual(len(json_resp['posts']), 2)

        resp = self.client.get('/blog/Dan')
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(json_resp['total'], 9)
        self.assertEqual(len(json_resp['posts']), 9)

        resp = self.client.get('/blog/Dan?before={}'.format(now))
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(json_resp['total'], 3)
        self.assertEqual(len(json_resp['posts']), 3)

    def test_ordering(self):
        """
        Test that posts are returned with newest first
        """
        self._post_posts(n=8)

        resp = self.client.get('/blog/Dan')
        json_resp = json.loads(resp.data.decode('utf-8'))
        dts = [post['created_at'] for post in json_resp['posts']]
        self.assertTrue(all([dts[i] > dts[i+1] for i in range(len(dts)-1)]))

    def test_delete(self):
        """
        Test delete
        """
        self._post_posts(n=2)
        self._post_posts(n=1, trip_id=2)
        self._post_posts(n=4, username='Bob', trip_id=3)
        self._post_posts(n=2, trip_id=4)

        self.assertEqual(Post.query.count(), 9)

        resp = self.client.get('/blog/Dan')
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(json_resp['total'], 5)
        self.assertEqual(len(json_resp['posts']), 5)

        resp = self.client.delete('/blog/Dan/1/2',
                                  headers=self._api_headers(username='Dan'))
        json_resp = json.loads(resp.data.decode('utf-8'))
        resp = self.client.get('/blog/Dan')
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(json_resp['total'], 4)
        resp = self.client.delete('/blog/Dan/1/1')
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(resp.status_code, 403)
        resp = self.client.get('/blog/Dan')
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(json_resp['total'], 4)
