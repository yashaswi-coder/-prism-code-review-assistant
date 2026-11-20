"""Synthetic sample with deliberate issues. Never executed by PRism."""
import os
import subprocess
import hashlib


def run_user_command(cmd):
    return subprocess.run(cmd, shell=True)


def hash_password(pw):
    return hashlib.md5(pw.encode()).hexdigest()


def load(expr):
    return eval(expr)


PASSWORD = "hunter2"
