from functools import wraps
import json
import sys
import uuid
import os

CODE = {
    "default": """<>
<strong>Hello World!</strong><br/>
<EG.Button onClick={() => callbacks.log("Clicked")}>Do something</EG.Button>
</>""",
    "audio": """<>
    <WB.Audio />
    </>""",
    "image": """<>
    <WB.Image />
    </>""",
    "webcam": """<>
    <WB.Webcam />
    </>""",
    "draw": """<>
    <WB.Draw />
    </>"""
}


class Inference(object):
    def render(self, content, mimetype="html"):
        import IPython
        display(IPython.display.HTML(content))

    def template(self, code, callbacks=[], host=None):
        template = open(os.path.join(os.path.dirname(__file__), "template.js"), "r").read()
        template = template.replace("\"__WANDB__\"", json.dumps({"code": code, "callbacks": callbacks}))
        template = template.replace("__HOST__", os.environ.get(
            "WANDB_UI_URL", host or "https://cocky-kowalevski-373523.netlify.com"))
        return template

    def __call__(self, inp, out, options={}):
        def wrap(f):
            template = "default"
            if "image" in inp:
                if options.get("webcam"):
                    template = "webcam"
                elif options.get("canvas"):
                    template = "draw"
                else:
                    template = "image"
            elif "audio" in inp:
                template = "audio"
            elif "text" in inp:
                template = "text"
            callbacks = []
            try:
                from google.colab import output
                callback = "wb_"+str(uuid.uuid4())
                output.register_callback(callback, f)
                callbacks.append(callback)
            except ImportError:
                pass
            self.render('''
                <div id="root"></div>
                <script type="text/javascript">
                    %s
                </script>
                ''' % self.template(CODE[template]), callbacks)

            @wraps(f)
            def wrapper(*args, **kwargs):
                return f(inp, out, *args, **kwargs)
            return wrapper
        return wrap


inference = Inference()
