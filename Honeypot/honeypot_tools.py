import subprocess

def rebuild_dockers():
    try:
        subprocess.run(["sudo", "docker-compose", "down"], check=True)
        subprocess.run(["sudo", "docker-compose", "build"], check=True)
        subprocess.run(["sudo", "docker-compose", "up", "-d"], check=True)

        print("Docker containers rebuilt")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred in rebuilding docker containers: {e}")


def start_dockers():
    try:
        subprocess.run(["sudo", "docker-compose", "build"], check=True)
        subprocess.run(["sudo", "docker-compose", "up", "-d"], check=True)

        print("Docker containers started")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred in starting docker containers: {e}")

def stop_dockers():
    try:
        subprocess.run(["sudo", "docker-compose", "down"], check=True)

        print("Docker containers stopped")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred in stopping docker containers: {e}")
