#!/usr/bin/env bash
set -euo pipefail

printf 'hostname='; hostname -f 2>/dev/null || hostname
printf 'user='; id -un
printf 'groups='; id -Gn
printf 'home='; printf '%s\n' "$HOME"
uname -a
printf 'cpu_count='; nproc
free -h
df -hT "$HOME"
for command_name in module sbatch qsub pjsub bsub docker podman apptainer singularity sumo netconvert marouter python3 git rsync sha256sum; do
    printf '%s=' "$command_name"
    command -v "$command_name" || true
done
python3 --version 2>&1 || true
sumo --version 2>&1 || true
docker version 2>&1 || true
