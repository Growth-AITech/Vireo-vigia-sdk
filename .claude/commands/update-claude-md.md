---
description: Actualiza CLAUDE.md con las novedades recientes del proyecto
argument-hint: [novedad opcional a registrar]
allowed-tools: Read, Edit, Bash(git log:*), Bash(git diff:*), Bash(git status:*), Glob, Grep
---

# Actualizar CLAUDE.md

Tu tarea es actualizar el archivo de memoria del proyecto [CLAUDE.md](CLAUDE.md) para que
refleje el estado **actual** del proyecto Vireo Vigía SDK.

## Entrada del usuario
$ARGUMENTS

- Si el usuario escribió una novedad arriba, intégrala en la sección correcta de CLAUDE.md.
- Si no escribió nada, **descubre tú** las novedades comparando lo que dice CLAUDE.md con la
  realidad del repositorio.

## Pasos

1. **Lee** el estado actual de [CLAUDE.md](CLAUDE.md).
2. **Detecta novedades** desde el último estado documentado:
   - `git log --oneline -20` para ver commits recientes.
   - `git diff --stat HEAD~5 HEAD` (o desde el commit relevante) para ver qué cambió.
   - `git status` por si hay trabajo sin commitear que valga la pena registrar.
   - Revisa cambios estructurales: nuevos módulos en `src/vireo_vigia/`, nuevas env vars
     (`VIREO_*`), nuevos comandos del CLI, nuevos canales/chains, cambios en cómo se corre o testea.
3. **Decide qué merece ir en CLAUDE.md.** Solo registra lo que sea memoria duradera y útil para
   futuras sesiones:
   - Cambios de arquitectura, estructura o flujo.
   - Nuevas env vars, comandos, dependencias o pasos de setup.
   - Nuevos "Gotchas" aprendidos a las malas (sección dedicada).
   - Cambios de estado del negocio/distribución.
   - **NO** registres: detalles efímeros, cosas obvias del código, o ruido de commits triviales.
4. **Edita CLAUDE.md** con cambios quirúrgicos (usa Edit, no reescribas todo). Mantén el estilo,
   tono y formato existentes (tablas, secciones, emojis ya usados). Conserva el español/inglés
   tal como está en cada sección.
5. **Resume** al final, en 2-4 líneas, exactamente qué cambiaste y por qué.

## Reglas
- No inventes hechos: si no puedes verificar algo en el repo, pregúntalo o no lo escribas.
- No toques secciones que siguen siendo correctas.
- Si una novedad contradice algo ya escrito, corrige lo viejo en lugar de duplicar.
- No hagas commit salvo que el usuario lo pida explícitamente.
