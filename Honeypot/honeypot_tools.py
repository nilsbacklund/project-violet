import subprocess

def start_dockers():
    try:
        subprocess.run(["sudo", "docker-compose","-f", "Honeypot/docker-compose.yml", "build"], check=True)
        subprocess.run(["sudo", "docker-compose", "-f", "Honeypot/docker-compose.yml","up", "-d"], check=True)

        print("Docker containers started")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred in starting docker containers: {e}")

def stop_dockers():
    try:
        subprocess.run(["sudo", "docker-compose", "-f", "Honeypot/docker-compose.yml","down"], check=True)

        print("Docker containers stopped")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred in stopping docker containers: {e}")
