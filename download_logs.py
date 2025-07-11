#!/usr/bin/env python3
import subprocess

# Run this code to fetch the logs on IBM Cloud

subprocess.run([
    "scp",
    "-r",
    "attack@honey-attack:project-violet/logs",
    "."
])