import subprocess
from config import honeypot

def init_docker():
    subprocess.run(["sudo", "docker", "stop", "kali3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "docker", "rm", "kali3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "docker", "stop", "cow"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "docker", "rm", "cow"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "docker", "stop", "blue_lagoon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "docker", "rm", "blue_lagoon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "docker", "network", "rm", "blue_lagoon_innet"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def start_dockers():
    print("Starting Docker containers...")
    subprocess.run(["sudo", "docker-compose","-f", f"Blue_Lagoon/docker-compose-{honeypot}.yml", "build"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "docker-compose", "-f", f"Blue_Lagoon/docker-compose-{honeypot}.yml","up", "-d"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Docker containers started")


def stop_dockers():
    print("Stopping Docker containers...")
    subprocess.run(["sudo", "docker-compose", "-f", f"Blue_Lagoon/docker-compose-{honeypot}.yml","down"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Docker containers stopped")
