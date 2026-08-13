# Auditoría inicial

Fecha: 13 de agosto de 2026

## Alcance revisado

- Repositorio y últimas revisiones de Git.
- Aplicación pública desplegada en Render.
- Dashboard en escritorio y viewport móvil de 390 × 844.
- Acceso de solo lectura con la clave `anon` a las tablas conocidas.
- Arranque local con Python 3.12 y las dependencias del proyecto.

## Datos observados sin extraer contenido

- 92 automatizaciones visibles.
- 83 relaciones entre automatizaciones y desarrolladores.
- 9 desarrolladores.
- 1 soporte o mantenimiento.

## Riesgos críticos

1. La aplicación no autentica usuarios. Al ser pública, cualquier operación que
   permita RLS queda disponible para cualquier visitante.
2. `.env` fue publicado y permanece en el historial de Git. La clave encontrada
   es `anon`, no `service_role`, pero debe considerarse pública. La seguridad
   depende completamente de las políticas RLS.
3. El repositorio no incluye el esquema ni las políticas de Supabase. No es
   posible confirmar todavía quién puede insertar, actualizar o borrar.
4. Las escrituras que afectan varias tablas no son transaccionales. Una falla
   intermedia puede dejar una tarea creada sin equipo, o borrar asignaciones sin
   completar una reasignación.

## Problemas altos

- Un único archivo de más de 2.700 líneas mezcla presentación, reglas y datos.
- Había dos implementaciones distintas de `actualizar_estado` y dos ramas de
  navegación para soportes.
- Los estados usaban variantes incompatibles: `En proceso` y `En Proceso`.
- El CSS forzaba fondo claro y texto claro en selectores bajo el tema oscuro.
- El dashboard consultaba el mismo conjunto de datos más de una vez por ciclo.
- Las dependencias no tenían versiones fijadas, haciendo los despliegues poco
  reproducibles.
- Los detalles técnicos de excepciones se enviaban directamente al visitante.
- Algunos filtros interpretaban nombres como expresiones regulares.
- El historial de soportes insertaba valores de la base dentro de HTML sin
  escapar.

## Problemas medios

- No existen pruebas automatizadas ni integración continua.
- No existe una migración versionada del esquema de Supabase.
- No hay auditoría de cambios, comentarios, adjuntos ni historial de estados.
- Las acciones se realizan introduciendo IDs manualmente, con alto riesgo de
  modificar el registro equivocado.
- Importar Excel puede dejar una importación parcialmente completada.
- No hay paginación del lado del servidor ni una consulta relacional única.
- Las métricas usan nombres ambiguos para horas manuales, horas posteriores y
  ahorro real.
- La navegación y el tablero son funcionales, pero todavía no se comportan como
  un flujo Kanban tipo Jira.

## Primera fase aplicada

- `.env` retirado del índice y protegido mediante `.gitignore`.
- `.env.example`, documentación y configuración declarativa de Render añadidos.
- Versiones de Python y dependencias fijadas.
- Validación explícita de configuración de Supabase.
- Estados centralizados y seguimiento coherente de fechas de inicio y fin.
- Caché de lectura con invalidación después de escrituras.
- Errores internos enviados al registro y mensajes seguros al usuario.
- Valores de soporte escapados antes de construir HTML.
- Filtros protegidos frente a caracteres de expresiones regulares.
- Código duplicado de estado y soportes eliminado.
- Contraste de selectores corregido para el tema oscuro.
- Tablero Kanban añadido con búsqueda, filtros y cambio de estado por nombre.
- Controles públicos de eliminación retirados de la interfaz.
- Migración RLS preparada para lectura, creación y actualización anónimas.
- Registro administrativo de inserciones y cambios preparado en Supabase.

## Próximas fases

1. Revisar y aplicar la migración de políticas RLS en Supabase.
2. Validar en producción el modelo acordado: lectura, creación y modificación
   públicas mediante enlace; eliminación solo administrativa.
3. Crear funciones RPC transaccionales para creación, reasignación, importación
   y eliminación.
4. Dividir la aplicación en configuración, repositorios, servicios, componentes
   y páginas.
5. Sustituir acciones por ID por selección directa de tarjetas o filas.
6. Crear tablero Kanban, vista de detalle, historial y métricas consistentes.
7. Añadir pruebas de reglas de negocio, importación y permisos.
