# Review app — Supabase + Vercel setup

The app is static (this `webapp/` folder). Reviewers log in by **email magic link**;
verdicts save to a free Supabase Postgres, tagged with the reviewer's verified email.

## 1. Create the Supabase project (free)
- https://supabase.com → New project. Pick a region near your reviewers. Wait ~2 min.

## 2. Create the verdicts table + security (SQL)
Supabase dashboard → **SQL Editor** → run:

```sql
create table if not exists public.verdicts (
  reviewer text not null,                 -- the reviewer's verified email
  corpus   text not null,
  item_id  text not null,
  status   text not null check (status in ('approve','reject','edit')),
  edits    jsonb,
  notes    text,
  ts       timestamptz default now(),
  user_id  uuid default auth.uid(),
  primary key (reviewer, corpus, item_id)
);
alter table public.verdicts enable row level security;

-- signed-in reviewers can READ all verdicts (needed for agreement + adjudication)
create policy verdicts_read on public.verdicts
  for select to authenticated using (true);

-- ...but can only WRITE rows tagged with their OWN email (no impersonation)
create policy verdicts_write on public.verdicts
  for insert to authenticated with check (reviewer = auth.jwt()->>'email');
create policy verdicts_update on public.verdicts
  for update to authenticated using (reviewer = auth.jwt()->>'email')
                              with check (reviewer = auth.jwt()->>'email');
```

## 3. Auth settings
- **Authentication → Providers → Email**: enabled (default). Magic link works out of the box.
- **Authentication → URL Configuration**: set **Site URL** to your Vercel URL
  (e.g. `https://canoncite-review.vercel.app`) and add it under **Redirect URLs**.
  (Add `http://localhost:8000` too if you want to test locally.)
- **Restrict who can sign in (recommended):** Authentication → **Users → Invite user**,
  and invite only your reviewers' emails. (Or disable open signups in Auth settings so
  only invited emails work.)

## 4. Wire the app
- Copy `config.example.js` → `config.js` and paste your **Project URL** + **anon public key**.
  (`config.js` is gitignored; the anon key is safe in the browser because RLS is on.)

## 5. Deploy to Vercel (free)
- Import the repo at https://vercel.com → **Root Directory = `canoncite/review/webapp`**,
  Framework = Other (static). Deploy.
- Add `config.js` there: either commit it (anon key is public-safe) **or** set it via a
  Vercel build step / paste its contents. Simplest: commit `config.js` for a private repo.
- Put the resulting Vercel URL back into Supabase's Site URL / Redirect URLs (step 3).

Done — send reviewers the Vercel link; they sign in with email and start reviewing.
