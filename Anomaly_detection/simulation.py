import pygame
import requests
import random
import time

# --- Config ---
WIDTH, HEIGHT = 900, 600
FPS = 30
URL = "http://127.0.0.1:8001/check_command"

# --- Couleurs ---
BLACK   = (0, 0, 0)
WHITE   = (255, 255, 255)
GRAY    = (50, 50, 50)
GREEN   = (0, 200, 0)
YELLOW  = (255, 200, 0)
RED     = (220, 0, 0)
BLUE    = (0, 120, 255)
ORANGE  = (255, 140, 0)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Robotaxi Teleoperation — Anomaly Detection")
clock = pygame.time.Clock()
font = pygame.font.SysFont("monospace", 16)
font_big = pygame.font.SysFont("monospace", 22, bold=True)

# --- État du véhicule ---
vehicle = {
    "x": 100,
    "y": HEIGHT // 2,
    "speed": 50.0,
    "steering": 0.0,
    "accel": 0.3,
    "freq": 3.0,
    "reaction": 400.0
}

obstacles = [
    {"x": random.randint(400, 800), "y": HEIGHT // 2, "radius": 20}
    for _ in range(3)
]

decision = "ACCEPT"
reason = "Commande normale"
source = "ml"
attack_mode = False
frame = 0

def get_obstacle_dist(vx, vy):
    min_dist = 9999
    for obs in obstacles:
        dist = ((obs["x"] - vx)**2 + (obs["y"] - vy)**2)**0.5
        if dist < min_dist:
            min_dist = dist
    return round(min_dist / 10, 1)  # converti en "mètres"

def check_command(v):
    try:
        payload = {
            "speed_kmh": v["speed"],
            "commanded_accel": v["accel"],
            "steering_angle": v["steering"],
            "obstacle_dist_m": get_obstacle_dist(v["x"], v["y"]),
            "cmd_freq_per_sec": v["freq"],
            "operator_reaction_ms": v["reaction"]
        }
        r = requests.post(URL, json=payload, timeout=0.2)
        result = r.json()
        return result["decision"], result["reason"], result["source"]
    except:
        return "ACCEPT", "API indisponible", "none"

def draw_road():
    screen.fill(GRAY)
    # Route
    pygame.draw.rect(screen, (80, 80, 80), (0, HEIGHT//2 - 60, WIDTH, 120))
    # Lignes de route
    for x in range(0, WIDTH, 60):
        pygame.draw.rect(screen, WHITE, (x, HEIGHT//2 - 3, 40, 6))

def draw_vehicle(v, color):
    pygame.draw.rect(screen, color, (v["x"] - 25, v["y"] - 15, 50, 30), border_radius=6)
    pygame.draw.rect(screen, WHITE, (v["x"] + 10, v["y"] - 10, 15, 20), border_radius=3)

def draw_obstacles():
    for obs in obstacles:
        pygame.draw.circle(screen, ORANGE, (obs["x"], obs["y"]), obs["radius"])
        pygame.draw.circle(screen, RED, (obs["x"], obs["y"]), obs["radius"], 3)

def draw_hud(v, dec, rea, src, attack):
    # Fond HUD
    pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, 80))
    pygame.draw.rect(screen, BLACK, (0, HEIGHT - 100, WIDTH, 100))

    # Décision
    color = GREEN if dec == "ACCEPT" else (YELLOW if dec == "LIMIT" else RED)
    text = font_big.render(f"DECISION: {dec}  ({src})", True, color)
    screen.blit(text, (20, 10))

    reason_text = font.render(f"Raison: {rea}", True, WHITE)
    screen.blit(reason_text, (20, 40))

    # Stats véhicule
    stats = [
        f"Vitesse: {v['speed']:.0f} km/h",
        f"Accel: {v['accel']:.1f}",
        f"Steering: {v['steering']:.0f}°",
        f"Obstacle: {get_obstacle_dist(v['x'], v['y'])}m",
        f"Freq: {v['freq']:.0f} cmd/s",
    ]
    for i, s in enumerate(stats):
        t = font.render(s, True, WHITE)
        screen.blit(t, (20 + i * 170, HEIGHT - 80))

    # Mode attaque
    if attack:
        atk = font_big.render("⚠ MODE ATTAQUE ACTIF", True, RED)
        screen.blit(atk, (WIDTH - 320, 10))

    # Contrôles
    controls = font.render("N=Normal  A=Attaque  D=DoS  F=Freinage urgence  R=Reset  ESC=Quitter", True, (150,150,150))
    screen.blit(controls, (20, HEIGHT - 25))

running = True
while running:
    clock.tick(FPS)
    frame += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_n:  # Mode normal
                vehicle["speed"] = 50.0
                vehicle["accel"] = 0.3
                vehicle["steering"] = 0.0
                vehicle["freq"] = 3.0
                vehicle["reaction"] = 400.0
                attack_mode = False
            elif event.key == pygame.K_a:  # Attaque : accélération forcée
                vehicle["accel"] = 2.0
                vehicle["speed"] = 60.0
                attack_mode = True
            elif event.key == pygame.K_d:  # Attaque : DoS flood
                vehicle["freq"] = 35.0
                vehicle["reaction"] = 15.0
                attack_mode = True
            elif event.key == pygame.K_f:  # Freinage d'urgence
                vehicle["accel"] = -2.0
                vehicle["speed"] = 100.0
                attack_mode = False
            elif event.key == pygame.K_r:  # Reset complet
                vehicle["x"] = 100
                vehicle["y"] = HEIGHT // 2
                vehicle["speed"] = 50.0
                vehicle["accel"] = 0.3
                vehicle["steering"] = 0.0
                vehicle["freq"] = 3.0
                vehicle["reaction"] = 400.0
                attack_mode = False
                decision = "ACCEPT"
                reason = "Commande normale"
                for obs in obstacles:
                    obs["x"] = random.randint(400, 800)

    # Déplacer le véhicule
    if decision == "DISENGAGE":
        vehicle["speed"] = max(0, vehicle["speed"] - 2)
    elif decision == "LIMIT":
        vehicle["speed"] = min(vehicle["speed"], 30)
    else:
        vehicle["x"] += int(vehicle["speed"] / 20)

    # Reset position si hors écran
    if vehicle["x"] > WIDTH + 50:
        vehicle["x"] = 50
        for obs in obstacles:
            obs["x"] = random.randint(400, 800)

    # Appel API toutes les 30 frames
    if frame % 30 == 0:
        decision, reason, source = check_command(vehicle)

    # Dessin
    draw_road()
    draw_obstacles()

    # Couleur véhicule selon décision
    vcolor = GREEN if decision == "ACCEPT" else (YELLOW if decision == "LIMIT" else RED)
    draw_vehicle(vehicle, vcolor)
    draw_hud(vehicle, decision, reason, source, attack_mode)

    pygame.display.flip()

pygame.quit()