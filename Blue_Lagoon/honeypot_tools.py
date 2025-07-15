import subprocess
from config import honeypot
import os

def init_docker():
    # subprocess.run(["sudo", "docker", "stop", "a_kali_1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # subprocess.run(["sudo", "docker", "rm", "a_kali_1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # subprocess.run(["sudo", "docker", "stop", "cow"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # subprocess.run(["sudo", "docker", "rm", "cow"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # subprocess.run(["sudo", "docker", "stop", "a_blue_lagoon_1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # subprocess.run(["sudo", "docker", "rm", "a_blue_lagoon_1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # subprocess.run(["sudo", "docker", "network", "rm", "a_innet"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pass


def start_dockers():
    print("Starting Docker containers...")
    subprocess.run(["sudo", "docker-compose","-f", f"docker-compose.yml", "-p", os.environ.get("RUNID"), "build"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "docker-compose", "-f", f"docker-compose.yml", "-p", os.environ.get("RUNID"), "up", "-d"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Docker containers started")


def stop_dockers():
    print("Stopping Docker containers...")
    subprocess.run(["sudo", "docker-compose", "-f", f"docker-compose.yml", "-p", os.environ.get("RUNID"),"down"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Docker containers stopped")
