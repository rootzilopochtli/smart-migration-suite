#!/usr/bin/env python3
#
# smart_backup.py - Respaldo Modular v5.2 (FULL BACKUP INTEGRADO + EXCLUSIONES + INSTRUCCIONES)
# Autor: Alex Callejas
#

import os
import subprocess
import sys
import datetime
import shutil

SIZE_THRESHOLD = 5 * 1024 * 1024 * 1024
HOME = os.path.expanduser("~")
USER = os.environ.get("USER", "usuario")

def get_size(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

def format_size(size_in_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} PB"

def get_heavy_items(directory, threshold):
    print(f"\nAnalizando uso de disco en: {directory} ...")
    items = []
    try:
        with os.scandir(directory) as it:
            for entry in it:
                if not entry.name.startswith('.'):
                    size = get_size(entry.path)
                    if size >= threshold:
                        items.append((entry.path, size))
    except PermissionError:
        pass
    return sorted(items, key=lambda x: x[1], reverse=True)

def get_archive_dir(base_dest, prefix):
    meses = {1:"Ene", 2:"Feb", 3:"Mar", 4:"Abr", 5:"May", 6:"Jun",
             7:"Jul", 8:"Ago", 9:"Sept", 10:"Oct", 11:"Nov", 12:"Dic"}
    now = datetime.datetime.now()
    date_str = f"{now.day}{meses[now.month]}{now.year}"

    base_name = f"{prefix}_{date_str}"
    target_dir = os.path.join(base_dest, base_name)

    if not os.path.exists(target_dir):
        return target_dir

    counter = 1
    while True:
        target_dir = os.path.join(base_dest, f"{base_name}_{counter}")
        if not os.path.exists(target_dir):
            return target_dir
        counter += 1

def get_installed_software():
    print("\n============================================================")
    print("==> SELECCIÓN DE SOFTWARE PARA RESTAURACIÓN")
    print("============================================================")

    # Lista blanca declarativa de software por categorías
    software_catalog = {
        "dnf": {
            "Sistema y Escritorio": ["conky", "gnome-tweaks", "gnome-extensions-app", "virt-manager"],
            "Desarrollo y Terminal": ["git", "vim-enhanced", "terminator", "tilix", "htop", "btop", "zsh", "bat", "jq", "vale", "fastfetch", "direnv", "nodejs", "npm", "zoxide"],
            "Multimedia y Utilidades": ["gimp", "google-chrome-stable", "libheif-tools", "yt-dlp", "vlc-plugins-base"],
            "Contenedores y Nube": ["podman", "podman-compose", "buildah", "awscli2", "ansible"],
            "Python y ML": ["python3-pip", "python3-virtualenv", "ollama"],
            "Herramientas de Red": ["nmap", "net-tools", "tcpdump", "bind-utils"],
            "Corporativo Red Hat": ["redhat-internal-cert-install", "redhat-internal-NetworkManager-openvpn-profiles", "scaffolding"]
        },
        "flatpak": {
            "Comunicación": ["com.slack.Slack", "org.telegram.desktop", "im.riot.Riot"],
            "Productividad": ["md.obsidian.Obsidian", "com.spotify.Client"],
            "Desarrollo y Medios": ["com.vscodium.codium", "io.podman_desktop.PodmanDesktop", "com.obsproject.Studio", "org.videolan.VLC"]
        }
    }

    selected_dnf = [pkg for pkgs in software_catalog["dnf"].values() for pkg in pkgs]
    selected_flatpak = [app for apps in software_catalog["flatpak"].values() for app in apps]

    print("\nEl siguiente software está preseleccionado en tu catálogo base:")

    print("\n📦 PAQUETES DEL SISTEMA:")
    for category, pkgs in software_catalog["dnf"].items():
        print(f"  --- {category} ---")
        for pkg in pkgs:
            print(f"    - {pkg}")

    print("\n📦 APLICACIONES FLATPAK:")
    for category, apps in software_catalog["flatpak"].items():
        print(f"  --- {category} ---")
        for app in apps:
            print(f"    - {app}")

    while True:
        while True:
            excluir = input("\n¿Quieres EXCLUIR algún paquete/app de la lista predeterminada? (s/N): ").strip().lower()
            if excluir in ['s', 'n', '']:
                break
            print("⚠️ Opción no válida. Ingresa 's' para sí, o 'n' (o Enter) para no.")

        if excluir == 's':
            item_to_remove = input("Ingresa el nombre exacto a excluir (ej. vim-enhanced o com.spotify.Client): ").strip()
            removed = False
            if item_to_remove in selected_dnf:
                selected_dnf.remove(item_to_remove)
                removed = True
            if item_to_remove in selected_flatpak:
                selected_flatpak.remove(item_to_remove)
                removed = True

            if removed:
                print(f"✅ Excluido de la lista: {item_to_remove}")
            else:
                print(f"⚠️ '{item_to_remove}' no se encuentra en las listas.")
        else:
            break

    while True:
        while True:
            agregar = input("\n¿Quieres AGREGAR algún paquete/app extra manualmente? (s/N): ").strip().lower()
            if agregar in ['s', 'n', '']:
                break
            print("⚠️ Opción no válida.")

        if agregar == 's':
            extra = input("Ingresa el nombre exacto del paquete o app: ").strip()
            tipo = input("¿Es paquete de Sistema o Flatpak? (s/f): ").strip().lower()
            if tipo == 's':
                if extra not in selected_dnf:
                    selected_dnf.append(extra)
                    print(f"✅ Añadido a Sistema: {extra}")
                else:
                    print("⚠️ Ya está en la lista.")
            elif tipo == 'f':
                if extra not in selected_flatpak:
                    selected_flatpak.append(extra)
                    print(f"✅ Añadido a Flatpak: {extra}")
                else:
                    print("⚠️ Ya está en la lista de Flatpak.")
            else:
                print("⚠️ Tipo no válido. Usa 's' o 'f'.")
        else:
            break

    temp_dir_name = ".smart_backup_software"
    temp_dir_path = os.path.join(HOME, temp_dir_name)
    os.makedirs(temp_dir_path, exist_ok=True)

    with open(os.path.join(temp_dir_path, "dnf_packages.txt"), "w") as f:
        for p in selected_dnf:
            f.write(f"{p}\n")

    with open(os.path.join(temp_dir_path, "flatpak_apps.txt"), "w") as f:
        for p in selected_flatpak:
            f.write(f"{p}\n")

    print(f"\n✅ Perfil de software guardado: {len(selected_dnf)} paquetes y {len(selected_flatpak)} apps Flatpak listas para empaquetar.")
    return temp_dir_name

def backup_system(dest_path):
    software_dir = get_installed_software()

    print("\n============================================================")
    print("==> INICIANDO RESPALDO DE SISTEMA (DOTFILES + SOFTWARE)")
    print("============================================================")

    os.makedirs(dest_path, exist_ok=True)

    # --- NUEVO: Volcar configuración de GNOME antes de empaquetar ---
    print("\n--> Extrayendo configuraciones visuales de GNOME (dconf)...")
    gnome_settings_path = os.path.join(HOME, ".smart_gnome_settings.ini")
    subprocess.run(f"dconf dump / > {gnome_settings_path}", shell=True)

    now = datetime.datetime.now()
    tar_filename = f"perfil_{USER}_{now.strftime('%Y-%m-%d')}.tar.gz"
    tar_filepath = os.path.join(dest_path, tar_filename)

    sys_items = [
        ".bashrc", ".bash_profile", ".bash_history", ".zshrc",
        ".ssh", "bin", "uwufetch",
        ".gitconfig", ".git-credentials",
        ".vim", ".vimrc", ".viminfo",
        ".ansible", ".aws",
        ".ollama", ".claude", ".claude.json", ".gemini", ".continue",
        ".vale-styles", ".vale.ini",
        ".config", ".local", ".var/app", # <--- Aquí agregamos el directorio de Flatpak
        ".npm-global",
        ".harmattan-themes", ".harmattan-assets",
        ".smart_gnome_interface.ini",
        ".smart_gnome_shell.ini"
    ]

    to_pack = [item for item in sys_items if os.path.exists(os.path.join(HOME, item))]

    if not to_pack:
        print("❌ No se encontraron archivos/directorios de sistema para respaldar.")
        return

    print("\nCalculando el peso de cada elemento (esto tomará unos segundos)...")
    item_sizes = {item: get_size(os.path.join(HOME, item)) for item in to_pack}

    print("\nEstos son los elementos del sistema preseleccionados:")
    to_pack_sorted = sorted(to_pack, key=lambda x: item_sizes[x], reverse=True)

    for item in to_pack_sorted:
        print(f" [ {format_size(item_sizes[item])} ]\t- {item}")

    while True:
        while True:
            remove_more = input("\n¿Quieres EXCLUIR algún elemento de la lista? (s/N): ").strip().lower()
            if remove_more in ['s', 'n', '']:
                break
            print("⚠️ Opción no válida. Ingresa 's' para sí, o 'n' (o Enter) para no.")

        if remove_more == 's':
            item_to_remove = input("Ingresa el nombre a excluir (ej. .config): ").strip()
            if item_to_remove in to_pack:
                to_pack.remove(item_to_remove)
                print(f"✅ Excluido de la lista: {item_to_remove}")
            else:
                print("⚠️ Ese elemento no está en la lista actual.")
        else:
            break

    while True:
        while True:
            add_more = input("\n¿Quieres AGREGAR algún dotfile/directorio adicional? (s/N): ").strip().lower()
            if add_more in ['s', 'n', '']:
                break
            print("⚠️ Opción no válida. Ingresa 's' para sí, o 'n' (o Enter) para no.")

        if add_more == 's':
            extra_item = input("Ingresa el nombre (ej. .putty o .npmrc): ").strip()
            if os.path.exists(os.path.join(HOME, extra_item)):
                if extra_item not in to_pack:
                    to_pack.append(extra_item)
                    item_sizes[extra_item] = get_size(os.path.join(HOME, extra_item))
                    print(f"✅ Agregado: {extra_item} ({format_size(item_sizes[extra_item])})")
                else:
                    print("⚠️ Ese elemento ya está en la lista.")
            else:
                print("❌ El elemento no existe en tu $HOME.")
        else:
            break

    if not to_pack:
        print("❌ No seleccionaste ningún elemento. Cancelando.")
        return

    print("\nCalculando tamaño estimado del entorno...")
    total_sys_size = sum(item_sizes[item] for item in to_pack)

    free_space = shutil.disk_usage(os.path.dirname(dest_path)).free

    print("\nResumen final listo para comprimir.")
    print(f"📦 Tamaño estimado sin comprimir: {format_size(total_sys_size)}")
    print(f"💾 Espacio disponible en el disco externo: {format_size(free_space)}")

    if total_sys_size > free_space:
        print(f"\n❌ ERROR CRÍTICO: No hay suficiente espacio en el destino para este entorno.")
        print("   Abortando operación por seguridad.")
        return

    while True:
        confirm = input("¿Proceder con la creación del archivo .tar.gz? (s/N): ").strip().lower()
        if confirm in ['s', 'n', '']:
            break
        print("⚠️ Opción no válida. Ingresa 's' o 'n'.")

    if confirm == 's':
        print(f"\n--> Ejecutando tar (esto tomará un momento dependiendo del tamaño)...")
        # Excluir la caché y las imágenes de contenedores para evitar problemas de simlinks y tamaño masivo
        # --- NUEVO: Exclusión del llavero (keyrings) agregada al tar ---
        cmd = ["tar", "--exclude=.local/share/containers", "--exclude=.cache", "--exclude=.local/share/keyrings", "-czf", tar_filepath] + to_pack
        subprocess.run(cmd, cwd=HOME, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        size_mb = os.path.getsize(tar_filepath) / (1024 * 1024)
        print(f"✅ Respaldo de sistema y software completado en: {dest_path}")
        print(f"   Archivo: {tar_filename} ({size_mb:.1f} MB)")

        src_software = os.path.join(HOME, software_dir)
        dst_software = os.path.join(dest_path, software_dir)
        if os.path.exists(dst_software):
            shutil.rmtree(dst_software)
        shutil.copytree(src_software, dst_software)
        print("✅ Listas de software guardadas junto al respaldo.")
    else:
        print("Operación de sistema cancelada.")

    temp_dir_path = os.path.join(HOME, software_dir)
    if os.path.exists(temp_dir_path):
        shutil.rmtree(temp_dir_path)

def backup_personal(dest_path, rsync_flags):
    print("\n============================================================")
    print("==> INICIANDO RESPALDO PERSONAL (LIBERACIÓN DE ESPACIO)")
    print("============================================================")

    heavy_items = get_heavy_items(HOME, SIZE_THRESHOLD)

    if not heavy_items:
        print(f"No se encontraron elementos pesados (> {format_size(SIZE_THRESHOLD)}).")
        return

    to_sync = []

    print("\nEstos son los directorios con más espacio utilizado:\n")
    for path, size in heavy_items:
        print(f"{format_size(size)}\t{os.path.basename(path)}")
    print("\nA continuación, indícame cómo proceder con cada uno de ellos.")

    for path, size in heavy_items:
        name = os.path.basename(path)
        print(f"\n[ {format_size(size)} ] -> {name}")

        if os.path.isdir(path):
            while True:
                action = input("¿Qué deseas hacer? [R]espaldar completo, [D]epurar internamente, [I]gnorar: ").strip().lower()
                if action in ['r', 'd', 'i']:
                    break
                print("⚠️ Opción no válida. Ingresa 'r', 'd' o 'i'.")

            if action == 'r':
                to_sync.append(path)
            elif action == 'd':
                sub_threshold = 500 * 1024 * 1024
                sub_items = get_heavy_items(path, sub_threshold)
                if not sub_items:
                    print("No se encontraron elementos pesados (>500MB) dentro de este directorio.")
                    continue

                print(f"\nContenido de {name}:")
                for sub_path, sub_size in sub_items:
                    sub_name = os.path.basename(sub_path)
                    while True:
                        sub_action = input(f"  - {sub_name} ({format_size(sub_size)}) -> ¿[R]espaldar o [I]gnorar?: ").strip().lower()
                        if sub_action in ['r', 'i']:
                            break
                        print("⚠️ Opción no válida. Ingresa 'r' o 'i'.")
                    if sub_action == 'r':
                        to_sync.append(sub_path)
        else:
            while True:
                action = input("¿Qué deseas hacer? [R]espaldar, [I]gnorar: ").strip().lower()
                if action in ['r', 'i']:
                    break
                print("⚠️ Opción no válida. Ingresa 'r' o 'i'.")
            if action == 'r':
                to_sync.append(path)

    while True:
        while True:
            add_more = input("\n¿Quieres agregar algún archivo/directorio adicional a los seleccionados? (s/N): ").strip().lower()
            if add_more in ['s', 'n', '']:
                break
            print("⚠️ Opción no válida. Ingresa 's' o 'n'.")

        if add_more == 's':
            extra_path = input("Ingresa el path (ej. Books o Documents/proyectos): ").strip()
            full_path = os.path.abspath(os.path.join(HOME, extra_path))
            if os.path.exists(full_path):
                if full_path not in to_sync:
                    to_sync.append(full_path)
                    print(f"✅ Agregado: {full_path}")
                else:
                    print("⚠️ Ese elemento ya está en la lista.")
            else:
                print("❌ El path no existe. Verifica y vuelve a intentar.")
        else:
            break

    if not to_sync:
        print("\nNo seleccionaste ningún elemento para respaldar. Saltando modo personal.")
        return

    print("\nResumen final de elementos a mover:")
    total_freed_bytes = 0
    for item in to_sync:
        print(f" - {item}")
        total_freed_bytes += get_size(item)

    free_space = shutil.disk_usage(os.path.dirname(dest_path) if os.path.exists(os.path.dirname(dest_path)) else dest_path).free

    print(f"\n🔥 Este respaldo moverá los archivos y liberará {format_size(total_freed_bytes)} de espacio.")
    print(f"💾 Espacio disponible en el disco externo: {format_size(free_space)}")

    if total_freed_bytes > free_space:
        print(f"\n❌ ERROR CRÍTICO: No hay suficiente espacio en el destino.")
        print("   Abortando operación por seguridad.")
        return

    while True:
        confirm = input("\n¿Proceder con el movimiento al disco externo de forma definitiva? (s/N): ").strip().lower()
        if confirm in ['s', 'n', '']:
            break
        print("⚠️ Opción no válida. Ingresa 's' o 'n'.")

    if confirm == 's':
        os.makedirs(dest_path, exist_ok=True)
        log_file_path = os.path.join(dest_path, "backup_registro.log")
        list_file = "/tmp/rsync_items.list"

        with open(list_file, 'w') as f:
            for item in to_sync:
                rel_path = os.path.relpath(item, HOME)
                f.write(f"{rel_path}\n")

        print(f"\n--> Ejecutando rsync silenciosamente...")
        print(f"--> El detalle de la operación se guardará en: {log_file_path}")

        cmd = [
            "rsync",
            rsync_flags,
            f"--log-file={log_file_path}",
            f"--files-from={list_file}",
            "--remove-source-files",
            f"{HOME}/",
            f"{dest_path}/"
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        os.remove(list_file)

        print("--> Limpiando directorios vacíos remanentes...")
        for item in to_sync:
            if os.path.isdir(item) and os.path.exists(item):
                subprocess.run(f"find '{item}' -mindepth 1 -type d -empty -delete 2>/dev/null", shell=True)

        print("\n✅ Respaldo personal completado con éxito. ¡Espacio liberado!")
    else:
        print("Operación cancelada.")

def print_restore_instructions():
    print("\n============================================================")
    print("📝 INSTRUCCIONES PARA LA RESTAURACIÓN EN UN EQUIPO NUEVO")
    print("============================================================")
    print("Si vas a restaurar este respaldo en un equipo nuevo, recuerda:")
    print("  1. Tu nuevo equipo debe tener montada la USB/Disco donde guardaste este respaldo.")
    print("  2. Necesitarás tener privilegios de 'sudo' activos en el nuevo equipo.")
    print("  3. Si vas a restaurar remotamente, recuerda abrir el puerto SSH en el firewall de tu destino:")
    print("     $ sudo firewall-cmd --add-service=ssh --permanent && sudo firewall-cmd --reload")
    print("  4. Transfiere de forma segura (scp) el script 'smart_restore.py' al $HOME de tu nueva máquina.")
    print("  5. Ejecuta: 'python3 smart_restore.py' y sigue el asistente.")
    print("============================================================\n")

def backup_desktop(dest_path):
    print("\n============================================================")
    print("==> INICIANDO RESPALDO EXCLUSIVO DE ESCRITORIO (GNOME)")
    print("============================================================")

    os.makedirs(dest_path, exist_ok=True)

    print("\n--> Extrayendo configuraciones visuales de GNOME (dconf)...")
    gnome_settings_path = os.path.join(HOME, ".smart_gnome_settings.ini")
    subprocess.run(f"dconf dump / > {gnome_settings_path}", shell=True)

    now = datetime.datetime.now()
    tar_filename = f"escritorio_{USER}_{now.strftime('%Y-%m-%d')}.tar.gz"
    tar_filepath = os.path.join(dest_path, tar_filename)

    sys_items = [
        ".smart_gnome_shell.ini",
        ".smart_gnome_interface.ini",
        "Pictures/Wallpapers",
        "Pictures/ProfilePic"
        ".local/share/gnome-shell/extensions" # <--- EL INGREDIENTE SECRETO
    ]

    to_pack = [item for item in sys_items if os.path.exists(os.path.join(HOME, item))]

    if not to_pack:
        print("❌ No se encontraron configuraciones ni imágenes de escritorio.")
        return

    print(f"\n--> Ejecutando tar (empaquetando entorno visual)...")
    cmd = ["tar", "-czf", tar_filepath] + to_pack
    subprocess.run(cmd, cwd=HOME, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    size_mb = os.path.getsize(tar_filepath) / (1024 * 1024)
    print(f"✅ Respaldo de escritorio completado en: {dest_path}")
    print(f"   Archivo: {tar_filename} ({size_mb:.2f} MB)")

def main():
    print("==> Iniciando Smart Backup v5.2 (PRODUCCIÓN FINAL)")

    dest_dir = input("\nIntroduce la ruta del disco externo (ej. /run/media/TU_USUARIO/TU_DISCO): ").strip()
    if not os.path.isdir(dest_dir):
        print(f"❌ Error: La ruta '{dest_dir}' no existe o no está montada.")
        sys.exit(1)

    try:
        fs_type = subprocess.check_output(f"df -T '{dest_dir}' | awk 'NR==2 {{print $2}}'", shell=True, text=True).strip()
    except Exception:
        fs_type = "unknown"

    rsync_flags = "-avh"
    if fs_type in ["exfat", "vfat", "fuseblk", "ntfs"]:
        print(f"ℹ️  Sistema de archivos '{fs_type}' detectado. Usando banderas de compatibilidad.")
        rsync_flags = "-rtvh"
    else:
        print(f"ℹ️  Sistema de archivos '{fs_type}' nativo detectado. Manteniendo permisos completos.")

    print("\n¿Qué tipo de respaldo deseas realizar hoy?")
    print("  1) [P]ersonal (Busca, mueve y limpia archivos pesados)")
    print("  2) [S]istema  (Empaqueta tus dotfiles esenciales en un .tar.gz)")
    print("  3) [C]ompleto (Ejecuta Personal primero, y luego Sistema)")
    print("  4) [E]scritorio (Solo personalización visual: fondos, temas, extensiones)")

    while True:
        mode = input("Opción [P/S/C/E]: ").strip().lower()
        if mode in ['p', 's', 'c', 'e']:
            break
        print("⚠️ Opción no válida. Ingresa 'p', 's', 'c' o 'e'.")

    if mode == 'c':
        full_backup_dir = get_archive_dir(dest_dir, "FullBackup")
        os.makedirs(full_backup_dir, exist_ok=True)
        backup_personal(os.path.join(full_backup_dir, "PersonalArchive"), rsync_flags)
        backup_system(os.path.join(full_backup_dir, "SystemBackup"))
    elif mode == 'p':
        personal_dir = get_archive_dir(dest_dir, "PersonalArchive")
        backup_personal(personal_dir, rsync_flags)
    elif mode == 's':
        system_dir = get_archive_dir(dest_dir, "SystemBackup")
        backup_system(system_dir)
    elif mode == 'e':
        desktop_dir = get_archive_dir(dest_dir, "DesktopBackup")
        backup_desktop(desktop_dir)

    print("\n🎉 Todas las operaciones solicitadas han finalizado. Puedes revisar tu disco externo.")
    print_restore_instructions()

if __name__ == "__main__":
    main()

