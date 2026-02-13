# Smart College Placement System

## Structure
- Backend: [backend/app.py](backend/app.py)
- Database scripts: [database/schema.sql](database/schema.sql), [database/procedures.sql](database/procedures.sql), [database/triggers.sql](database/triggers.sql), [database/views.sql](database/views.sql), [database/indexes.sql](database/indexes.sql)

## Run backend
```sh
cd backend
python app.py
```

## Environment variables
- `DB_HOST` (default: `localhost`)
- `DB_USER` (default: `placement_user`)
- `DB_PASSWORD` (default: `placement_pass`)
- `DB_NAME` (default: `placement_db`)