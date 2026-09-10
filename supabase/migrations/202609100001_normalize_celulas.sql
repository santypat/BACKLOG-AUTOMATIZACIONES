-- Normaliza las células históricas al catálogo oficial usado por la aplicación.
begin;

update public.desarrollos
set celula = case trim(celula)
    when 'ACOMPAÑAMIENTO CANALES' then 'ACOMPAÑAMIENTO CANALES'
    when 'AREA' then 'TRANSVERSALES'
    when 'BDUA Y TRASLADOS' then 'TRASLADOS Y BDUA/ ACTIVACION DEL SERVICIO'
    when 'CALIDAD MANTENIMIENTO Y GESTIÓN DE GLOSAS' then 'CALIDAD MANTENIMIENTO Y GESTION DE GLOSAS'
    when 'COMPENSACION' then 'COMPENSACION'
    when 'Compensación' then 'COMPENSACION'
    when 'CONTROL Y GESTIÓN CARTERA' then 'CONTROL Y GESTION CARTERA'
    when 'CUOTAS MODERADORAS Y COPAGOS' then 'CUOTAS MODERADORAS Y COPAGOS'
    when 'Cuotas Moderadoras y copagos' then 'CUOTAS MODERADORAS Y COPAGOS'
    when 'DIRECCIÓN' then 'TRANSVERSALES'
    when 'EXPEDICION Y NOVEDADES' then 'EXPEDICION Y NOVEDADES'
    when 'MANTENIMIENTO Y CALIDAD' then 'CALIDAD MANTENIMIENTO Y GESTION DE GLOSAS'
    when 'MANTENIMIENTO Y CALIDAD DE LA INFORMACION' then 'CALIDAD MANTENIMIENTO Y GESTION DE GLOSAS'
    when 'OTRAS - NO PBS' then 'RECOBROS ARL'
    when 'RECOBROS' then 'RECOBROS ARL'
    when 'Sin Asignar' then 'TRANSVERSALES'
    when 'TRANSVERSALES' then 'TRANSVERSALES'
    when 'TRASLADOS Y BDUA/ ACTIVACIÓN DEL SERVICIO' then 'TRASLADOS Y BDUA/ ACTIVACION DEL SERVICIO'
    when 'TRASNVERSAL' then 'TRANSVERSALES'
    else trim(celula)
end;

update public.soportes_mantenimiento
set celula = case trim(celula)
    when 'EXPEDICION Y NOVEDADES' then 'EXPEDICION Y NOVEDADES'
    when 'RECOBROS ARL' then 'RECOBROS ARL'
    when 'TRASLADOS Y BDUA/ ACTIVACIÓN DEL SERVICIO' then 'TRASLADOS Y BDUA/ ACTIVACION DEL SERVICIO'
    else trim(celula)
end;

commit;
