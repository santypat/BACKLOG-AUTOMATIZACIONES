-- Unifica el flujo histórico de soportes con los tres estados visibles.

begin;

update public.soportes_mantenimiento
set estado = 'En curso'
where estado in ('En Proceso', 'En proceso', 'En Curso', 'Terminado');

update public.soportes_mantenimiento
set estado = 'Pendiente'
where estado is null or btrim(estado) = '';

commit;
