\echo '================================================'
\echo '1. ALL TABLES WITH ROW COUNTS'
\echo '================================================'
SELECT tablename, n_live_tup AS row_count FROM pg_stat_user_tables WHERE schemaname = 'public' ORDER BY tablename;

\echo '================================================'
\echo '2. ATHLETES TABLE SCHEMA'
\echo '================================================'
SELECT column_name, data_type, character_maximum_length, is_nullable, column_default FROM information_schema.columns WHERE table_name = 'athletes' ORDER BY ordinal_position;

\echo '================================================'
\echo '3. TRAINING_PLANS TABLE SCHEMA'
\echo '================================================'
SELECT column_name, data_type, character_maximum_length, is_nullable, column_default FROM information_schema.columns WHERE table_name = 'training_plans' ORDER BY ordinal_position;

\echo '================================================'
\echo '4. PLANNED_WORKOUTS TABLE SCHEMA'
\echo '================================================'
SELECT column_name, data_type, character_maximum_length, is_nullable, column_default FROM information_schema.columns WHERE table_name = 'planned_workouts' ORDER BY ordinal_position;

\echo '================================================'
\echo '5. RIDES TABLE SCHEMA'
\echo '================================================'
SELECT column_name, data_type, character_maximum_length, is_nullable, column_default FROM information_schema.columns WHERE table_name = 'rides' ORDER BY ordinal_position;

\echo '================================================'
\echo '6. AI_FEEDBACK TABLE SCHEMA'
\echo '================================================'
SELECT column_name, data_type, character_maximum_length, is_nullable, column_default FROM information_schema.columns WHERE table_name = 'ai_feedback' ORDER BY ordinal_position;

\echo '================================================'
\echo '7. FOREIGN KEY RELATIONSHIPS'
\echo '================================================'
SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table, ccu.column_name AS foreign_column FROM information_schema.table_constraints AS tc JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public' AND tc.table_name IN ('athletes', 'training_plans', 'planned_workouts', 'rides', 'ai_feedback') ORDER BY tc.table_name;

\echo '================================================'
\echo '8. SAMPLE DATA - ATHLETES'
\echo '================================================'
SELECT * FROM athletes LIMIT 2;

\echo '================================================'
\echo '9. SAMPLE DATA - TRAINING_PLANS'
\echo '================================================'
SELECT * FROM training_plans LIMIT 1;

\echo '================================================'
\echo '10. SAMPLE DATA - PLANNED_WORKOUTS'
\echo '================================================'
SELECT * FROM planned_workouts LIMIT 2;
