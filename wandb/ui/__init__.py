from functools import wraps
from google.colab import output
import json
import IPython
import sys

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


class UI(object):
    def __call__(self, inp, out, options={}):
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
        display(IPython.display.HTML('''
        <div id="root"></div>
        <script type="text/javascript">
        window.initialScope = %s
        </script>
        <link href="https://cocky-kowalevski-373523.netlify.com/static/css/main.0d13eeef.chunk.css" rel="stylesheet">
        <script src="https://cocky-kowalevski-373523.netlify.com/static/js/2.9ae5943a.chunk.js" />
        <script src="https://cocky-kowalevski-373523.netlify.com/static/js/main.bd6e96d6.chunk.js" />
        ''' % json.dumps({"code": CODE[template]})))

        def wrap(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                return f(input, output, *args, **kwargs)
            return wrapper
        return wrap


sys.modules[__name__] = UI()
