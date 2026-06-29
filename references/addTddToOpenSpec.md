# Add TDD to a greenfield OpenSpec repo

Receta para que un repo **OpenSpec greenfield** genere tareas **test-first** en cada
change. OpenSpec no lo hace solo: su schema de `tasks` no menciona tests — el test vive
únicamente como `#### Scenario:` en la spec. Acá se le da la señal por contexto, igual que
el gate opt-in de GitHub Spec Kit.

> **Por qué:** la práctica autoritativa (GitHub Spec Kit, Amazon Kiro, TDD-con-agentes de
> Anthropic) pone el test **como tarea en `tasks.md`, antes de implementar**, derivado de
> los scenarios. OpenSpec es el más liviano y no lo trae; estos 4 pasos lo habilitan.

## Prerequisito

Repo ya inicializado con OpenSpec (`openspec init`), con `openspec/project.md` y al menos
una spec. Stack con test runner definible (estos ejemplos usan **Vitest**).

## 1. Convención TDD en `openspec/project.md`

Agregar esta sección (el generador la lee como contexto y por eso tira tasks test-first):

```
## Convención de testing (TDD)
El proyecto se construye con TDD. Al generar `tasks.md` de cualquier change:
- Por cada `### Requirement:`, crear PRIMERO una tarea de test que cubra todos sus
  `#### Scenario:`, ANTES de la tarea de implementación.
- Formato:
  - [ ] X.Y [TEST] <qué se testea> (desde scenarios de <requirement>) — debe fallar
  - [ ] X.Z Implementar <...> hasta que los tests pasen
- El test se deriva del scenario (GIVEN/WHEN/THEN), nunca del código.
- Test runner: Vitest (unit + integration). E2E (Playwright) en fases posteriores.
- TDD estricto y obligatorio en lógica de dominio (máquinas de estado, funciones de
  decisión con oracle claro). CRUD/UI plumbing puede ir test-after, pero igual cubre
  los scenarios.
- Pirámide: muchos unit (dominio), pocos integration (endpoints/eventos), mínimos E2E.
```

## 2. `CLAUDE.md` en la raíz del repo (archivo nuevo)

Gobierna `/opsx:apply`. Corto a propósito (un CLAUDE.md largo se ignora):

```
# <Proyecto> — instrucciones de proyecto

## Stack / tests
<stack>. Test runner: Vitest.
Correr: `npm test` · un archivo: `npm test -- <ruta>`.

## Workflow TDD (durante /opsx:apply)
1. Escribí los tests desde los `#### Scenario:` del requirement (no desde el código).
2. Corré y confirmá que FALLAN (rojo).
3. Commiteá los tests que fallan ANTES de implementar.
4. Implementá hasta verde. NO modifiques los tests para que pasen — si un test está
   mal, pará y avisá.
5. Mostrá la salida real de los tests como evidencia; no afirmes "pasa" sin correr.
```

El punto 3-4 (commitear el test fallando + no tocarlo) es la salvaguarda de Anthropic
contra que el agente cambie el test para que pase.

## 3. Test runner

No es un paso aparte: es una **decisión** registrada en los dos archivos de arriba
(ej. Vitest). La instalación real (`npm i -D vitest` + config + script `npm test`) entra
como **tarea del primer bloque de fundaciones** del `tasks.md`, no antes.

## 4. (Opcional) Perfil expandido para `/opsx:verify`

```
openspec config profile    # elegir el perfil expandido
openspec update            # regenera comandos/instrucciones
```

Habilita `/opsx:verify`, que tras `apply` reporta `⚠ Scenario X not tested` y cierra el
loop TDD.

## El ciclo resultante (por change)

1. `/opsx:propose <slug>` → el generador, con la convención en `project.md`, arma el
   `tasks.md` con una tarea `[TEST]` antes de cada implementación, por requirement.
2. Revisar el `tasks.md` → confirmar test-first y cobertura de cada scenario (red de
   seguridad manual; OpenSpec no lo garantiza).
3. `/opsx:apply` → red→green: test desde scenario → falla → commit del test fallando →
   implementar hasta verde, sin tocar el test.
4. `/opsx:verify` (perfil expandido) → confirma cada scenario testeado.
5. `/opsx:archive` → mergea deltas a `specs/`.

## Fuentes

- [GitHub Spec Kit — tasks template](https://github.com/github/spec-kit/blob/main/templates/commands/tasks.md) (test tasks opt-in, ordenadas test-first).
- [Amazon Kiro — specs](https://kiro.dev/docs/specs/) (requirements/design/tasks con testing strategy).
- [Anthropic — Best practices for Claude Code](https://code.claude.com/docs/en/best-practices) (TDD: test primero, commitear fallando, no modificar tests).
- [Google Testing Blog](https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html) / [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) — base de unit tests.
