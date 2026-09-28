<div align="center">
  <img src="https://raw.githubusercontent.com/rootzilopochtli/smart-migration-suite/main/banner.jpg" alt="Smart Migration Suite Python" width="100%">
</div>

# Smart Migration Suite 🐧⚙️

![Status](https://img.shields.io/badge/status-producción-success)
![License](https://img.shields.io/badge/license-MIT-blue)

**Smart Migration Suite** (anteriormente *Smart Backup*) es un conjunto de herramientas de línea de comandos (CLI) escritas en Python, diseñadas para automatizar, organizar y asegurar el proceso de respaldo y restauración de un entorno de trabajo para SysAdmins y Desarrolladores en Linux.

Este proyecto nació de la necesidad de liberar espacio crítico en disco, pero evolucionó hasta convertirse en un orquestador capaz de migrar tu identidad de desarrollador hacia entornos corporativos fuertemente administrados (como el *Corporate Standard Build* de Red Hat / IBM), respetando las políticas de ciberseguridad corporativas.

📖 **Lee la historia completa de su desarrollo en mi blog (rootzilopochtli.com):**
* Parte 1: [De Bash a Python: Automatización, IA y las Tres Leyes del SysAdmin](https://www.rootzilopochtli.com/de-bash-a-python-automatizacion-e-ia)
* Parte 2: [Linux como Ciudadano de Primera Clase: Automatizando tu Entorno en un Mundo Corporativo](https://www.rootzilopochtli.com/linux-como-entorno-corporativo)

> **⚠️ NOTA:** No soy un desarrollador experto en Python; me encuentro en pleno desarrollo de esta habilidad. Este script es el resultado de mi aprendizaje activo para resolver problemas operativos reales. Cualquier sugerencia de mejora o reporte de errores (vía *Issues* o *Pull Requests*) es más que bienvenida.

---

## 📦 Herramienta 1: Smart Backup (`smart_backup.py`)

Extrae y organiza tus datos con base en cuatro modos de operación interactivos:

1. **Modo Personal (Liberación de Espacio):** Analiza tu `$HOME` en busca de los directorios más pesados. Te permite decidir interactivamente si quieres respaldar una carpeta completa, depurarla internamente o ignorarla. Utiliza `rsync` de forma transaccional para mover y eliminar datos del origen solo si la copia fue exitosa.
2. **Modo Sistema (Empaquetado de Entorno):** Toma una "Lista de Oro" de *dotfiles* (`.ssh`, `.config`, `.vim`, etc.) y crea un manifiesto automático del software instalado (paquetes DNF y aplicaciones Flatpak), comprimiendo todo en un archivo `.tar.gz`.
3. **Modo Completo:** Ejecuta el modo Personal y el de Sistema de forma secuencial.
4. **Modo Escritorio (Exclusivo GNOME):** Extrae quirúrgicamente tu personalización visual (wallpapers, foto de perfil, extensiones y base de datos `dconf`), generando un archivo ultra-ligero para llevar tu "identidad gráfica" a cualquier máquina en segundos.

---

## 🛠️ Herramienta 2: Smart Restore (`smart_restore.py`)

Un orquestador inteligente diseñado para reconstruir tu entorno sin romper las reglas del sistema destino:

* **Aprovisionamiento de Software:** Lee los manifiestos creados en el respaldo e instala automáticamente los paquetes DNF y aplicaciones Flatpak.
* **Visibilidad Corporativa (Fail-Loud):** Si el repositorio corporativo bloquea la instalación de un paquete, el script no falla; captura el error y te entrega un reporte clínico al final para revisión manual.
* **Cirugía de GNOME (dconf):** Restaura tu configuración visual inyectando únicamente las ramas permitidas de la base de datos (`/org/gnome/shell/`), evitando conflictos con llaves bloqueadas por políticas de seguridad corporativas (MDMs/Ansible).
* **Extracción Idempotente:** Maneja de forma inteligente los errores de permisos (ej. al intentar sobreescribir repositorios de Git o llaves SSH de solo lectura) asegurando que el despliegue termine con éxito.

---

## 🚀 Requisitos y Uso

### Requisitos
Para ejecutar esta suite, asegúrate de tener instalados:
* Python 3.x
* `rsync`
* `tar`
* Entorno de escritorio GNOME (para la extracción/restauración visual)

### Instalación
Clona este repositorio en tu equipo:

```bash
$ git clone https://github.com/rootzilopochtli/smart-migration-suite.git
$ cd smart-migration-suite
```

### Ejecución
**Para respaldar tu máquina original**:

```bash
$ python3 smart_backup.py
```

_El script te pedirá la ruta de montaje de tu disco externo y te guiará paso a paso._

**Para restaurar en una máquina nueva**:

1. Monta tu disco externo en el equipo nuevo.
2. Copia de forma segura el script de restauración al equipo destino.
3. Ejecútalo con privilegios administrativos listos:

```bash
$ python3 smart_restore.py
```

## 🤝 Contribuciones
¿Tienes ideas para hacer el código más "Pythónico", optimizar funciones o agregar soporte para gestores de paquetes como `apt` o `pacman`? ¡Adelante! Siéntete libre de hacer un Fork del repositorio, crear tu rama y enviar un Pull Request.

## 📄 Licencia
Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---
👤 **Alex (@rootzilopochtli)** *Technical Training Developer en Red Hat | Miembro de Fedora Project | Autor de "Fedora Linux System Administration"*
