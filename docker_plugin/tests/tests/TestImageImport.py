# coding=utf-8
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import os
import SimpleHTTPServer
import SocketServer
import multiprocessing


from tests.tests.TestCaseBase import TestCaseBase


_PORT = 8000
_HOST = 'localhost'


def _get_request(httpd, workdir):
    os.chdir(workdir)
    httpd.handle_request()
    httpd.server_close()


class TestImageImport(TestCaseBase):
    def test_image_import(self):
        image_url = 'http://{}:{}/{}'.format(_HOST, _PORT, 'mini.tar.xz')
        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler

        class TCPServer(SocketServer.TCPServer):
            allow_reuse_address = True
        httpd = TCPServer((_HOST, _PORT), Handler)
        request_process = multiprocessing.Process(
            target=_get_request,
            args=(httpd, self.blueprint_dir))
        request_process.start()
        self._execute(['create', 'configure'],
                      image_import={'src': image_url},
                      image_build={'stub': 'prop'},
                      container_config={'command': '/bin/true'},
                      container_remove={'remove_image': True})
        request_process.join()
        self.assertIsNotNone(
            self.client.inspect_image(self.runtime_properties['image']))
