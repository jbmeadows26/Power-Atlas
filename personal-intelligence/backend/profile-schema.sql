-- Apply only to a dedicated Personal Intelligence project after provisioning.
begin;
create table public.pi_profiles (
 user_id uuid primary key references auth.users(id) on delete cascade,
 profile jsonb not null default '{}'::jsonb,
 constraint pi_profile_object check (jsonb_typeof(profile)='object' and octet_length(profile::text)<=4096)
);
alter table public.pi_profiles enable row level security;
revoke all on public.pi_profiles from public, anon, authenticated;
grant select, insert, update, delete on public.pi_profiles to authenticated;
create policy pi_select_own on public.pi_profiles for select to authenticated using ((select auth.uid())=user_id);
create policy pi_insert_own on public.pi_profiles for insert to authenticated with check ((select auth.uid())=user_id);
create policy pi_update_own on public.pi_profiles for update to authenticated using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
create policy pi_delete_own on public.pi_profiles for delete to authenticated using ((select auth.uid())=user_id);
commit;
