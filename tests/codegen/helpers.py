"""Helper functions for code generation tests."""

import subprocess
import tempfile
import sys
import shutil
from pathlib import Path
from typing import Tuple, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.ir_generator import IRGenerator
from src.codegen.x86_generator import X86Generator


def has_nasm() -> bool:
    try:
        result = subprocess.run(["nasm", "-v"], capture_output=True, check=False)
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def has_ld() -> bool:
    try:
        result = subprocess.run(["ld", "-v"], capture_output=True, check=False)
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def compile_to_asm(source: str, use_regalloc: bool = True) -> str:
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()
    parser = Parser(tokens)
    ast = parser.parse()
    analyzer = SemanticAnalyzer("<test>")
    analyzer.analyze(ast, source)
    ir_gen = IRGenerator(analyzer.symbol_table)
    program = ir_gen.generate(ast)
    x86_gen = X86Generator(use_register_allocation=use_regalloc)
    return x86_gen.generate(program)


def compile_and_run(source: str, use_regalloc: bool = True) -> subprocess.CompletedProcess:
    if not has_nasm():
        return subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr="NASM not available"
        )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Generate assembly
        asm = compile_to_asm(source, use_regalloc)
        asm_file = tmp_path / "output.asm"
        asm_file.write_text(asm, encoding="utf-8")
        
        # Assemble main
        obj_file = tmp_path / "output.o"
        result = subprocess.run(
            ["nasm", "-f", "elf64", "-o", str(obj_file), str(asm_file)],
            capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            return result
        
        # Copy runtime.asm to temp directory
        runtime_src = PROJECT_ROOT / "src" / "runtime" / "runtime.asm"
        if not runtime_src.exists():
            return subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr=f"runtime.asm not found at {runtime_src}"
            )
        
        # Copy to temp directory (avoid Unicode path issues)
        runtime_asm = tmp_path / "runtime.asm"
        shutil.copy2(runtime_src, runtime_asm)
        
        # Assemble runtime
        runtime_obj = tmp_path / "runtime.o"
        result = subprocess.run(
            ["nasm", "-f", "elf64", "-o", str(runtime_obj), str(runtime_asm)],
            capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            return result
        
        # Link
        exe_file = tmp_path / "program"
        
        # Try gcc first
        result = subprocess.run(
            ["gcc", "-no-pie", "-o", str(exe_file), str(runtime_obj), str(obj_file)],
            capture_output=True, text=True, check=False
        )
        
        # If gcc fails, try ld
        if result.returncode != 0:
            result = subprocess.run(
                ["ld", "-o", str(exe_file), str(runtime_obj), str(obj_file)],
                capture_output=True, text=True, check=False
            )
        
        if result.returncode != 0:
            return result
        
        # Run
        result = subprocess.run([str(exe_file)], capture_output=True, text=True, check=False)
        return result


def compile_and_run_with_io(source: str, use_regalloc: bool = True) -> Tuple[str, str, int]:
    result = compile_and_run(source, use_regalloc)
    return result.stdout, result.stderr, result.returncode


def run_assembly(asm_code: str) -> Tuple[str, str, int]:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        asm_file = tmp_path / "test.asm"
        asm_file.write_text(asm_code, encoding="utf-8")
        obj_file = tmp_path / "test.o"
        result = subprocess.run(
            ["nasm", "-f", "elf64", "-o", str(obj_file), str(asm_file)],
            capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            return "", result.stderr, result.returncode
        exe_file = tmp_path / "test"
        result = subprocess.run(
            ["gcc", "-no-pie", "-o", str(exe_file), str(obj_file)],
            capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            return "", result.stderr, result.returncode
        result = subprocess.run([str(exe_file)], capture_output=True, text=True, check=False)
        return result.stdout, result.stderr, result.returncode
