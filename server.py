import json

from tornado.options import define, options
import tornado.httpserver
from tornado import httpclient
import tornado.ioloop
import tornado.options
import tornado.web

from auth import Auth

define("port", default=8000, help="port to listen on", type=int)

search_form = '''
<html>
  <head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.0.0-beta1/jquery.min.js"></script>
  </head>
  <body>
    <div>

      <form action="/search" method="GET" id="search-form">

        <label for="name">
          Filter by Member of Congress
        </label>
        <input name="name" type="text" />

        <label for="term">
          Search by Content
        </label>
        <input name="term" type="text" />

        <input type="submit" value="Submit" />

      </form>

      <div id="tweets">
      </div>

    </div>
    <script>
      $(function() {
        $('#search-form').on('submit', function(e) {
          e.preventDefault();
          var $target = $(e.target);
          var vals = $target.serialize();
          $target.find('input[type="text"]').val('');
          var endpoint = $target.attr('action');
          $.get(endpoint, vals, function(data) {
            //TODO: handle error
            $('#tweets').html('');
            var data = JSON.parse(data);
            data.forEach(function(tweet) {
              var tweetDiv = "<div>" +
                "<div>" + new Date(tweet.created_at).toTimeString() + "</div>" +
                "<div>" + tweet.member + "</div>" +
                "<div>" + tweet.text + "</div>" +
              "</div>";
              $('#tweets').append(tweetDiv);
            });
          });
        });
      })
    </script>
  </body>
</html>
'''

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(search_form)

class SearchHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        member_name = self.get_argument("name")
        search_term = self.get_argument("term")
        write_result = write_result_cb(self)
        search_client.do_search(member_name, search_term, write_result)
        
def write_result_cb(handler):
    def write_result(result):
        # TODO: handle error
        print(result.error)
        formatted_results = []
        body = json.loads(result.body)
        for item in body["hits"]["hits"]:
            formatted_results.append(item["_source"])
        handler.write(json.dumps(formatted_results))
        handler.finish()
    return write_result

class SearchClient:

    def __init__(self):
        self.url = "%s/congress/tweets/_search" % Auth.es_host
        self.http_client = httpclient.AsyncHTTPClient()

    def do_search(self, member_name, search_term, cb):
        data = {
            "query": {
                "bool": {
                    "must": []
                }
            }
        }
        if member_name != "":
            restriction = {"match": {"member": member_name}}
            data["query"]["bool"]["must"].append(restriction)
        if search_term != "":
            restriction = {"match": {"text": search_term}}
            data["query"]["bool"]["must"].append(restriction)
        data_json = json.dumps(data)
        self.http_client.fetch(self.url, cb, method="GET", body=data_json, allow_nonstandard_methods=True)

search_client = SearchClient()

if __name__ == '__main__':
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[(r'/', IndexHandler), (r'/search', SearchHandler)]
    )
    http_server = tornado.httpserver.HTTPServer(app)
    print("Listening on", options.port)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
