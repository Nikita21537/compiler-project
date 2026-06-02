section .text
global _start
global exit
global print_int
global print_string
global read_int
global printf

extern main

_start:
    xor rbp, rbp
    pop rdi
    mov rsi, rsp
    call main
    mov rdi, rax
    mov rax, 60
    syscall

exit:
    mov rax, 60
    syscall

; printf wrapper
printf:
    push rbp
    mov rbp, rsp
    mov rsi, rdi          ; string
    call print_string
    pop rbp
    ret

print_int:
    push rbp
    mov rbp, rsp
    sub rsp, 40

    mov rax, rdi
    mov rsi, rsp
    add rsi, 39
    mov byte [rsi], 0
    dec rsi

    test rax, rax
    jnz .convert_loop

    mov byte [rsi], '0'
    dec rsi
    jmp .print

.convert_loop:
    test rax, rax
    jz .print

    xor rdx, rdx
    mov rcx, 10
    div rcx

    add dl, '0'
    mov byte [rsi], dl
    dec rsi
    jmp .convert_loop

.print:
    inc rsi
    mov rdx, rsp
    add rdx, 39
    sub rdx, rsi

    mov rax, 1
    mov rdi, 1
    syscall

    mov rsp, rbp
    pop rbp
    ret

print_string:
    push rbp
    mov rbp, rsp

    mov rdx, rdi
    xor rcx, rcx

.count:
    cmp byte [rdx + rcx], 0
    je .write
    inc rcx
    jmp .count

.write:
    mov rax, 1
    mov rdi, 1
    mov rsi, rdx
    mov rdx, rcx
    syscall

    pop rbp
    ret

read_int:
    push rbp
    mov rbp, rsp
    sub rsp, 40

    mov rax, 0
    mov rdi, 0
    mov rsi, rsp
    mov rdx, 39
    syscall

    mov rsi, rsp
    xor rax, rax
    xor r8, r8

    cmp byte [rsi], '-'
    jne .parse_loop
    mov r8, 1
    inc rsi

.parse_loop:
    movzx rdx, byte [rsi]
    cmp rdx, 10
    je .done
    cmp rdx, 0
    je .done
    cmp rdx, '0'
    jl .done
    cmp rdx, '9'
    jg .done

    sub rdx, '0'
    imul rax, rax, 10
    add rax, rdx

    inc rsi
    jmp .parse_loop

.done:
    cmp r8, 0
    je .return
    neg rax

.return:
    mov rsp, rbp
    pop rbp
    ret

section .note.GNU-stack noalloc noexec nowrite progbits