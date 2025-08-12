-- Create a function to atomically increment the free_conversions_used for a user.
create function public.increment_conversions(user_id_param uuid)
returns void as $$
begin
  update public.profiles
  set free_conversions_used = free_conversions_used + 1
  where id = user_id_param;
end;
$$ language plpgsql security definer;

-- Note: The `security definer` part is important. It makes the function
-- execute with the permissions of the user that defined it (the database owner),
-- not the user that calls it. This allows our backend service role to
-- update the table even if Row Level Security would otherwise prevent it.
