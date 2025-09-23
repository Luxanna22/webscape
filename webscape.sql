-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Aug 26, 2025 at 08:31 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.1.25

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `capstone_v1`
--

-- --------------------------------------------------------

--
-- Table structure for table `admin_logs`
--

CREATE TABLE `admin_logs` (
  `id` int(11) NOT NULL,
  `admin_id` int(11) DEFAULT NULL,
  `action` text DEFAULT NULL,
  `timestamp` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `badges`
--

CREATE TABLE `badges` (
  `id` int(11) NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `icon` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `badges`
--

INSERT INTO `badges` (`id`, `name`, `description`, `icon`) VALUES
(1, 'First Steps', 'Complete your first lesson.', NULL),
(2, 'Tag Tamer', 'Finish all chapters in the HTML genre.', NULL),
(3, 'Perfect Run', 'Finish a full chapter with no incorrect attempts.', NULL),
(4, 'Queen', 'Ate and left no crumbs!', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `chapters`
--

CREATE TABLE `chapters` (
  `id` int(11) NOT NULL,
  `level_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `title` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `xp_reward` int(11) DEFAULT 0,
  `points_reward` int(11) DEFAULT 0,
  `order_num` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `chapters`
--

INSERT INTO `chapters` (`id`, `level_id`, `name`, `title`, `description`, `xp_reward`, `points_reward`, `order_num`) VALUES
(5, 1, 'html-basics', 'HTML Basics', 'Learn the fundamental elements and structure of HTML documents.', 100, 50, 1),
(7, 1, 'html-links', 'HTML Links', 'Master the creation and manipulation of hyperlinks to navigate between web pages.', 150, 75, 2),
(8, 1, 'html-semantic', 'Semantic HTML', 'Understand semantic elements and their importance in web development.', 200, 100, 3),
(9, 2, 'css-basics', 'CSS Basics', 'Learn the fundamentals of CSS styling.', 100, 50, 1),
(10, 2, 'css-layout', 'CSS Layout', 'Master CSS layout techniques including Flexbox and Grid.', 150, 75, 2),
(11, 2, 'css-responsive', 'Responsive Design', 'Create responsive websites that work on all devices.', 200, 100, 3);

-- --------------------------------------------------------

--
-- Table structure for table `leaderboards`
--

CREATE TABLE `leaderboards` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `total_score` int(11) DEFAULT 0,
  `total_wins` int(11) DEFAULT 0,
  `fastest_time` time DEFAULT NULL,
  `last_updated` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `lesson_choices`
--

CREATE TABLE `lesson_choices` (
  `id` int(11) NOT NULL,
  `lesson_content_id` int(11) NOT NULL,
  `choice_text` text NOT NULL,
  `is_correct` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `lesson_choices`
--

INSERT INTO `lesson_choices` (`id`, `lesson_content_id`, `choice_text`, `is_correct`) VALUES
(82, 5, 'Program robots', 0),
(83, 5, 'Hack NASA', 0),
(84, 5, 'Structure and build web pages', 1),
(85, 5, 'Regine Velasquez', 0);

-- --------------------------------------------------------

--
-- Table structure for table `lesson_content`
--

CREATE TABLE `lesson_content` (
  `id` int(11) NOT NULL,
  `chapter_id` int(11) NOT NULL,
  `page_num` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `content` text NOT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `code_example` text DEFAULT NULL,
  `next_button_text` varchar(50) DEFAULT 'Next',
  `page_type` enum('text_image','text_code','quiz','playground') DEFAULT 'text_image',
  `correct_message` text DEFAULT NULL,
  `incorrect_message` text DEFAULT NULL,
  `notes` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `lesson_content`
--

INSERT INTO `lesson_content` (`id`, `chapter_id`, `page_num`, `title`, `content`, `image_url`, `code_example`, `next_button_text`, `page_type`, `correct_message`, `incorrect_message`, `notes`) VALUES
(2, 5, 1, 'Introduction', 'Every website you\'ve ever visited is built using <span style=\"color: #ff66c4;\">HTML code</span>, that structures and displays content on the web.\r\n<br><br>\r\nWith WebScape, you’ll be able to build your own web page.', '/static/uploads/lesson_images\\1750208129_web-illustrations.png', '', 'Next', 'text_image', '', NULL, ''),
(3, 5, 3, 'Code Sample', 'This is sample HTML code:', 'https://lecontent.sololearn.com/material-images/556eb06d9ba4465ba4f7c127e352ce9e-4b1d81f4aa5e46038fbe64c37f953912-01.png', '<h1>Hi, welcome to WebScape!</h1>', 'Next', 'text_code', '', NULL, ''),
(5, 5, 2, '', 'HTML code is used to:', '', '', 'Continue', 'quiz', ' HTML is used to structure and build web pages by defining elements like headings, paragraphs, images, and links.', 'While HTML can look impressive, it won’t get you past NASA’s firewalls — it’s for building websites, not breaking into space agencies. 😉', ''),
(20, 9, 1, 'Introduction', 'Hi this is CSS', '/static/uploads/lesson_images\\1750393264_image-removebg-preview_6.png', '', 'Next', 'text_image', '', NULL, ''),
(24, 5, 4, '', 'Below is an example of heading. You can use different heading from heading 1 to 6 (h1-h6).\r\n<br><br>\r\nTry to run the code below:', NULL, '<h1>This is Heading 1.</h1>\r\n<h2>This is Heading 2.</h2>\r\n<h3>This is Heading 3.</h3>\r\n', 'Next', 'playground', '', NULL, ''),
(26, 5, 5, 'Lesson Takeaways', '<h1>Lesson Takeaways</h1>\r\n<br>\r\n<ul>\r\n<li>You have learned what the HTML does.</li>\r\n<li>Discovered different types of Headings.</li>\r\n<li>Learned how HTML code works!</li>\r\n</ul>', NULL, '<h1>This is Heading 1.</h1>\r\n<h2>This is Heading 2.</h2>\r\n<h3>This is Heading 3.</h3>\r\n', 'Next', 'text_image', '', NULL, '');

-- --------------------------------------------------------

--
-- Table structure for table `lesson_page_analytics`
--

CREATE TABLE `lesson_page_analytics` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `chapter_id` int(11) NOT NULL,
  `page_num` int(11) NOT NULL,
  `time_spent` int(11) DEFAULT 0,
  `visit_count` tinyint(1) DEFAULT 0,
  `incorrect_attempts` int(11) DEFAULT 0,
  `last_visited` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `lesson_page_analytics`
--

INSERT INTO `lesson_page_analytics` (`id`, `user_id`, `chapter_id`, `page_num`, `time_spent`, `visit_count`, `incorrect_attempts`, `last_visited`) VALUES
(82, 9, 5, 1, 2, 1, 0, '2025-06-24 02:10:25'),
(83, 9, 5, 2, 1, 1, 0, '2025-06-24 02:10:27'),
(84, 9, 5, 3, 0, 1, 0, '2025-06-24 02:10:27'),
(85, 9, 5, 4, 0, 1, 0, '2025-06-24 02:10:27'),
(86, 9, 5, 5, 0, 1, 0, '2025-06-24 02:10:28'),
(87, 9, 5, 6, 0, 1, 0, '2025-06-24 02:10:28'),
(88, 14, 5, 1, 3, 1, 0, '2025-06-24 02:28:22'),
(89, 14, 5, 2, 40, 1, 0, '2025-06-24 02:29:02'),
(90, 14, 5, 3, 144, 1, 0, '2025-06-24 02:31:26'),
(91, 8, 5, 1, 2, 1, 0, '2025-06-24 02:50:21'),
(92, 8, 5, 2, 2, 1, 1, '2025-06-24 02:50:23'),
(93, 8, 5, 3, 0, 1, 0, '2025-06-24 02:50:23'),
(94, 8, 5, 4, 0, 1, 0, '2025-06-24 02:50:24'),
(95, 8, 5, 5, 0, 1, 0, '2025-06-24 02:50:24'),
(96, 8, 5, 6, 0, 1, 0, '2025-06-24 02:50:24'),
(97, 17, 5, 1, 11, 1, 0, '2025-07-01 14:50:49'),
(98, 17, 5, 2, 6, 1, 0, '2025-07-01 14:50:56'),
(99, 17, 5, 3, 4, 1, 0, '2025-07-01 14:51:00'),
(100, 17, 5, 4, 20, 1, 0, '2025-07-01 14:51:21'),
(101, 17, 5, 5, 3, 1, 0, '2025-07-01 14:51:24'),
(102, 17, 5, 6, 8, 1, 0, '2025-07-01 14:51:33'),
(103, 7, 5, 1, 3, 1, 0, '2025-07-05 10:34:59'),
(104, 8, 7, 1, 16, 1, 1, '2025-07-13 11:46:40'),
(105, 8, 7, 2, 7, 1, 0, '2025-07-13 11:46:47'),
(106, 8, 7, 3, 7, 1, 0, '2025-07-13 11:46:55'),
(107, 8, 9, 1, 4, 1, 0, '2025-07-15 20:46:41'),
(121, 19, 5, 1, 14, 1, 0, '2025-07-17 04:14:10'),
(122, 19, 5, 2, 2, 1, 0, '2025-07-17 04:14:13'),
(123, 19, 5, 3, 10, 1, 0, '2025-07-17 04:14:41'),
(124, 19, 5, 4, 28, 1, 0, '2025-07-17 04:15:10'),
(125, 19, 5, 5, 15, 1, 0, '2025-07-17 04:15:25'),
(126, 19, 5, 6, 10, 1, 0, '2025-07-17 04:15:35');

--
-- Triggers `lesson_page_analytics`
--
DELIMITER $$
CREATE TRIGGER `trg_visit_count_before_insert` BEFORE INSERT ON `lesson_page_analytics` FOR EACH ROW BEGIN
  IF NEW.visit_count NOT IN (0, 1) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'visit_count must be 0 or 1';
  END IF;
END
$$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER `trg_visit_count_before_update` BEFORE UPDATE ON `lesson_page_analytics` FOR EACH ROW BEGIN
  IF NEW.visit_count NOT IN (0, 1) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'visit_count must be 0 or 1';
  END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `levels`
--

CREATE TABLE `levels` (
  `id` int(11) NOT NULL,
  `genre` varchar(50) DEFAULT NULL,
  `title` varchar(100) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `difficulty` enum('easy','medium','hard') DEFAULT NULL,
  `code_challenge` text DEFAULT NULL,
  `expected_output` text DEFAULT NULL,
  `image_url` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `levels`
--

INSERT INTO `levels` (`id`, `genre`, `title`, `description`, `difficulty`, `code_challenge`, `expected_output`, `image_url`) VALUES
(1, NULL, 'HTML', 'Learn the building blocks of web pages. Master HTML elements, attributes, and document structure.', NULL, NULL, NULL, NULL),
(2, NULL, 'CSS', 'Style your web pages with CSS. Learn selectors, properties, layouts and responsive design.', NULL, NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `pvp_matches`
--

CREATE TABLE `pvp_matches` (
  `id` int(11) NOT NULL,
  `player1_id` int(11) DEFAULT NULL,
  `player2_id` int(11) DEFAULT NULL,
  `winner_id` int(11) DEFAULT NULL,
  `start_time` datetime DEFAULT NULL,
  `end_time` datetime DEFAULT NULL,
  `match_type` enum('quiz','code-challenge') DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `question_choices`
--

CREATE TABLE `question_choices` (
  `id` int(11) NOT NULL,
  `lesson_content_id` int(11) NOT NULL,
  `choice_text` text NOT NULL,
  `is_correct` tinyint(1) DEFAULT 0,
  `order_num` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('student','admin') DEFAULT 'student',
  `created_at` datetime DEFAULT current_timestamp(),
  `avatar_path` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `email`, `password`, `role`, `created_at`, `avatar_path`) VALUES
(7, 'admin', 'admin@gmail.com', '$2b$12$.cAnGGuGGUWed8UFJUhPlOvbx2q8f23boABXXtZ7V/ayInVZVHCFC', 'admin', '2025-05-12 00:42:42', NULL),
(8, 'lux', 'luxparradon@gmail.com', '$2b$12$r6Uel/eUjc1IJ1PnO/wm1On62n0EIHU1RyF0Ei9cVPrFlgBO3laoS', '', '2025-05-15 19:38:30', NULL),
(9, 'leblanc', 'lebevaine@gmail.comm', '$2b$12$DKzzWb63.HbiQeC4TMv2LuizZfctocbeay06zpQf6RG7shcsLYQ46', '', '2025-05-15 22:55:43', NULL),
(10, 'jeric', 'jericcanva@cesbizmain.store', '$2b$12$Dopi8q3dbQxu.hsRFVqA1eywefQKTa9KUYrDFE3WvGQwdhxCDcU8e', '', '2025-05-23 14:48:59', NULL),
(14, 'lorena', 'lorena@gmail.com', '$2b$12$dxQO3Be0hvHUC3q56hTYb.cBs7Y105m.gZ.x4FReHgtjSZI7zS2cK', '', '2025-06-18 13:41:25', NULL),
(15, 'ahri', 'ahri@gmail.com', '$2b$12$5R0uV/Tp7KAGKuqTUSyF.eqVOIheHsAClX05uMHTU7odrkbHUaSTq', '', '2025-06-20 05:43:13', NULL),
(16, 'anivia', 'anivia@gmail.com', '$2b$12$aQhE8UOVvXVpIPF3Tak15u9vWOIq9umw0CpRQpVI84uDYY.yDgkXm', '', '2025-06-21 23:24:04', NULL),
(17, 'apple', 'apple@gmail.com', '$2b$12$q9BHeJ6YaBFtFqJO/BCXtunKza0MSw3fH9swyif9NJFfofC9pTbMO', '', '2025-07-01 22:49:54', NULL),
(19, 'lime', 'lime@gmail.com', '$2b$12$AMN0ndNOXfczWJwQiysvVeCslHXnJIygglojTfTg7zLMJygj6kgkK', '', '2025-07-17 12:10:01', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `user_badges`
--

CREATE TABLE `user_badges` (
  `user_id` int(11) NOT NULL,
  `badge_id` int(11) NOT NULL,
  `earned_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user_badges`
--

INSERT INTO `user_badges` (`user_id`, `badge_id`, `earned_at`) VALUES
(8, 1, '2025-06-18 04:59:19'),
(8, 2, '2025-06-18 04:59:38'),
(8, 4, '2025-06-03 03:17:20');

-- --------------------------------------------------------

--
-- Table structure for table `user_progress`
--

CREATE TABLE `user_progress` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `chapter_id` int(11) NOT NULL,
  `progress` int(11) NOT NULL DEFAULT 0,
  `completed` tinyint(1) DEFAULT 0,
  `last_accessed` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user_progress`
--

INSERT INTO `user_progress` (`id`, `user_id`, `chapter_id`, `progress`, `completed`, `last_accessed`) VALUES
(2, 9, 5, 100, 1, '2025-05-20 05:12:13'),
(3, 10, 5, 0, 0, '2025-05-23 07:05:42'),
(210, 7, 5, 0, 0, '2025-06-17 17:53:38'),
(905, 15, 9, 0, 0, '2025-06-20 00:16:57'),
(1027, 8, 9, 100, 1, '2025-06-20 23:14:26'),
(1079, 16, 5, 100, 1, '2025-06-21 15:24:18'),
(1088, 8, 5, 100, 1, '2025-06-22 21:26:20'),
(1129, 14, 5, 40, 0, '2025-06-24 02:28:18'),
(1146, 17, 5, 100, 1, '2025-07-01 14:50:35'),
(1182, 8, 7, 0, 0, '2025-07-15 20:46:29'),
(1246, 19, 5, 100, 1, '2025-07-17 04:13:54'),
(1252, 19, 7, 0, 0, '2025-07-17 04:15:42');

-- --------------------------------------------------------

--
-- Table structure for table `user_stats`
--

CREATE TABLE `user_stats` (
  `user_id` int(11) NOT NULL,
  `xp` int(11) DEFAULT 0,
  `level` int(11) DEFAULT 1,
  `points` int(11) DEFAULT 0,
  `rating` int(11) DEFAULT 0,
  `last_updated` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user_stats`
--

INSERT INTO `user_stats` (`user_id`, `xp`, `level`, `points`, `rating`, `last_updated`) VALUES
(8, 300, 1, 150, 0, '2025-07-17 03:49:10'),
(19, 200, 1, 100, 0, '2025-07-17 12:18:51');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admin_logs`
--
ALTER TABLE `admin_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `admin_id` (`admin_id`);

--
-- Indexes for table `badges`
--
ALTER TABLE `badges`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `chapters`
--
ALTER TABLE `chapters`
  ADD PRIMARY KEY (`id`),
  ADD KEY `level_id` (`level_id`);

--
-- Indexes for table `leaderboards`
--
ALTER TABLE `leaderboards`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `lesson_choices`
--
ALTER TABLE `lesson_choices`
  ADD PRIMARY KEY (`id`),
  ADD KEY `lesson_content_id` (`lesson_content_id`);

--
-- Indexes for table `lesson_content`
--
ALTER TABLE `lesson_content`
  ADD PRIMARY KEY (`id`),
  ADD KEY `chapter_id` (`chapter_id`);

--
-- Indexes for table `lesson_page_analytics`
--
ALTER TABLE `lesson_page_analytics`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_user_chapter_page` (`user_id`,`chapter_id`,`page_num`),
  ADD KEY `chapter_id` (`chapter_id`);

--
-- Indexes for table `levels`
--
ALTER TABLE `levels`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `pvp_matches`
--
ALTER TABLE `pvp_matches`
  ADD PRIMARY KEY (`id`),
  ADD KEY `player1_id` (`player1_id`),
  ADD KEY `player2_id` (`player2_id`),
  ADD KEY `winner_id` (`winner_id`);

--
-- Indexes for table `question_choices`
--
ALTER TABLE `question_choices`
  ADD PRIMARY KEY (`id`),
  ADD KEY `lesson_content_id` (`lesson_content_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `user_badges`
--
ALTER TABLE `user_badges`
  ADD PRIMARY KEY (`user_id`,`badge_id`),
  ADD KEY `badge_id` (`badge_id`);

--
-- Indexes for table `user_progress`
--
ALTER TABLE `user_progress`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_user_chapter` (`user_id`,`chapter_id`),
  ADD KEY `chapter_id` (`chapter_id`);

--
-- Indexes for table `user_stats`
--
ALTER TABLE `user_stats`
  ADD PRIMARY KEY (`user_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admin_logs`
--
ALTER TABLE `admin_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `badges`
--
ALTER TABLE `badges`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `chapters`
--
ALTER TABLE `chapters`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=39;

--
-- AUTO_INCREMENT for table `leaderboards`
--
ALTER TABLE `leaderboards`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `lesson_choices`
--
ALTER TABLE `lesson_choices`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=94;

--
-- AUTO_INCREMENT for table `lesson_content`
--
ALTER TABLE `lesson_content`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=41;

--
-- AUTO_INCREMENT for table `lesson_page_analytics`
--
ALTER TABLE `lesson_page_analytics`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=129;

--
-- AUTO_INCREMENT for table `levels`
--
ALTER TABLE `levels`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT for table `pvp_matches`
--
ALTER TABLE `pvp_matches`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `question_choices`
--
ALTER TABLE `question_choices`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=20;

--
-- AUTO_INCREMENT for table `user_progress`
--
ALTER TABLE `user_progress`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1257;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `admin_logs`
--
ALTER TABLE `admin_logs`
  ADD CONSTRAINT `admin_logs_ibfk_1` FOREIGN KEY (`admin_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `chapters`
--
ALTER TABLE `chapters`
  ADD CONSTRAINT `chapters_ibfk_1` FOREIGN KEY (`level_id`) REFERENCES `levels` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `leaderboards`
--
ALTER TABLE `leaderboards`
  ADD CONSTRAINT `leaderboards_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `lesson_choices`
--
ALTER TABLE `lesson_choices`
  ADD CONSTRAINT `lesson_choices_ibfk_1` FOREIGN KEY (`lesson_content_id`) REFERENCES `lesson_content` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `lesson_content`
--
ALTER TABLE `lesson_content`
  ADD CONSTRAINT `lesson_content_ibfk_1` FOREIGN KEY (`chapter_id`) REFERENCES `chapters` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `lesson_page_analytics`
--
ALTER TABLE `lesson_page_analytics`
  ADD CONSTRAINT `lesson_page_analytics_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `lesson_page_analytics_ibfk_2` FOREIGN KEY (`chapter_id`) REFERENCES `chapters` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `pvp_matches`
--
ALTER TABLE `pvp_matches`
  ADD CONSTRAINT `pvp_matches_ibfk_1` FOREIGN KEY (`player1_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `pvp_matches_ibfk_2` FOREIGN KEY (`player2_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `pvp_matches_ibfk_3` FOREIGN KEY (`winner_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `question_choices`
--
ALTER TABLE `question_choices`
  ADD CONSTRAINT `question_choices_ibfk_1` FOREIGN KEY (`lesson_content_id`) REFERENCES `lesson_content` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `user_badges`
--
ALTER TABLE `user_badges`
  ADD CONSTRAINT `user_badges_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `user_badges_ibfk_2` FOREIGN KEY (`badge_id`) REFERENCES `badges` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `user_progress`
--
ALTER TABLE `user_progress`
  ADD CONSTRAINT `user_progress_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `user_progress_ibfk_2` FOREIGN KEY (`chapter_id`) REFERENCES `chapters` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `user_stats`
--
ALTER TABLE `user_stats`
  ADD CONSTRAINT `user_stats_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
