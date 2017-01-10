-- command prompt
sqlite3 SteamAnalysis.db

-- setup commands
-- sqlite ints are huge...
create table users (
	user_id integer
	,friend_count integer
	,country varchar(20)
	,created integer
);
create table user_games (
	user_id integer
	,game_id integer
	,inserted text
	,time_played integer
);

--delete duplicates
delete from users
where user_id in
	(
		select
			user_id
		from
		(
			select
				user_id
				,count(*) as ct
			from users
			group by user_id
		)
		where ct > 1
	)
;



--export copy of userlist (just in case)
.headers on
.mode csv
.output userlist.csv
select * from users;
