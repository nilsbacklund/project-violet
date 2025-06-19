import subprocess

def start_dockers():
    try:
        print("Starting Docker containers...")
        subprocess.run(["sudo", "docker-compose","-f", "Blue_Lagoon/docker-compose.yml", "build"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["sudo", "docker-compose", "-f", "Blue_Lagoon/docker-compose.yml","up", "-d"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print("Docker containers started")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred in starting docker containers: {e}")

def stop_dockers():
    try:
        print("Stopping Docker containers...")
        subprocess.run(["sudo", "docker-compose", "-f", "Blue_Lagoon/docker-compose.yml","down"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print("Docker containers stopped")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred in stopping docker containers: {e}")
