#!/usr/bin/env python3
#
# smart_restore.py - Restauración Modular v1.1
# Autor: Alex Callejas
#

import os
import subprocess
import sys
import shutil
import socket

HOME = os.path.expanduser("~")
RESTORE_LOG = ["============================================================",
               "       RESUMEN DE RESTAURACIÓN - SMART RESTORE",
               "============================================================"]

def log_append(section, details):
    RESTORE_LOG.append(f"\n--- {section} ---")
    RESTORE_LOG.append(details)

def save_log():
    log_path = os.path.join(HOME, ".smart_restore_summary.log")
    with open(log_path, "w") as f:
        f.write("\n".join(RESTORE_LOG) + "\n")
    return log_path

def cache_sudo(dry_run=False):
    if dry_run:
        print("\n[DRY-RUN] Se ejecutaría: sudo -v (para cachear credenciales)")
        return

    print("==> Solicitando privilegios de administrador (sudo) para la restauración...")
    try:
        subprocess.run(["sudo", "-v"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Error: No se pudo obtener acceso a sudo. Saliendo.")
        sys.exit(1)

def configure_hostname(dry_run=False):
    current_hostname = socket.gethostname()
    print("\n============================================================")
    print("==> CONFIGURACIÓN DE IDENTIDAD")
    print("============================================================")

    while True:
        ans = input(f"El hostname actual del sistema es '{current_hostname}', ¿deseas cambiarlo? (s/N): ").strip().lower()
        if ans in ['s', 'n', '']:
            break
        print("⚠️ Opción no válida.")

    if ans == 's':
        new_host = input("¿Qué hostname quieres configurar al sistema?: ").strip()
        if new_host:
            if dry_run:
                print(f"[DRY-RUN] Se ejecutaría: sudo hostnamectl set-hostname {new_host}")
            else:
                print(f" -> Configurando nuevo hostname: {new_host}")
                subprocess.run(["sudo", "hostnamectl", "set-hostname", new_host], check=True)
                print("✅ Hostname actualizado.")
                log_append("Identidad", f"Hostname modificado de {current_hostname} a {new_host}")
        else:
            print(" -> Hostname en blanco, omitiendo.")

def configure_timezone(dry_run=False):
    print("\n============================================================")
    print("==> CONFIGURACIÓN DE ZONA HORARIA")
    print("============================================================")

    try:
        current_tz = subprocess.check_output(["timedatectl", "show", "-p", "Timezone", "--value"], text=True).strip()
    except Exception:
        current_tz = "Desconocida"

    print(f"La zona horaria actual es: {current_tz}")

    while True:
        ans = input("¿Deseas configurarla a 'America/Mexico_City'? (s/N): ").strip().lower()
        if ans in ['s', 'n', '']:
            break
        print("⚠️ Opción no válida.")

    if ans == 's':
        if dry_run:
            print("[DRY-RUN] Se ejecutaría: sudo timedatectl set-timezone America/Mexico_City")
        else:
            try:
                subprocess.run(["sudo", "timedatectl", "set-timezone", "America/Mexico_City"], check=True)
                print("✅ Zona horaria actualizada a America/Mexico_City.")
                log_append("Zona Horaria", "Actualizada a America/Mexico_City")
            except subprocess.CalledProcessError:
                print("❌ Error al intentar cambiar la zona horaria.")

def select_backup_file():
    print("\n============================================================")
    print("==> BÚSQUEDA DE RESPALDOS")
    print("============================================================")

    while True:
        base_path = input("Introduce la ruta de tu USB/Disco de respaldo (ej. /run/media/usuario/USB):\n> ").strip()

        if not os.path.exists(base_path):
            print(f"❌ La ruta '{base_path}' no existe. Intenta de nuevo.")
            continue

        print(" -> Escaneando en busca de respaldos de sistema...")
        backups = []

        for root, dirs, files in os.walk(base_path):
            for file in files:
                if (file.startswith("perfil_") or file.startswith("escritorio_")) and file.endswith(".tar.gz"):
                    backups.append(os.path.join(root, file))

        if not backups:
            print("⚠️ No se encontraron respaldos de sistema (perfil_*.tar.gz) en esa ruta.")
            manual = input("¿Deseas introducir la ruta exacta manualmente? (s/N): ").strip().lower()
            if manual == 's':
                exact_path = input("Ruta exacta al archivo .tar.gz:\n> ").strip()
                if os.path.exists(exact_path):
                    return exact_path
                else:
                    print("❌ El archivo no existe.")
            continue

        print("\nRespaldos encontrados:")
        backups.sort(key=os.path.getmtime)

        for i, bkp in enumerate(backups, 1):
            size_mb = os.path.getsize(bkp) / (1024 * 1024)
            rel_path = os.path.relpath(bkp, base_path)
            print(f"  [{i}] {rel_path} ({size_mb:.1f} MB)")

        while True:
            sel = input(f"\nSelecciona el respaldo a restaurar (1-{len(backups)}) o '0' para otra ruta: ").strip()
            if sel == '0':
                break
            try:
                idx = int(sel) - 1
                if 0 <= idx < len(backups):
                    return backups[idx]
                else:
                    print("⚠️ Número fuera de rango.")
            except ValueError:
                print("⚠️ Ingresa un número válido.")

        if sel == '0':
            continue

def prepare_environment(tar_path, dry_run=False):
    print("\n============================================================")
    print("==> VALIDANDO ESPACIO Y CREANDO DIRECTORIOS")
    print("============================================================")

    tar_size = os.path.getsize(tar_path)
    estimated_needed = tar_size * 2.5
    free_space = shutil.disk_usage(HOME).free

    print(f"📦 Tamaño del archivo comprimido: {tar_size / (1024*1024):.1f} MB")
    print(f"💾 Espacio libre en {HOME}: {free_space / (1024*1024*1024):.1f} GB")

    if free_space < estimated_needed:
        print("❌ ERROR CRÍTICO: Es probable que no tengas espacio suficiente para descomprimir.")
        log_append("Entorno", f"Fallo por espacio insuficiente. Requerido ~{estimated_needed/(1024**3):.1f}GB. Disponible {free_space/(1024**3):.1f}GB.")
        return False
    print("✅ Espacio suficiente validado.")

    print("\n -> Creando estructura base de directorios...")
    directorios = ["Devel", "Documents/Work", "Documents/Personal"]

    for d in directorios:
        dir_path = os.path.join(HOME, d)
        if dry_run:
            print(f"[DRY-RUN] Se crearía el directorio: {dir_path}")
        else:
            os.makedirs(dir_path, exist_ok=True)
            print(f"  - Creado: ~/{d}")

    log_append("Entorno", f"Validación de espacio exitosa. Archivo fuente: {tar_path}")
    return True

def get_pkg_manager():
    """Detecta el gestor de paquetes base según la distribución de Linux."""
    pm_cmd = ["sudo", "dnf", "install", "-y", "--skip-unavailable"]
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            os_info = f.read().lower()
            if "ubuntu" in os_info or "debian" in os_info:
                pm_cmd = ["sudo", "apt-get", "install", "-y"]
            elif "arch" in os_info or "manjaro" in os_info:
                pm_cmd = ["sudo", "pacman", "-S", "--noconfirm", "--needed"]
    return pm_cmd

def install_software(tar_path, dry_run=False):
    print("\n============================================================")
    print("==> INSTALACIÓN DE SOFTWARE (APROVISIONAMIENTO)")
    print("============================================================")

    backup_dir = os.path.dirname(tar_path)
    software_dir = os.path.join(backup_dir, ".smart_backup_software")

    sys_pkg_file = os.path.join(software_dir, "dnf_packages.txt")
    flatpak_file = os.path.join(software_dir, "flatpak_apps.txt")

    missing_pkgs = [] # <--- Acumulador global de paquetes perdidos

    if not os.path.exists(software_dir):
        print("⚠️ No se encontraron listas de software junto al respaldo. Saltando instalación.")
        log_append("Software", "No se encontraron listas de instalación en el respaldo.")
        return True, missing_pkgs

    # 1. Paquetes del Sistema
    if os.path.exists(sys_pkg_file):
        with open(sys_pkg_file, 'r') as f:
            sys_pkgs = [line.strip() for line in f if line.strip()]

        if sys_pkgs:
            print(f"\n -> Instalando {len(sys_pkgs)} paquetes del sistema...")
            base_cmd = get_pkg_manager()
            cmd_pkg = base_cmd + (sys_pkgs if not dry_run else ["<paquetes_sistema>"])

            if dry_run:
                print(f"[DRY-RUN] Ejecutaría: {' '.join(cmd_pkg)}")
            else:
                try:
                    result = subprocess.run(cmd_pkg, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
                    output = result.stdout

                    for line in output.split('\n'):
                        if "No match for argument:" in line or "Unable to locate package" in line:
                            missing_pkgs.append(line.split(':')[-1].strip() if ":" in line else line.split()[-1].strip())

                    if result.returncode == 0 and not missing_pkgs:
                        print("✅ Paquetes del sistema instalados correctamente.")
                        log_append("Software (Sistema)", f"Instalación exitosa.\nPaquetes: {', '.join(sys_pkgs)}")
                    else:
                        print("⚠️ La instalación terminó, pero algunos paquetes no se encontraron. Revisa el log.")
                        log_append("Software (Sistema)", f"Instalación finalizada con paquetes faltantes.\n\nPaquetes solicitados: {', '.join(sys_pkgs)}\n\nPaquetes NO encontrados:\n{chr(10).join([' - ' + p for p in missing_pkgs])}\n\nDetalle de ejecución de DNF:\n{output.strip()}")

                except Exception as e:
                    print("❌ Error crítico durante la instalación de paquetes del sistema.")
                    log_append("Software (Sistema)", f"Error de ejecución: {str(e)}")

    # 2. Flatpak
    if os.path.exists(flatpak_file):
        with open(flatpak_file, 'r') as f:
            flatpak_apps = [line.strip() for line in f if line.strip()]

        if flatpak_apps:
            print(f"\n -> Instalando {len(flatpak_apps)} aplicaciones Flatpak...")
            cmd_flatpak = ["flatpak", "install", "--user", "-y", "flathub"] + (flatpak_apps if not dry_run else ["<apps_flatpak>"])

            if dry_run:
                print("[DRY-RUN] Ejecutaría: flatpak remote-add --user --if-not-exists flathub ...")
                print(f"[DRY-RUN] Ejecutaría: {' '.join(cmd_flatpak)}")
            else:
                try:
                    subprocess.run(["flatpak", "remote-add", "--user", "--if-not-exists", "flathub", "https://flathub.org/repo/flathub.flatpakrepo"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    result_flatpak = subprocess.run(cmd_flatpak, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)

                    if result_flatpak.returncode == 0:
                        print("✅ Aplicaciones Flatpak instaladas correctamente.")
                        log_append("Software (Flatpak)", f"Instalación exitosa.\nAplicaciones: {', '.join(flatpak_apps)}")
                    else:
                        print("⚠️ Algunas aplicaciones Flatpak fallaron al instalarse. Revisa el log.")
                        log_append("Software (Flatpak)", f"Errores en la instalación.\nAplicaciones solicitadas: {', '.join(flatpak_apps)}\n\nDetalle de ejecución de Flatpak:\n{result_flatpak.stdout.strip()}")
                except Exception as e:
                    print("❌ Error crítico durante la instalación de Flatpak.")
                    log_append("Software (Flatpak)", f"Error de ejecución: {str(e)}")

    # Retornamos el estado y la lista de faltantes de forma unificada
    return True, missing_pkgs

def extract_backup(tar_path, dry_run=False):
    print("\n============================================================")
    print("==> RESTAURACIÓN DEL PERFIL Y DOTFILES")
    print("============================================================")

    # Quitamos --unlink-first para no romper directorios con contenido
    cmd = ["tar", "--overwrite", "-xzf", tar_path, "-C", HOME]

    if dry_run:
        print(f"[DRY-RUN] Se ejecutaría el comando: {' '.join(cmd)}")
        return True

    print(f" -> Extrayendo {os.path.basename(tar_path)} en {HOME}...")
    print("    (Esto tomará unos minutos dependiendo del tamaño)")

    result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)

    if result.returncode == 0:
        print("✅ Perfil y dotfiles restaurados con éxito.")
        log_append("Descompresión (tar)", "Éxito al extraer sin errores.")
        return True
    else:
        # Volvemos el error no-fatal para permitir que el script termine
        print("⚠️ Hubo advertencias al descomprimir (conflictos de permisos en archivos preexistentes).")
        print("   La mayoría de los archivos se restauraron. Continuando...")
        log_append("Descompresión (tar)", f"Finalizó con advertencias (Código {result.returncode}).\nEsto es común al sobreescribir llaves SSH o repositorios Git.\nSalida de error:\n{result.stderr}")
        return True # <-- Forzamos el True para que continúe hacia la configuración

def restore_personal_archive(tar_path, dry_run=False):
    print("\n============================================================")
    print("==> RESTAURANDO ARCHIVO PERSONAL")
    print("============================================================")

    system_backup_dir = os.path.dirname(tar_path)
    full_backup_dir = os.path.dirname(system_backup_dir)
    personal_dir = os.path.join(full_backup_dir, "PersonalArchive")

    if os.path.exists(personal_dir):
        print(f" -> Directorio PersonalArchive detectado en: {personal_dir}")
        cmd = ["rsync", "-avh", f"{personal_dir}/", f"{HOME}/", "--exclude=backup_registro.log"]

        if dry_run:
            print(f"[DRY-RUN] Se ejecutaría: {' '.join(cmd)}")
        else:
            print(" -> Restaurando archivos personales (esto tomará un momento dependiendo del tamaño)...")
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            print("✅ Archivos personales restaurados con éxito.")
            log_append("Archivo Personal", f"Copiado desde {personal_dir}")
    else:
        print(" -> No se detectó un 'PersonalArchive' asociado a este respaldo. Omitiendo.")
        log_append("Archivo Personal", "No se detectó directorio asociado. Omitido.")

    return True

def configure_desktop(dry_run=False):
    print("\n============================================================")
    print("==> PERSONALIZACIÓN DE ESCRITORIO (GNOME)")
    print("============================================================")

    # --- NUEVO: Carga quirúrgica de configuraciones permitidas ---
    dconf_paths = [
        (".smart_gnome_shell.ini", "/org/gnome/shell/"),
        (".smart_gnome_interface.ini", "/org/gnome/desktop/interface/")
    ]

    print("\n -> Restaurando configuraciones visuales de GNOME (dconf)...")
    for ini_file, dconf_path in dconf_paths:
        ini_path = os.path.join(HOME, ini_file)
        if os.path.exists(ini_path):
            if dry_run:
                print(f"[DRY-RUN] Ejecutaría: dconf load {dconf_path} < {ini_path}")
            else:
                result = subprocess.run(f"dconf load {dconf_path} < {ini_path}", shell=True, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    print(f"✅ Cargado: {dconf_path}")
                else:
                    print(f"⚠️ Advertencia al cargar {dconf_path}: {result.stderr.strip()}")

    log_append("GNOME dconf", "Configuraciones visuales inyectadas (Shell e Interfaz).")

    wallpaper_dir = os.path.join(HOME, "Pictures", "Wallpapers")
    profile_dir = os.path.join(HOME, "Pictures", "ProfilePic")

    if os.path.exists(wallpaper_dir):
        wallpapers = sorted([f for f in os.listdir(wallpaper_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        if wallpapers:
            print("\nImágenes encontradas en tu carpeta de Wallpapers:")
            for i, wp in enumerate(wallpapers, 1):
                print(f"  [{i}] {wp}")

            while True:
                sel_bg = input(f"\nSelecciona el número para tu WALLPAPER (1-{len(wallpapers)}) o '0' para omitir: ").strip()
                if sel_bg == '0':
                    wp_path = None
                    break
                try:
                    idx = int(sel_bg) - 1
                    if 0 <= idx < len(wallpapers):
                        wp_path = os.path.join(wallpaper_dir, wallpapers[idx])
                        break
                    else:
                        print("⚠️ Número fuera de rango.")
                except ValueError:
                    print("⚠️ Ingresa un número válido.")

            while True:
                sel_lock = input(f"Selecciona el número para tu PANTALLA DE BLOQUEO (1-{len(wallpapers)}) o '0' para omitir: ").strip()
                if sel_lock == '0':
                    lock_path = None
                    break
                try:
                    idx = int(sel_lock) - 1
                    if 0 <= idx < len(wallpapers):
                        lock_path = os.path.join(wallpaper_dir, wallpapers[idx])
                        break
                    else:
                        print("⚠️ Número fuera de rango.")
                except ValueError:
                    print("⚠️ Ingresa un número válido.")

            if wp_path:
                print(f"\n -> Configurando wallpaper: {os.path.basename(wp_path)}")
                cmd_wp_light = ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", f"file://{wp_path}"]
                cmd_wp_dark = ["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", f"file://{wp_path}"]
                if dry_run:
                    print(f"[DRY-RUN] Ejecutaría: {' '.join(cmd_wp_light)}")
                else:
                    subprocess.run(cmd_wp_light, check=False)
                    subprocess.run(cmd_wp_dark, check=False)
                    print("✅ Wallpaper configurado.")

            if lock_path:
                print(f" -> Configurando pantalla de bloqueo: {os.path.basename(lock_path)}")
                cmd_lock_light = ["gsettings", "set", "org.gnome.desktop.screensaver", "picture-uri", f"file://{lock_path}"]
                cmd_lock_dark = ["gsettings", "set", "org.gnome.desktop.screensaver", "picture-uri-dark", f"file://{lock_path}"]
                if dry_run:
                    print(f"[DRY-RUN] Ejecutaría: {' '.join(cmd_lock_light)}")
                else:
                    subprocess.run(cmd_lock_light, check=False)
                    subprocess.run(cmd_lock_dark, check=False)
                    print("✅ Pantalla de bloqueo configurada.")
        else:
            print("⚠️ No se encontraron imágenes válidas (.png, .jpg) en la carpeta de Wallpapers.")
    else:
        print("⚠️ El directorio de Wallpapers no existe aún.")

    if os.path.exists(profile_dir):
        pics = sorted([f for f in os.listdir(profile_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        if pics:
            pic_path = os.path.join(profile_dir, pics[0])
            face_path = os.path.join(HOME, ".face")
            print(f"\n -> Configurando foto de perfil desde: {pic_path}")

            if dry_run:
                print(f"[DRY-RUN] Copiaría {pic_path} a {face_path}")
            else:
                shutil.copy2(pic_path, face_path)
                print("✅ Foto de perfil configurada (~/.face).")
        else:
            print("⚠️ No se encontraron imágenes en la carpeta de ProfilePic.")
    else:
        print("⚠️ El directorio de ProfilePic no existe aún.")

    return True

def main():
    print("==> Iniciando Smart Restore v1.1")

    while True:
        mode = input("\n¿Deseas ejecutar en modo Simulación (Dry-Run)? No se harán cambios reales. (S/n): ").strip().lower()
        if mode in ['s', 'n', '', 'y']:
            break
        print("⚠️ Opción no válida.")

    is_dry_run = mode in ['s', '', 'y']
    if is_dry_run:
        print("\n🟢 MODO SIMULACIÓN ACTIVADO - No se modificará el sistema.")

    cache_sudo(dry_run=is_dry_run)
    configure_hostname(dry_run=is_dry_run)
    configure_timezone(dry_run=is_dry_run)

    tar_path = select_backup_file()
    filename = os.path.basename(tar_path)
    is_desktop_only = filename.startswith("escritorio_")

    if is_desktop_only:
        print("\nℹ️  Se detectó un respaldo EXCLUSIVO DE ESCRITORIO.")
        print("    Se omitirá la instalación de software y creación de directorios base.")

        if extract_backup(tar_path, dry_run=is_dry_run):
            configure_desktop(dry_run=is_dry_run)
            log_file = save_log()
            print("\n🎉 Personalización visual restaurada con éxito.")
            print(f"📄 Revisa el log en: {log_file}")
        else:
            log_file = save_log()
            print(f"\n⚠️ La restauración visual finalizó con errores. Revisa el log en: {log_file}")

    else: # <--- ESTE ES EL BLOQUE QUE FALTABA
        if not prepare_environment(tar_path, dry_run=is_dry_run):
            save_log()
            sys.exit(1)

        # --- CORRECCIÓN DE DESEMPAQUETADO ---
        status_sw, missing_pkgs = install_software(tar_path, dry_run=is_dry_run)
        if not status_sw:
            print("⚠️ Ocurrió un problema instalando el software, pero continuaremos con la extracción.")

        if extract_backup(tar_path, dry_run=is_dry_run):
            restore_personal_archive(tar_path, dry_run=is_dry_run)
            configure_desktop(dry_run=is_dry_run)

            log_file = save_log()
            print("\n" + "="*60)
            print("🎉 OPERACIÓN COMPLETADA. Tu sistema base y perfil están restaurados.")
            print("="*60)
            print(f"📄 Revisa el resumen detallado clínico en: {log_file}")

            if missing_pkgs:
                print("\n📦 PAQUETES NO INSTALADOS (Requieren revisión manual o incumplen políticas):")
                for pkg in missing_pkgs:
                   print(f"   - {pkg}")

            print("\n🏢 AVISO DE ENTORNO CORPORATIVO (COMPLIANCE):")
            print("   Si este equipo está gestionado por un MDM o Ansible (ej. Red Hat CSB),")
            print("   es probable que configuraciones de sistema a bajo nivel (Hostname,")
            print("   Firewall, llaves de dconf protegidas) regresen a su estado original")
            print("   en el próximo ciclo de sincronización para mantener el cumplimiento.")
            print("   Tus archivos de usuario ($HOME) y configuraciones locales están a salvo.")
            print("="*60)

            if not is_dry_run:
                while True:
                    reiniciar = input("\n¿Deseas reiniciar el sistema ahora para aplicar todos los cambios? (s/N): ").strip().lower()
                    if reiniciar in ['s', 'n', '']:
                        break
                    print("⚠️ Opción no válida.")

                if reiniciar == 's':
                    print(" -> Reiniciando el sistema en 3 segundos...")
                    subprocess.run(["sleep", "3"])
                    subprocess.run(["sudo", "reboot"])
                else:
                    print(" -> Reinicio omitido. Te sugerimos cerrar sesión para que GNOME recargue tu perfil.")
        else:
            log_file = save_log()
            print(f"\n⚠️ La restauración finalizó con errores críticos. Revisa el log en: {log_file}")

if __name__ == "__main__":
    main()

