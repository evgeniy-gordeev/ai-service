-- Attach the second database file
ATTACH DATABASE 'resources/tenders_stage.db' AS stage;

-- For each common table, we'll need to run a separate query
-- This example assumes a table called 'tenders' with an 'id' column

-- Count total rows in each database
SELECT 
    'Main DB' AS database_name,
    COUNT(*) AS row_count
FROM tenders
UNION ALL
SELECT 
    'Stage DB' AS database_name,
    COUNT(*) AS row_count
FROM stage.tenders;

-- Count matching IDs between the two databases
SELECT 
    COUNT(*) AS matching_id_count
FROM tenders m
INNER JOIN stage.tenders s ON m.id = s.id;