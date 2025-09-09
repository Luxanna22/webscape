-- Database Performance Optimization Script
-- Run this script on your AIVEN MySQL database to add missing indexes

-- Add indexes for frequently queried columns
-- These will significantly improve query performance

-- Index for lesson_content table (most frequently accessed)
ALTER TABLE lesson_content ADD INDEX idx_chapter_page (chapter_id, page_num);
ALTER TABLE lesson_content ADD INDEX idx_page_type (page_type);

-- Index for lesson_choices table
ALTER TABLE lesson_choices ADD INDEX idx_lesson_content_id (lesson_content_id);

-- Index for user_progress table
ALTER TABLE user_progress ADD INDEX idx_user_chapter (user_id, chapter_id);
ALTER TABLE user_progress ADD INDEX idx_progress (progress);
ALTER TABLE user_progress ADD INDEX idx_completed (completed);

-- Index for chapters table
ALTER TABLE chapters ADD INDEX idx_level_id (level_id);
ALTER TABLE chapters ADD INDEX idx_order_num (order_num);

-- Index for users table (if not already exists)
ALTER TABLE users ADD INDEX idx_username (username);
ALTER TABLE users ADD INDEX idx_email (email);

-- Index for user_stats table (if it exists)
-- ALTER TABLE user_stats ADD INDEX idx_user_id (user_id);

-- Index for leaderboards table
ALTER TABLE leaderboards ADD INDEX idx_total_score (total_score DESC);
ALTER TABLE leaderboards ADD INDEX idx_user_id (user_id);

-- Index for user_badges table
ALTER TABLE user_badges ADD INDEX idx_user_id (user_id);
ALTER TABLE user_badges ADD INDEX idx_badge_id (badge_id);

-- Index for lesson_page_analytics table (if it exists)
-- ALTER TABLE lesson_page_analytics ADD INDEX idx_user_chapter_page (user_id, chapter_id, page_num);
-- ALTER TABLE lesson_page_analytics ADD INDEX idx_last_visited (last_visited);

-- Optimize table settings for better performance
-- These settings help with query optimization
SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';

-- Analyze tables to update statistics (helps query optimizer)
ANALYZE TABLE users;
ANALYZE TABLE chapters;
ANALYZE TABLE lesson_content;
ANALYZE TABLE lesson_choices;
ANALYZE TABLE user_progress;
ANALYZE TABLE leaderboards;
ANALYZE TABLE user_badges;
ANALYZE TABLE levels;

-- Show current indexes for verification
SHOW INDEX FROM lesson_content;
SHOW INDEX FROM lesson_choices;
SHOW INDEX FROM user_progress;
SHOW INDEX FROM chapters;
