-- Om Malak boutique schema, apply to a dedicated Supabase project
create table if not exists public.om_malak_admins (
  user_id uuid primary key references auth.users(id) on delete cascade
);
create table if not exists public.om_malak_products (
  id uuid primary key default gen_random_uuid(),
  title text not null check (char_length(title) between 1 and 90),
  category text not null default 'إبداعات متنوعة',
  description text not null default '',
  price numeric(12,2) check(price >= 0),
  image_url text not null,
  storage_path text not null,
  published boolean not null default true,
  created_at timestamptz not null default now()
);
alter table public.om_malak_admins enable row level security;
alter table public.om_malak_products enable row level security;
create policy "admin self read" on public.om_malak_admins for select to authenticated using (user_id=(select auth.uid()));
create policy "products public read" on public.om_malak_products for select to anon, authenticated using (published or exists(select 1 from public.om_malak_admins a where a.user_id=(select auth.uid())));
create policy "admin insert products" on public.om_malak_products for insert to authenticated with check (exists(select 1 from public.om_malak_admins a where a.user_id=(select auth.uid())));
create policy "admin update products" on public.om_malak_products for update to authenticated using (exists(select 1 from public.om_malak_admins a where a.user_id=(select auth.uid()))) with check (exists(select 1 from public.om_malak_admins a where a.user_id=(select auth.uid())));
create policy "admin delete products" on public.om_malak_products for delete to authenticated using (exists(select 1 from public.om_malak_admins a where a.user_id=(select auth.uid())));
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('om-malak-gallery','om-malak-gallery',true,5242880,ARRAY['image/jpeg','image/png','image/webp'])
on conflict(id) do nothing;
create policy "om malak public view images" on storage.objects for select to anon, authenticated using(bucket_id='om-malak-gallery');
create policy "om malak admin upload" on storage.objects for insert to authenticated with check(bucket_id='om-malak-gallery' and exists(select 1 from public.om_malak_admins a where a.user_id=(select auth.uid())));
create policy "om malak admin delete image" on storage.objects for delete to authenticated using(bucket_id='om-malak-gallery' and exists(select 1 from public.om_malak_admins a where a.user_id=(select auth.uid())));
grant select on public.om_malak_products to anon, authenticated;
grant insert,update,delete on public.om_malak_products to authenticated;
grant select on public.om_malak_admins to authenticated;
-- After manually creating your mother's auth user, grant only her UUID:
-- INSERT INTO public.om_malak_admins(user_id) VALUES ('YOUR_MOTHER_AUTH_USER_UUID');
