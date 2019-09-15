from functools import wraps
import json
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


class Inference(object):
    def render(self, content, mimetype="html"):
        import IPython
        #from google.colab import output
        display(IPython.display.HTML(content))

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
        self.render('''
            <div id="root"></div>
            <script type="text/javascript">
            const host = "%s"
            window.initialScope = %s
            document.head.innerHTML = document.head.innerHTML + "<base href='" + host + "' />";
            const body = fetch(host+"/asset-manifest.json").then((a) => a.json().then(j => j));
            function load(url, type='js') {
                const promise = new Promise((resolve, reject) => {
                    const node = document.createElement(type === 'css' ? 'link' : 'script');
                    if(type === 'css') {
                        node.href = value
                        node.rel = 'stylesheet'
                    } else {
                        node.src = value
                    }
                    node.onload = resolve;
                    node.onerror = reject;
                    document.head.appendChild(node);
                });
                return promise
            }
            for (let [key, value] of Object.entries(body)) {
                if(key.endsWith('js')) {
                    load(value)
                } else if(key.endsWith('css')) {
                    load(value, 'css')
                }
            }
            </script>
            ''' % ("https://cocky-kowalevski-373523.netlify.com", json.dumps({"code": CODE[template]})))

        def wrap(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                return f(inp, out, *args, **kwargs)
            return wrapper
        return wrap


inference = Inference()
