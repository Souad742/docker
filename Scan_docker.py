import subprocess
import os

# VM source du scan
REMOTE_HOST = "192.168.100.137"
REMOTE_PORT = "64295"
REMOTE_USER = "ubuntu"
REMOTE_PASS = "ubuntu"
REMOTE_TRIVY_DIR = "/tmp/trivy_results"

# VM cible pour recevoir les résultats
DEST_HOST = "192.168.100.144"
DEST_USER = "ubuntu"
DEST_PASS = "ubuntu"
DEST_DIR = "/home/ubuntu/trivy_results"

def run_remote_scan():
    """Exécute le scan Trivy sur les images des conteneurs en cours sur la VM distante."""
    scan_command = (
        f"mkdir -p {REMOTE_TRIVY_DIR}; "
        "docker ps --format '{{.Image}} {{.ID}}' | "
        "while read line; do "
        "image=$(echo $line | awk '{print $1}'); "
        "id=$(echo $line | awk '{print $2}'); "
        f"trivy image $image > {REMOTE_TRIVY_DIR}/$(echo $image | tr '/:' '__')_${{id}}.txt; "
        "done"
    )

    ssh_cmd = [
        "sshpass", "-p", REMOTE_PASS,
        "ssh", "-p", REMOTE_PORT,
        f"{REMOTE_USER}@{REMOTE_HOST}",
        scan_command
    ]

    print("🔍 Lancement du scan Trivy sur la machine distante...")
    subprocess.run(ssh_cmd)

def check_remote_files_exist():
    """Vérifie si des fichiers de scan existent sur la machine distante."""
    check_cmd = [
        "sshpass", "-p", REMOTE_PASS,
        "ssh", "-p", REMOTE_PORT,
        f"{REMOTE_USER}@{REMOTE_HOST}",
        f"ls {REMOTE_TRIVY_DIR}/*.txt 2>/dev/null | wc -l"
    ]
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    try:
        count = int(result.stdout.strip())
        return count > 0
    except ValueError:
        return False

def send_results_to_target():
    """Envoie les fichiers de résultats Trivy vers une autre machine distante."""
    print("📤 Envoi des résultats Trivy vers la machine cible...")

    # Création du dossier cible si nécessaire
    mkdir_cmd = [
        "sshpass", "-p", DEST_PASS,
        "ssh",
        f"{DEST_USER}@{DEST_HOST}",
        f"mkdir -p {DEST_DIR}"
    ]
    subprocess.run(mkdir_cmd)

    # Transfert des fichiers
    scp_cmd = [
        "sshpass", "-p", REMOTE_PASS,
        "scp",
        f"{REMOTE_USER}@{REMOTE_HOST}:{REMOTE_TRIVY_DIR}/*.txt",
        f"{DEST_USER}@{DEST_HOST}:{DEST_DIR}/"
    ]
    subprocess.run(scp_cmd)

    print(f"✅ Résultats transférés vers {DEST_HOST}:{DEST_DIR}")

def main():
    run_remote_scan()
    if check_remote_files_exist():
        send_results_to_target()
    else:
        print("⚠️ Aucun fichier de scan Trivy trouvé sur la machine distante. Vérifie que des conteneurs sont actifs.")

if __name__ == "__main__":
    main()

