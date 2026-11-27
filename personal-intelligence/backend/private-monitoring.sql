-- Reproduce the deployed private monitoring schema after profile-schema.sql.
-- Do not apply twice to the live project. Contains public paths only, no private records or keys.
begin;
create schema pi_internal;
revoke all on schema pi_internal from public,anon,authenticated;
create extension http with schema pi_internal;
create extension if not exists pg_cron;
alter table public.pi_profiles add column monitoring boolean not null default false, add column revision uuid not null default gen_random_uuid();
CREATE OR REPLACE FUNCTION pi_internal.profile_revision()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path TO 'pg_catalog'
AS $function$ begin new.revision:=gen_random_uuid(); return new; end $function$;
revoke all on function pi_internal.profile_revision() from public,anon,authenticated;
create trigger pi_revision before insert or update on public.pi_profiles for each row execute function pi_internal.profile_revision();
create table public.pi_watch_results(user_id uuid primary key references public.pi_profiles(user_id) on delete cascade, profile_revision uuid not null, checked_at timestamptz not null, findings jsonb not null, feed_status jsonb not null);
alter table public.pi_watch_results enable row level security;
revoke all on public.pi_watch_results from public,anon,authenticated;
grant select on public.pi_watch_results to authenticated;
create policy own_current_watch on public.pi_watch_results for select to authenticated using ((select auth.uid())=user_id and exists(select 1 from public.pi_profiles p where p.user_id=pi_watch_results.user_id and p.monitoring and p.revision=pi_watch_results.profile_revision));
create table pi_internal.feeds(id text primary key, path text not null, request_id bigint, requested_at timestamptz, retrieved_at timestamptz, status text not null default 'unavailable', payload jsonb);
insert into pi_internal.feeds(id,path) values ('affordability','data/affordability/bergen-basic-needs-2026.json'),('telecom','data/consumer-costs/telecom-picks-v1.json'),('shortage','eastern-axis/public/analysis/product-shortage-outlook.json'),('finance','eastern-axis/public/analysis/financial-transmission.json'),('warning','eastern-axis/public/analysis/early-warning-triage.json');
CREATE OR REPLACE FUNCTION pi_internal.run_watch()
 RETURNS void
 LANGUAGE plpgsql
 SET search_path TO 'pg_catalog'
