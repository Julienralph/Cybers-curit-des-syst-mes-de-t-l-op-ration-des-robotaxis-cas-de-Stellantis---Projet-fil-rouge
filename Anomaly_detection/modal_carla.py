import modal

app = modal.App("carla-robotaxi")

image = (
    modal.Image.debian_slim()
    .apt_install(
    "wget", "software-properties-common",
    "xvfb", "libvulkan1", "libomp5",
    "libsdl2-2.0-0", "libsdl2-image-2.0-0",
    "libpng16-16", "libjpeg62-turbo",
    "libgles2-mesa", "vulkan-tools", "libvulkan-dev",
    "mesa-utils", "libgl1-mesa-dri",
    "libasound2", "pulseaudio", "libglu1-mesa"
)
    .run_commands(
        "wget -q https://tiny.carla.org/carla-0-9-15-linux -O /tmp/carla.tar.gz",
        "mkdir -p /opt/carla && tar -xzf /tmp/carla.tar.gz -C /opt/carla",
        "pip install carla==0.9.15",
        "useradd -m carlauser && chown -R carlauser:carlauser /opt/carla"
    )
)

@app.function(
    image=image,
    gpu="T4",
    timeout=3600
)
def run_carla_simulation():
    import subprocess
    import time
    import os
    import carla

    # Vérifier que CARLA est bien installé
    print(f"Contenu /opt/carla : {os.listdir('/opt/carla')}")

    # Lancer le serveur CARLA en tant que carlauser
    print("Démarrage serveur CARLA...")
    server = subprocess.Popen(
    ["su", "carlauser", "-c",
     "xvfb-run -a bash /opt/carla/CarlaUE4.sh -RenderOffScreen -carla-port=2000 -opengl"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

    # Attendre 90 secondes
    print("Attente 90s...")
    time.sleep(90)

    # Vérifier si le process tourne encore
    if server.poll() is not None:
        stdout, stderr = server.communicate()
        print(f"CARLA s'est arrete ! STDOUT: {stdout.decode()}")
        print(f"STDERR: {stderr.decode()}")
        return

    # Connexion client
    print("Connexion au serveur CARLA...")
    client = carla.Client("localhost", 2000)
    client.set_timeout(30.0)

    world = client.get_world()
    print(f"Monde charge : {world.get_map().name}")

    # Spawner un vehicule
    blueprint_library = world.get_blueprint_library()
    vehicle_bp = blueprint_library.filter("vehicle.tesla.model3")[0]
    spawn_point = world.get_map().get_spawn_points()[0]
    vehicle = world.spawn_actor(vehicle_bp, spawn_point)
    print(f"Vehicule spawne")

    # Simuler 30 secondes
    for i in range(30):
        vehicle.apply_control(carla.VehicleControl(throttle=0.5))
        time.sleep(1)
        velocity = vehicle.get_velocity()
        speed = (velocity.x**2 + velocity.y**2 + velocity.z**2)**0.5 * 3.6
        print(f"Vitesse : {speed:.1f} km/h")

    vehicle.destroy()
    server.terminate()
    print("Simulation terminee")

@app.local_entrypoint()
def main():
    run_carla_simulation.remote()