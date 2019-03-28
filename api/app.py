import falcon
import json
from worker import celery
import celery.states as states


class SendMailResource:
    def on_get(self, req, resp, **kwargs):
        if (
            (req.params['fromaddr'] is not None) and
            (req.params['toaddr'] is not None) and
            (req.params['subject'] is not None) and
            (req.params['msg'] is not None)
        ):
            fromaddr = req.params['fromaddr']
            toaddr = req.params['toaddr']
            subject = req.params['subject']
            msg = req.params['msg']

            task_mail = celery.send_task(
                'tasks.send_mail',
                args=[
                    fromaddr,
                    toaddr,
                    subject,
                    msg
                ],
                kwargs={}
            )

            res_msg = {
                "task_id": task_mail.id,
            }
        else:
            res_msg = {
                "message": "no valid format."
            }
        resp.body = json.dumps(res_msg)


class AddTaskResource:

    def on_get(self, req, resp, **kwargs):
        if (kwargs['param1'] is not None) and \
           (kwargs['param2'] is not None):

            task = celery.send_task(
                'tasks.add',
                args=[
                    int(kwargs['param1']),
                    int(kwargs['param2'])
                ],
                kwargs={}
            )

            msg = {
                "task_id": task.id,
                "url": "/check/" + str(task.id)
            }

        else:
            msg = {
                "message": "no valid format."
            }
        resp.body = json.dumps(msg)


class CheckTaskResource:

    def on_get(self, req, resp, **kwargs):
        if kwargs['task_id'] is not None:
            task_id = kwargs['task_id']
            res = celery.AsyncResult(task_id)

            if res.state == states.PENDING:
                msg = {
                    'state': res.state
                }
            else:
                msg = {
                    'state': res.state,
                    'result': res.result
                }
        else:
            msg = {
                "message": "no valid format."
            }
        resp.body = json.dumps(msg)


app = falcon.API()
app.add_route("/mail", SendMailResource())
app.add_route("/add/{param1}/{param2}", AddTaskResource())
app.add_route("/check/{task_id}", AddTaskResource())

# if __name__ == "__main__":
#     from wsgiref import simple_server
#     httpd = simple_server.make_server("127.0.0.1", 5001, app)
#     httpd.serve_forever()