AS $function$
declare p record; a jsonb; t jsonb; s jsonb; f jsonb; w jsonb; rec jsonb; oil jsonb; arr jsonb; health jsonb; diff numeric;
begin
 select payload into a from pi_internal.feeds where id='affordability' and status='retrieved' and retrieved_at>now()-interval '2 hours';
 select payload into t from pi_internal.feeds where id='telecom' and status='retrieved' and retrieved_at>now()-interval '2 hours';
 select payload into s from pi_internal.feeds where id='shortage' and status='retrieved' and retrieved_at>now()-interval '2 hours';
 select payload into f from pi_internal.feeds where id='finance' and status='retrieved' and retrieved_at>now()-interval '2 hours';
 select payload into w from pi_internal.feeds where id='warning' and status='retrieved' and retrieved_at>now()-interval '2 hours';
 select jsonb_object_agg(id,case when status='retrieved' and retrieved_at>now()-interval '2 hours' then 'retrieved' else 'unavailable' end) into health from pi_internal.feeds;
 delete from public.pi_watch_results r where not exists(select 1 from public.pi_profiles x where x.user_id=r.user_id and x.monitoring);
 for p in select user_id,profile,revision from public.pi_profiles where monitoring loop
  arr:='[]'::jsonb;
  if p.profile->>'county'='34003' and a#>>'{location,countyFips}'='34003' and a->>'asOf' ~ '^\d{4}-\d{2}-\d{2}$' and jsonb_typeof(a->'scenarios')='array' and jsonb_typeof(p.profile->'gross')='number' then
   select x into rec from jsonb_array_elements(a->'scenarios') x where x->>'id'=p.profile->>'household' limit 1;
   if jsonb_typeof(rec->'gross')='number' and (p.profile->>'gross')::numeric>=0 and (rec->>'gross')::numeric>=0 then
    diff:=(p.profile->>'gross')::numeric-(rec->>'gross')::numeric;
    arr:=arr||jsonb_build_array(jsonb_build_object('title','Compare income with county basic-needs model','value',diff,'unit','USD annual difference','date',a->>'asOf','source','https://livingwage.mit.edu/counties/34003','detail','Modeled county benchmark, not a personal expense estimate or benefits test.'));
   end if;
  end if;
  if p.profile->'lines'='2'::jsonb and t->>'schema'='power-atlas.consumer-costs.telecom-picks.v1' and t#>'{factualBaseline,eligibleVoiceLines}'='2'::jsonb and jsonb_typeof(t#>'{factualBaseline,sharedPicks}')='number' and t->>'reviewedUtc' ~ '^\d{4}-\d{2}-\d{2}$' then
   arr:=arr||jsonb_build_array(jsonb_build_object('title','Check shared wireless promotion limits','value',t#>'{factualBaseline,sharedPicks}','unit','account-level Picks','date',t->>'reviewedUtc','source','https://www.t-mobile.com/cell-phone-plans','detail','Dated terms, not a current quote. Verify offer and eligibility.'));
  end if;
  if p.profile->'drives'='true'::jsonb and jsonb_typeof(s->'forecasts')='array' then
   select x into rec from jsonb_array_elements(s->'forecasts') x where x->>'id'='fuel' and x->>'status'='input-cost-watch' and x->'confirmedShortage'='false'::jsonb limit 1;
   if jsonb_typeof(rec->'evidence')='array' then
    select x into oil from jsonb_array_elements(rec->'evidence') x where x->>'kind'='input-price' and x->>'title'='Brent crude oil' and jsonb_typeof(x->'changePct')='number' and x->>'period' ~ '^\d{4}-\d{2}$' limit 1;
    if oil is not null then arr:=arr||jsonb_build_array(jsonb_build_object('title','Monitor transport fuel input costs','value',oil->'changePct','unit','% Brent change','date',oil->>'period','source','https://www.worldbank.org/en/research/commodity-markets','detail','Input-cost watch only. Not a confirmed shortage or local pump-price forecast.')); end if;
   end if;
  end if;
  if p.profile->'employed'='true'::jsonb and jsonb_typeof(f->'householdMetrics')='array' then
   select x into rec from jsonb_array_elements(f->'householdMetrics') x where x->>'id'='UNRATE' and x->>'status'='ok' and jsonb_typeof(x->'value')='number' and x->>'period' ~ '^\d{4}-\d{2}-\d{2}$' limit 1;
   if rec is not null then arr:=arr||jsonb_build_array(jsonb_build_object('title','Review employment context','value',rec->'value','unit','% national unemployment','date',rec->>'period','source','https://fred.stlouisfed.org/series/UNRATE','detail','National context, not an individual job-loss forecast.')); end if;
  end if;
  insert into public.pi_watch_results values(p.user_id,p.revision,now(),arr,health) on conflict(user_id) do update set profile_revision=excluded.profile_revision,checked_at=excluded.checked_at,findings=excluded.findings,feed_status=excluded.feed_status;
 end loop;
end $function$;
CREATE OR REPLACE FUNCTION pi_internal.refresh_feeds()
 RETURNS void
 LANGUAGE plpgsql
 SET search_path TO 'pg_catalog'
AS $function$
declare f record; r pi_internal.http_response; j jsonb;
begin
 perform set_config('http.curlopt_timeout_ms','10000',true);
 perform set_config('http.curlopt_connecttimeout_ms','3000',true);
 for f in select id,path from pi_internal.feeds loop
  begin
   select * into r from pi_internal.http_get('https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/'||f.path);
   j:=case when r.status=200 and octet_length(r.content)<=2000000 then r.content::jsonb else null end;
   if jsonb_typeof(j)='object' then update pi_internal.feeds set payload=j,status='retrieved',requested_at=now(),retrieved_at=now() where id=f.id;
   else update pi_internal.feeds set payload=null,status='unavailable',requested_at=now() where id=f.id; end if;
  exception when others then update pi_internal.feeds set payload=null,status='unavailable',requested_at=now() where id=f.id; end;
 end loop;
end $function$;
revoke all on all functions in schema pi_internal from public,anon,authenticated;
select cron.schedule('pi-public-feed-hourly','5 * * * *','select pi_internal.refresh_feeds(); select pi_internal.run_watch();');
commit;
