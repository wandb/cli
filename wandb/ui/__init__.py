from functools import wraps
from google.colab import output
import IPython

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


def __call__(inp, out, options={}):
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
    display(IPython.display.Javascript('''
    window.initialScope = {
        "code": %s
    }
    ''' % CODE[template]))

    def wrap(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(input, output, *args, **kwargs)
        return wrapper
    return wrap
