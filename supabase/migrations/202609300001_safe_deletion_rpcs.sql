-- Eliminación pública controlada para la aplicación colaborativa.
-- Las tablas conservan DELETE revocado para anon; solo estas funciones
-- SECURITY DEFINER pueden borrar y exigen la confirmación exacta.

begin;

create or replace function public.eliminar_soporte_confirmado(
    p_soporte_id bigint,
    p_confirmacion text
)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
    filas_eliminadas integer;
begin
    if p_confirmacion is distinct from 'ELIMINAR' then
        raise exception 'Confirmación de eliminación inválida'
            using errcode = '22023';
    end if;

    delete from public.soportes_mantenimiento
    where id = p_soporte_id
      and coalesce(tipo_soporte, '') not in (
          '__DOCUMENTACION__',
          '__FECHA_ESTIMADA__',
          '__AVANCE_TAREA__'
      );

    get diagnostics filas_eliminadas = row_count;
    return filas_eliminadas = 1;
end;
$$;

revoke all on function public.eliminar_soporte_confirmado(bigint, text)
from public;
grant execute on function public.eliminar_soporte_confirmado(bigint, text)
to anon, authenticated;

create or replace function public.eliminar_tarea_confirmada(
    p_tarea_id bigint,
    p_confirmacion text
)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
    filas_eliminadas integer;
begin
    if p_confirmacion is distinct from 'ELIMINAR' then
        raise exception 'Confirmación de eliminación inválida'
            using errcode = '22023';
    end if;

    delete from public.desarrollo_dev
    where desarrollo_id = p_tarea_id;

    delete from public.soportes_mantenimiento
    where desarrollo = '__DESARROLLO_ID__:' || p_tarea_id::text
      and tipo_soporte in (
          '__DOCUMENTACION__',
          '__FECHA_ESTIMADA__',
          '__AVANCE_TAREA__'
      );

    delete from public.desarrollos
    where id = p_tarea_id;

    get diagnostics filas_eliminadas = row_count;
    return filas_eliminadas = 1;
end;
$$;

revoke all on function public.eliminar_tarea_confirmada(bigint, text)
from public;
grant execute on function public.eliminar_tarea_confirmada(bigint, text)
to anon, authenticated;

commit;
