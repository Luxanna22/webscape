-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Oct 09, 2025 at 06:27 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

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
(39, 19, 'CSS-Text style', 'CSS Text Styling Basics', 'Learn how to style a text.', 100, 50, 1),
(40, 19, 'CSS Spacing', 'CSS Spacing (Margin vs Padding)', 'Learn how to control the space inside and outside your elements.', 150, 75, 2),
(41, 19, 'CSS Selectors', 'CSS Selectors', 'Learn how to select and style specific elements in your webpage using CSS selectors.', 200, 100, 3),
(42, 19, 'Styling Links & Hover Effects', 'CSS Styling Links & Hover Effects', 'Learn how to style links and add hover effects to make your website more interactive and user-friendly.', 250, 125, 4),
(43, 19, 'Borders & Rounded Corners', 'CSS Borders & Rounded Corners', 'Learn how to use borders and border-radius to outline elements and create smooth, rounded corners.', 300, 150, 5),
(44, 1, 'html-text and headings', 'HTML Text & Headings', 'Learn how to use headings and paragraphs to add text to your webpage.', 100, 50, 1),
(45, 1, 'html-links and images', 'HTML Links & Images', 'Learn how to connect pages with links and add images to your site.', 150, 75, 2),
(46, 1, 'html-forms and imputs', 'HTML Forms & Inputs', 'Learn how to collect information from users with forms, text fields, and submit buttons.', 200, 100, 3),
(47, 20, 'js-variables and operators', 'JavaScript Variables & Operators', 'Learn how to store values and use operators in JavaScript.', 100, 50, 1),
(48, 20, 'js-statements and syntax', 'JavaScript Statements & Syntax', 'Learn how JavaScript statements are written and structured.', 150, 75, 2),
(49, 20, 'js-events and buttons', 'JavaScript Events & Buttons', 'Learn how to make buttons interactive with JavaScript events.', 200, 100, 3),
(50, 20, 'js-outputs and messages', 'JavaScript Output & Messages', 'Learn how to display messages in your webpage using JavaScript.', 250, 125, 4);

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
(101, 47, 'background-color', 0),
(102, 47, 'font-style', 0),
(103, 47, 'color', 1),
(104, 47, 'text-color', 0),
(109, 51, 'font-size', 1),
(110, 51, 'text-size', 0),
(111, 51, 'size', 0),
(112, 51, 'font-style', 0),
(113, 53, 'p { text-align: middle; }', 0),
(114, 53, 'p { align: center; }', 0),
(115, 53, 'p { text-align: center; }', 1),
(116, 53, 'p { content-align: center; }', 0),
(121, 59, 'margin', 0),
(122, 59, 'padding', 1),
(123, 59, 'spacing', 0),
(124, 59, 'border-spacing', 0),
(125, 57, 'padding', 0),
(126, 57, 'spacing', 0),
(127, 57, 'margin', 1),
(128, 57, 'border', 0),
(129, 66, '#', 0),
(130, 66, '.', 1),
(131, 66, ',', 0),
(132, 66, '@', 0),
(133, 68, '.', 0),
(134, 68, '#', 1),
(135, 68, '@', 0),
(136, 68, ',', 0),
(137, 73, 'a { text-style: none; }', 0),
(138, 73, 'a { decoration: none; }', 0),
(139, 73, 'a { text-decoration: none; }', 1),
(140, 73, 'a { underline: 0; }', 0),
(141, 75, 'button { hover-color: red; }', 0),
(142, 75, 'button:hover { background-color: red; }', 1),
(143, 75, 'button.hover { color: red; }', 0),
(144, 75, 'hover button { background: red; }', 0),
(145, 81, 'corner-radius', 0),
(146, 81, 'border-radius', 1),
(147, 81, 'round-corner', 0),
(148, 81, 'curve', 0),
(157, 92, '<a link=\"index.html\">Home</a>', 0),
(158, 92, '<a href=\"index.html\">Home</a>', 1),
(159, 92, '<link href=\"index.html\">Home</link>', 0),
(160, 92, '<url src=\"index.html\">Home</url>', 0),
(161, 94, '<a href=\"page.html\">Link</a>', 0),
(162, 94, '<a href=\"page.html\" target=\"_new\">Link</a>', 0),
(163, 94, '<a href=\"page.html\" target=\"_blank\">Link</a>', 1),
(164, 94, '<a target=\"newtab\">Link</a>', 0),
(165, 96, '<image src=\"sample.jpg\" alt=\"Sample\">', 0),
(166, 96, '<img src=\"sample.jpg\" alt=\"Sample\">', 1),
(167, 96, '<pic src=\"sample.jpg\" alt=\"Sample\">', 0),
(168, 96, '<photo src=\"sample.jpg\" alt=\"Sample\">', 0),
(169, 100, '<input placeholder=\"Enter name\">', 0),
(170, 100, '<input type=\"text\" placeholder=\"Enter name\">', 1),
(171, 100, '<textbox placeholder=\"Enter name\">', 0),
(172, 100, '<input text=\"Enter name\">', 0),
(173, 102, '<form><button>Submit</button></form>', 0),
(174, 102, '<form><submit>Submit</submit></form>', 0),
(175, 102, '<form><input type=\"submit\"></form>', 0),
(176, 102, 'Both a and c ✅', 1),
(177, 107, '==', 0),
(178, 107, '=', 1),
(179, 107, '===', 0),
(180, 107, ':=', 0),
(181, 109, 'if(age == 18)', 0),
(182, 109, 'if(age === 18)', 1),
(183, 109, 'if(age = 18)', 0),
(184, 109, 'if(age != 18)', 0),
(185, 114, '.', 0),
(186, 114, ':', 0),
(187, 114, ';', 1),
(188, 114, ',', 0),
(193, 119, '<button onclick=', 0),
(194, 119, '<button show=', 0),
(195, 119, '<button onhover=', 0),
(196, 119, '<button onclick=', 1),
(197, 120, '<button show=\"alert(\'You clicked the button!\')\">Click me</button>', 0),
(198, 120, '<button onclick=\"alert(\'You clicked the button!\')\">Click me</button>', 1),
(199, 120, '<button onhover=\"alert(\'You clicked the button!\')\">Click me</button>', 0),
(200, 120, '<button onclick=\"console.log(\'You clicked the button!\')\">Click me</button>', 0),
(201, 125, 'alert(\"Welcome!\");', 1),
(202, 125, 'console.log(\"Welcome!\");', 0),
(203, 125, 'print(\"Welcome!\");', 0),
(204, 125, 'message(\"Welcome!\");', 0),
(225, 86, '<h1>Hello World!</h1>', 1),
(226, 86, '<p>Hello World!</p>', 0),
(227, 86, '<div>Hello World!</div>', 0),
(228, 86, '<a>Hello World!</a>', 0),
(229, 87, '<p>Welcome</p>', 0),
(230, 87, '<heading>Welcome</heading>', 0),
(231, 87, '<h1>Welcome</h1>', 1),
(232, 87, '<title>Welcome</title>', 0);

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
(42, 39, 1, 'What is Txt Styling?', '<h5>CSS is like the “makeup” for your website.\r\nIt can change color, size, and alignment of your text.\r\n<br><br>\r\n👀 Imagine this:\r\n<br><br>\r\nWithout CSS → plain, boring black text.\r\n<br>\r\nWith CSS → colorful, readable, and well-placed text.\r\n<br><br><h5>', '/static/uploads/lesson_images\\1759126271_1676899274105.png', 'p {\r\n  color: blue;\r\n}\r\n', 'Next', 'text_image', '', NULL, ''),
(46, 39, 2, 'Changing Text Color', '<h5>This example below makes all paragraph text appear blue.\r\n<br><br>\r\nYou can use names (like red, blue), hex codes (#ff0000), or RGB (rgb(255,0,0)).<h5>\r\n<br>', NULL, '<p style=\"color: blue;\">\r\n  Hello, World!\r\n</p>\r\n', 'Next', 'text_code', '', NULL, ''),
(47, 39, 3, 'MCQ', '<h5>Which CSS property changes the text color?<h5>\r\n<br>', NULL, '', 'Next', 'quiz', 'color is indeed the css syntax for changing color.', NULL, ''),
(48, 39, 4, 'Changing Text Size', '<h5>Font-size makes text bigger or smaller.\r\n<br><br>\r\npx = fixed pixels (20px, 30px, etc.)\r\n<br>\r\n% or em = relative to surrounding text<h5>\r\n<br>', NULL, 'p {\r\n  font-size: 20px;\r\n}\r\n', 'Next', 'text_code', '', NULL, ''),
(49, 39, 6, 'Changing Text Size', '<h5>Try changing both color and size of this text: <h5>\r\n<br><br>\r\n', NULL, '<p style=\"font-size: ; color: ;\">\r\n  Hello, World!\r\n</p>\r\n', 'Next', 'playground', '', NULL, ''),
(50, 39, 7, 'Aligning Text', '<h5>This makes all paragraph text centered inside its box. \r\n\r\n<h5>\r\n<br>', NULL, '<p style=\"text-align: center;\">\r\n  Hello, World!\r\n</p>\r\n\r\np {\r\n  text-align: left;    /* Default: text starts from the left side */\r\n  text-align: right;   /* Moves all text to the right side */\r\n  text-align: justify; /* Spreads text so both left & right edges align neatly */\r\n}\r\n', 'Next', 'text_code', '', NULL, ''),
(51, 39, 5, 'MCQ', '<h5>Which CSS property controls text size?\r\n<h5><br>', NULL, '', 'Next', 'quiz', 'Great job—font-size is the CSS property used to control how big or small your text appears on the page.', NULL, ''),
(53, 39, 8, 'MCQ', '<h5>You want text in paragraph tag to be centered. Which is correct?\r\n<h5><br>', NULL, '', 'Next', 'quiz', 'Nice work—text-align: center; is the right way to center text inside a paragraph element.', NULL, ''),
(54, 39, 9, 'Lesson Takeaways ', '<h4>Lesson Takeaways – Text Styling Basics<h4><br>\r\n<h5>\r\nUse color to change text color. <br>\r\nUse font-size to control how big or small text appears. <br>\r\nUse text-align to align text: <br>\r\nleft (default) <br>\r\nright <br>\r\ncenter <br>\r\njustify<br><br>\r\nRemember: these properties apply to any text element<h5><br>', NULL, '', 'Next', 'text_image', '', NULL, ''),
(55, 40, 1, 'What is Spacing?', '<h5>In CSS, spacing makes your layout breathe. <br><br>\r\nMargin = space outside an element (pushes other elements away).<br>\r\nPadding = space inside an element (creates room between the content and the border).<h5><br>', '/static/uploads/lesson_images\\1759163439_Translation_6_.png', '', 'Next', 'text_image', '', NULL, ''),
(56, 40, 2, 'Margin Example', '<h5>This code below adds 20px of space outside the paragraph, so it sits away from other elements:\r\n<h5><br>', NULL, 'p {\r\n  margin: 20px;\r\n}\r\n', 'Next', 'text_code', '', NULL, ''),
(57, 40, 3, 'MCQ', 'Which CSS property adds space outside an element?', NULL, '', 'Next', 'quiz', 'Correct! margin is the coding property that controls the space outside an element.', NULL, ''),
(58, 40, 4, 'Padding Example', '<h5>This code below adds 20px of space inside the paragraph, pushing the text away from its border:\r\n<h5><br>', NULL, 'p {\r\n  padding: 20px;\r\n}\r\n', 'Next', 'text_code', '', NULL, ''),
(59, 40, 5, 'MCQ', 'Which CSS property adds space inside an element’s border?', NULL, '', 'Next', 'quiz', 'Right! padding is the coding property that controls the space inside the element’s border.', NULL, ''),
(60, 40, 6, 'Interactive Playground', '<h5>This code below creates a paragraph with margin, padding, and a border. Try changing the values to see the effect:\r\n<h5><br>', NULL, '<p style=\"margin: 30px; padding: 10px; border: 2px solid black; background-color: yellow;\">\r\n  Hello, CSS spacing!\r\n</p>\r\n', 'Next', 'playground', '', NULL, ''),
(61, 40, 7, 'Lesson Takeaways - Spacing', '<h4>Lesson Takeaways – Spacing<h4><br>\r\n<h5>\r\nMargin = space outside the element (separates elements).<br>\r\nPadding = space inside the element (adds room between text and border).<br><br>\r\nUse margin for layout spacing, padding for content spacing.<h5><br>', NULL, '', 'Next', 'text_image', '', NULL, ''),
(62, 41, 1, 'Introduction to CSS Selectors', '<h5>\r\nLearn how to select and style specific elements in your webpage using CSS selectors. <br><br>\r\nElement Selector → targets HTML tags (e.g., p, h1) <br>\r\nClass Selector (.) → targets elements with a class <br>\r\nID Selector (#) → targets a unique element with an ID \r\n<h5><br>\r\n\r\n', '/static/uploads/lesson_images\\1759165522_a-1664876228524-2x.jpg', '', 'Next', 'text_image', '', NULL, ''),
(64, 41, 2, 'Element Selector', '<h5>\r\nThis code below selects all paragraph elements and makes them blue:\r\n<h5><br>', NULL, '<p>Hello, world!</p>\r\n<p>This is another paragraph.</p>\r\n\r\n<style>\r\n  p {\r\n    color: blue;\r\n  }\r\n</style>\r\n', 'Next', 'text_code', '', NULL, ''),
(65, 41, 3, 'Class Selector', '<h5>\r\nThis code below uses a class selector (.) to style only elements with the class note:\r\n<h5><br>', NULL, '<p class=\"note\">This text is important.</p>\r\n<p>This text is normal.</p>\r\n\r\n<style>\r\n  .note {\r\n    color: green;\r\n    font-weight: bold;\r\n  }\r\n</style>\r\n', 'Next', 'text_code', '', NULL, ''),
(66, 41, 4, 'MCQ', '<h5>\r\nIn CSS, which symbol is used before a class selector?\r\n<h5><br>', NULL, '', 'Next', 'quiz', 'Great job! A dot (.) is used for class selectors. That means you can style many elements with the same class.', NULL, ''),
(67, 41, 5, 'ID Selector', '<h5>\r\nThis code below uses an ID selector (#) to style one unique element:\r\n<h5><br>', NULL, '<h1 id=\"title\">Welcome!</h1>\r\n\r\n<style>\r\n  #title {\r\n    color: red;\r\n    font-size: 28px;\r\n  }\r\n</style>\r\n', 'Next', 'text_code', '', NULL, ''),
(68, 41, 6, 'MCQ', '<h5>\r\nIn CSS, which symbol is used before an ID selector?\r\n<h5><br>', NULL, '', 'Next', 'quiz', 'Perfect! The hash symbol (#) is for IDs. An ID is special because it only styles one unique element.', NULL, ''),
(69, 41, 7, 'Practice with Selectors', '<h5>\r\nThis code below has an element, a class, and an ID. Try styling them differently:\r\n<h5><br>', NULL, '<h1 id=\"mainTitle\">Main Title</h1>\r\n<p class=\"highlight\">This is a highlighted paragraph.</p>\r\n<p>This is a normal paragraph.</p>\r\n\r\n<style>\r\n  h1 { color: blue; }          \r\n  .highlight { color: green; } \r\n  #mainTitle { font-size: 32px; }\r\n</style>\r\n', 'Next', 'playground', '', NULL, ''),
(70, 41, 8, 'Lesson Takeaways', '<h4>Lesson Takeaways - CSS Class Selectors<h4> <br>\r\n<h5>\r\nElement selector → styles all elements of that type.<br>\r\nClass selector (.) → styles elements with the same class.<br>\r\nID selector (#) → styles one unique element.\r\n<h5><br>', NULL, '', 'Next', 'text_image', '', NULL, ''),
(71, 42, 1, 'Styling Links', '<h5>\r\nLinks don’t have to stay plain blue and underlined — CSS lets you style them to match your design! <br><br>\r\nBy default, anchor tags are blue with an underline. <br>\r\nWith CSS, you can change their color, remove underline, or add effects when hovering.\r\n<h5><br>', '/static/uploads/lesson_images\\1759166813_maxresdefault.jpg', '', 'Next', 'text_image', '', NULL, ''),
(72, 42, 2, 'Remove Underline', '<h5>This code below removes the underline from all links:<h5><br>', NULL, '<a href=\"#\">Visit My Site</a>\r\n\r\n<style>\r\n  a {\r\n    text-decoration: none; /* removes underline */\r\n    color: blue;           /* keep the text blue */\r\n  }\r\n</style>\r\n', 'Next', 'text_code', '', NULL, ''),
(73, 42, 3, 'MCQ', '<h5>\r\nWhich CSS should you use to remove the underline from anchor links?\r\n<h5><br>', NULL, '', 'Next', 'quiz', 'Great! text-decoration: none; removes the underline from links. Now you can style links to look clean or even like buttons!', NULL, ''),
(74, 42, 4, 'Hover Effect', '<h5>\r\nThis code below changes the background when you hover over a link:\r\n<h5><br>', NULL, '<a href=\"#\">Hover over me!</a>\r\n\r\n<style>\r\n  a {\r\n    text-decoration: none;\r\n    padding: 5px 10px;\r\n    color: white;\r\n    background-color: blue;\r\n  }\r\n\r\n  a:hover {\r\n    background-color: red; /* changes color on hover */\r\n  }\r\n</style>\r\n', 'Next', 'text_code', '', NULL, ''),
(75, 42, 5, 'MCQ', '<h5>\r\nWhich CSS is correct to make a button turn red when hovered?\r\n<h5><br>', NULL, '', 'Next', 'quiz', 'Yes! button:hover is the right syntax. Hover is a pseudo-class—it activates when your mouse is over the element.', NULL, ''),
(76, 42, 6, 'Interactive Playground', '<h5>\r\nTry editing this code below to practice removing underlines and adding hover effects:\r\n<h5><br>', NULL, '<a href=\"#\">Click Me</a>\r\n\r\n<style>\r\n  a {\r\n    color: green;\r\n    text-decoration: underline; /* try changing to none */\r\n  }\r\n\r\n  a:hover {\r\n    color: orange; /* try changing to blue or red */\r\n  }\r\n</style>\r\n', 'Next', 'playground', '', NULL, ''),
(77, 42, 7, 'Lesson Takeaways', '<h4>Lesson Takeaways - CSS Styling Link and Hover Effects<h4><br>\r\n\r\n<h5>\r\ntext-decoration: none; removes underlines from links. <br>\r\n:hover is used to change styles when the mouse is over an element. <br>\r\nLinks can be styled like buttons with padding, colors, and hover effects.\r\n<h5><br>', NULL, '', 'Next', 'text_image', '', NULL, ''),
(78, 43, 1, 'Intro to Borders & Border Radius', '<h5>\r\nBorders outline elements, and border-radius lets you round the corners for smoother, modern designs. <br><br>\r\n\r\nborder → adds lines around elements. <br>\r\nborder-radius → makes corners curved (like buttons or cards).\r\n\r\n<h5><br>', '/static/uploads/lesson_images\\1759167717_css-border-radius.png', '', 'Next', 'text_image', '', NULL, ''),
(79, 43, 2, 'Adding a Border', '<h5>This code below creates a simple border around a paragraph:<h5><br>', NULL, '<p>Hello, World!</p>\r\n\r\n<style>\r\n  p {\r\n    border: 2px solid black; /* width, style, color */\r\n    padding: 10px;\r\n  }\r\n</style>\r\n', 'Next', 'text_code', '', NULL, ''),
(80, 43, 3, 'Rounded Corners', '<h5>This code below makes a button with rounded corners:<h5><br>', NULL, '<button>Click Me</button>\r\n\r\n<style>\r\n  button {\r\n    background-color: blue;\r\n    color: white;\r\n    padding: 10px 20px;\r\n    border: none;\r\n    border-radius: 10px; /* rounds the corners */\r\n  }\r\n</style>\r\n', 'Next', 'text_code', '', NULL, ''),
(81, 43, 4, 'MCQ', '<h5>\r\nWhich CSS property makes the corners of a button rounded?\r\n<h5><br>', NULL, '', 'Next', 'quiz', 'Perfect! border-radius is the magic that rounds corners. The higher the number (px or %), the rounder the element becomes!', NULL, ''),
(82, 43, 5, 'Interactive Playground', '<h5>Try editing this code to play with border styles and radius:<h5><br>', NULL, '<div class=\"box\">I am a box!</div>\r\n\r\n<style>\r\n  .box {\r\n    border: 3px solid red;\r\n    padding: 15px;\r\n    width: 200px;\r\n    text-align: center;\r\n    border-radius: 0px; /* try 10px, 25px, or 50% */\r\n  }\r\n</style>\r\n', 'Next', 'playground', '', NULL, ''),
(83, 43, 6, 'Lesson Takeaways', '<h4>Lesson Takeaways - CSS Borders and Round Corners<h4><br>\r\n\r\n<h5>\r\nborder adds outlines to elements (solid, dashed, dotted, etc.). <br>\r\npadding is inside the border; margin is outside. <br>\r\nborder-radius makes rounded corners — perfect for buttons or circles.\r\n<h5><br>', NULL, '', 'Next', 'text_image', '', NULL, ''),
(84, 44, 1, 'Intro to Text & Headings', '<h5>\r\nEvery webpage starts with text — headings for titles and paragraphs for regular content. <br><br>\r\n\r\nh1 to h6 tag → headings, from biggest to smallest. <br>\r\np tag → paragraph of text.\r\n<h5><br>', '/static/uploads/lesson_images\\1759168727_2022_04_HTML-Heading-and-Paragraph-Tags.jpg', '', 'Next', 'text_image', '', NULL, ''),
(85, 44, 2, 'Example', '<h5>This code below displays a heading and a paragraph:<h5><br>', NULL, '<h1>Hello World!</h1>\r\n<p>This is my first webpage.</p>\r\n', 'Next', 'text_code', '', NULL, ''),
(86, 44, 3, 'MCQ', 'You want to show a simple message “Hello World!” as a heading on your webpage. <br><br>Which HTML tag should you use?<br>', NULL, '<h1>Welcome to My Website</h1>\r\n<p>This is my first paragraph of text.</p>\r\n<h2>About Me</h2>\r\n<p>I love learning HTML!</p>\r\n', 'Next', 'quiz', 'Great choice! Headings like < h1 > are perfect for important text like page titles or big messages.', NULL, ''),
(87, 44, 4, 'MCQ', '<h6>You are creating a page heading called “Welcome” at the top of your site. <br><br>Which tag is correct?<h6><br>', NULL, '<h1>Welcome to My Website</h1>\r\n<p>This is my first paragraph of text.</p>\r\n<h2>About Me</h2>\r\n<p>I love learning HTML!</p>\r\n', 'Next', 'quiz', 'Awesome! < h1 > is for the main heading at the top of your page. You can use < h2 >, < h3 > … for subheadings.', NULL, ''),
(88, 44, 5, 'Practice Headings & Paragraphs', '<h5>\r\nTry editing this code below using different headings:<h5><br>', NULL, '<h1>Welcome to My Website</h1>\r\n<p>This is my first paragraph of text.</p>\r\n<h2>About Me</h2>\r\n<p>I love learning HTML!</p>\r\n', 'Next', 'playground', '', NULL, ''),
(89, 44, 6, 'Lesson Takeaways', '<h4>Lesson Takeaways - HTML Text & Headings<h4><br>\r\n\r\n<h5>\r\n< h1 > to < h6 > = headings (biggest to smallest). <br>\r\n< p > = paragraph text. <br>\r\nHeadings organize your content, paragraphs add details.\r\n<h5><br>', NULL, '', 'Next', 'text_image', '', NULL, ''),
(90, 45, 1, 'Introduction', '<h5>Links connect one page to another, while images add visuals. <br><br>\r\n\r\nA link uses the < a > tag (anchor) followed by href=\"link\". <br>\r\nAn image uses the < img > tag.\r\n<h5><br>', '/static/uploads/lesson_images\\1759169493_Make-a-Picture-Link-in-HTML-Step-6.jpg', '<h1>Welcome to My Website</h1>\r\n<p>This is my first paragraph of text.</p>\r\n<h2>About Me</h2>\r\n<p>I love learning HTML!</p>\r\n', 'Next', 'text_image', '', NULL, ''),
(91, 45, 2, 'Link Example', '<h5>This code below creates a link to another page: <h5><br>', NULL, '<a href=\"index.html\">Home</a>\r\n', 'Next', 'text_code', '', NULL, ''),
(92, 45, 3, 'MCQ', '<h5>Which code correctly creates a link to index.html? <h5><br>', NULL, '', 'Next', 'quiz', 'Great job! The < a href=\"...\" > tag is the real deal for links—href is like the URL’s GPS, telling the browser exactly where to go.\"', NULL, ''),
(93, 45, 4, 'Open Link in New Tab', '<h5>An anchor with a `target=\"_blank\"` opens the link in a new tab.<br><br>This code below opens the link in a new tab: <h5><br>', NULL, '<a href=\"page.html\" target=\"_blank\">Open in New Tab</a>\r\n', 'Next', 'text_code', '', NULL, ''),
(94, 45, 5, 'MCQ', '<h5>Which code opens a link in a new tab? <h5><br>', NULL, '', 'Next', 'quiz', 'Great work! Adding target=\"_blank\" tells the browser to launch the link in a brand-new tab—perfect for external sites.', NULL, ''),
(95, 45, 6, 'Image Example', 'Image `&#60img&#62` tag adds an image.  <br><br>This code below adds an image with alt text for accessibility: <br>', NULL, '<img src=\"sample.jpg\" alt=\"Sample\" width=\"200\" height=\"100\">\r\n', 'Next', 'text_code', '', NULL, ''),
(96, 45, 7, 'MCQ', '<h5>Which code correctly inserts an image named “sample.jpg” with alt text “Sample”? <h5><br>', NULL, '', 'Next', 'quiz', 'Awesome! The < img > tag is the standard for images. And the alt attribute is super important for accessibility.', NULL, ''),
(97, 45, 8, 'Lesson Takeaways - HTML Links & Images', '<h4>Lesson Takeaways - HTML Links & Images <h4><br>\r\n\r\n<h5>\r\nUse the < a > tag with href for links. <br>\r\nAdd target=\"_blank\" to open links in a new tab. <br>\r\nUse the < img > tag for images. <br><br>\r\nAlways include an alt attribute for accessibility.\r\n<h5><br>', NULL, '', 'Next', 'text_image', '', NULL, ''),
(98, 46, 1, 'Introduction', '<h5>\r\nForms are how websites ask users for information — like names, emails, or passwords. <br><br>\r\nUse the < form > tag to create a form. <br>\r\nUse the < input > tag to collect user input. <br>\r\nAdd a submit button to send the form.\r\n<h5><br>', '/static/uploads/lesson_images\\1759170119_HTML-Form-Input-Type.jpg', '', 'Next', 'text_image', '', NULL, ''),
(99, 46, 2, 'Text Input with Placeholder', '<h5>This code below creates a text field with a hint for the user: <h5><br>', NULL, '<input type=\"text\" placeholder=\"Enter name\">\r\n', 'Next', 'text_code', '', NULL, ''),
(100, 46, 3, 'MCQ', '<h5>Which code correctly creates a text input field with placeholder “Enter name”? <h5><br>', NULL, '', 'Next', 'quiz', 'Correct. The attribute type=\"text\" specifies a text input field, and placeholder provides a hint that appears inside the field until the user types.', NULL, ''),
(101, 46, 4, 'Form with Submit Button', '<h5>This code below creates a form with a working submit button: <h5><br>', NULL, '<form>\r\n  <input type=\"text\" placeholder=\"Your name\">\r\n  <input type=\"submit\" value=\"Submit\">\r\n</form>\r\n', 'Next', 'text_code', '', NULL, ''),
(102, 46, 5, 'MCQ', '<h5>Which HTML code correctly creates a form with a submit button? <h5><br>', NULL, '', 'Next', 'quiz', 'Perfect! You can use either a < button > or an < input type=\"submit\"> to make a submit button — both work inside a < form >.', NULL, ''),
(103, 46, 6, 'Interactive Playground', '<h5>Try creating a simple form with a text field and a submit button. <br><br>\r\nThis code below shows an example:\r\n <h5><br>', NULL, '<form>\r\n  <input type=\"text\" placeholder=\"Enter your email\">\r\n  <input type=\"submit\" value=\"Submit\">\r\n</form>\r\n', 'Next', 'playground', '', NULL, ''),
(104, 46, 7, 'Lesson Takeaways', '<h4>Lesson Takeaways - Forms & Links <h4><br>\r\n\r\n<h5>\r\nUse the < form > tag to create a form. <br>\r\nUse the < input > tag to collect user input. <br>\r\nAdd a submit button to send the form.\r\n<h5> <br>', NULL, '', 'Next', 'text_image', '', NULL, ''),
(105, 47, 1, 'Introduction to Variables', '<h5>\r\nJavaScript uses variables to store data, like numbers, text, or other information. <br><br>\r\nThink of a variable as a box with a label where you can keep something. <br>\r\nThe assignment operator (=) puts a value inside the box. \r\n<h5><br>', '/static/uploads/lesson_images\\1759171054_JS-EVERY-OPERATOR.png', '', 'Next', 'text_image', '', NULL, ''),
(106, 47, 2, 'Assigning a Value', '<h5> This code below assigns the value 10 to a variable named score: <br><br>\r\n\r\nlet → declares a variable. <br>\r\nscore → the variable name. <br>\r\n= → the assignment operator. <br>\r\n10 → the value stored in the variable. \r\n\r\n<h5><br>', NULL, 'let score = 10;\r\n', 'Next', 'text_code', '', NULL, ''),
(107, 47, 3, 'MCQ', '<h5>Which JavaScript operator is used to assign a value to a variable? <h5><br>', NULL, '', 'Next', 'quiz', 'Correct. The single equal sign = is the assignment operator in JavaScript. It stores a value in a variable.', NULL, ''),
(108, 47, 4, 'Comparison vs Strict Comparison', '<h5>This code below compares values using == and ===: <h5><br>', NULL, 'let age = \"18\";\r\n\r\nconsole.log(age == 18);   // true (compares only value)\r\nconsole.log(age === 18);  // false (compares value AND type)\r\n', 'Next', 'text_code', '', NULL, ''),
(109, 47, 5, 'MCQ', '<h5>Which code correctly checks if the variable age is equal to 18 in both value and type? <h5><br>', NULL, '', 'Next', 'quiz', 'Correct. The === operator checks both value and type, making it the strict equality operator.', NULL, ''),
(110, 47, 6, 'Lesson Takeaways', '<h4>Lesson Takeaways - JavaScript Variables & Operators <h4><br>\r\n\r\n<h5>\r\nUse the assignment operator = to give a variable a value. <br>\r\nUse == for equality comparison (value only). <br>\r\nUse === for strict equality comparison (value and type).\r\n<h5><br>', NULL, '', 'Next', 'text_image', '', NULL, ''),
(111, 48, 1, 'Introduction to Statements', '<h5>\r\nIn JavaScript, each instruction is called a statement. <br><br>\r\nStatements tell the computer what to do step by step.<br>\r\nMost statements end with a semicolon (;).\r\n<h5><br>', NULL, '', 'Next', 'text_image', '', NULL, ''),
(113, 48, 2, 'Ending Statements', '<h5> This code below declares a variable and ends the statement with a semicolon:  <br><br>\r\nWithout the semicolon, JavaScript might still run, but semicolons keep code clean and clear.\r\n<h5><br>', NULL, 'let name = \"Alice\";\r\nlet age = 18;\r\n', 'Next', 'text_code', '', NULL, ''),
(114, 48, 3, 'MCQ', '<h5>What symbol is used to end a statement in JavaScript?<h5><br>', NULL, '', 'Next', 'quiz', 'Great Job! A semicolon ; marks the end of a JavaScript statement, just like a period ends a sentence.\"', NULL, ''),
(115, 48, 4, 'Interactive Playground', '<h5>\r\nInstruction: Try declaring a variable and ending the statement properly.\r\n<br><br>\r\nExample code below:\r\n<h5><br>', NULL, 'let city = \"New York\";\r\n', 'Next', 'playground', '', NULL, ''),
(116, 48, 5, 'Lesson Takeaways', '<h4> Lesson Takeaways - Variables & Operators <h4><br>\r\n\r\n<h5>\r\nJavaScript code is written as statements. <br>\r\nMost statements end with a semicolon ;. <br>\r\nEnding statements properly makes your code more organized and readable.\r\n<h5><br>', NULL, '', 'Next', 'text_image', '', NULL, ''),
(117, 49, 1, 'Introduction to Events', '<h5>\r\nJavaScript can respond to user actions like clicking a button, hovering, or typing.\r\n<br><br>\r\nThese actions are called events. <br>\r\nThe most common is onclick, which runs code when a button is clicked.\r\n<h5><br>', '/static/uploads/lesson_images\\1759172364_maxresdefault_1.jpg', '', 'Next', 'text_image', '', NULL, ''),
(118, 49, 2, 'Button with onclick Alert', '<h5>This code below shows a button that displays a message when clicked:  <br><br>\r\nWhen you click the button, an alert box pops up with the message \"Hello!\".\r\n<h5><br>', NULL, '<button onclick=\"alert(\'Hello!\')\">Click me</button>\r\n', 'Next', 'text_code', '', NULL, ''),
(119, 49, 3, 'MCQ', '<h5>You want a button to show a message “Hello!” when clicked. Which code is correct? <h5><br>', NULL, '', 'Next', 'quiz', 'Nice job! You used onclick correctly — now your button can ‘listen’ for clicks and run alert() to show the message. That’s interactivity in action!', NULL, ''),
(120, 49, 4, 'MCQ', '<h5>You want a button to show a message “You clicked the button!” when someone clicks it. Which code is correct? <h5><br>', NULL, '', 'Next', 'quiz', 'Well done! By combining onclick with alert(), you’ve created a button that responds instantly to user clicks. That’s how websites talk back to users.', NULL, ''),
(121, 49, 5, 'Interactive Playground', '<h5> \r\nInstruction: Create your own button that shows any message when clicked. <br><br>\r\n\r\nExample code below:<h5><br>', NULL, '<button onclick=\"alert(\'Welcome to my site!\')\">Click me</button>\r\n', 'Next', 'playground', '', NULL, ''),
(122, 49, 6, 'Lesson Takeaways', '<h4>Lesson Takeaways - Events & Buttons <h4><br>\r\n\r\n<h5>JavaScript uses events to respond to user actions.\r\n<br>\r\nUse onclick to run code when a button is clicked.\r\n<br>\r\nUse alert() to show popup messages.\r\n<br>\r\nEvents make webpages interactive and dynamic.<h5><br>', NULL, '', 'Next', 'text_image', '', NULL, ''),
(123, 50, 1, 'Introduction to Output', '<h5>JavaScript can show messages in different ways:\r\n<br><br>\r\nalert() → shows a popup message box.\r\n<br>\r\nconsole.log() → writes a message in the browser console (for developers).<h5><br>', '/static/uploads/lesson_images\\1759172897_R.jpeg', '', 'Next', 'text_image', '', NULL, ''),
(124, 50, 2, 'Alert Message', '<h5>This code below displays a popup that says Welcome!:  <br><br>\r\nWhen the page runs, you’ll see a message box appear with the text.\r\n<h5><br>', NULL, 'alert(\"Welcome!\");\r\n', 'Next', 'text_code', '', NULL, ''),
(125, 50, 3, 'MCQ', '<h5>You want to display a message box with the text “Welcome!”. Which code should you use? <h5><br>', NULL, '', 'Next', 'quiz', 'Great work! alert() is the correct function for showing popup messages directly to the user.', NULL, ''),
(126, 50, 4, 'Interactive Playground', '<h5>Instruction: Write your own alert() message. <br><br>\r\n\r\nExample code below:<h5><br>', NULL, 'alert(\"Hello, JavaScript learner!\");\r\n', 'Next', 'playground', '', NULL, ''),
(127, 50, 5, 'Lesson Takeaways', '<h4>Lesson Takeaways - Output & Messages <h4><br>\r\n\r\n<h5>Use alert() to show popup messages. <br>\r\nUse console.log() to write messages in the console. <br>\r\nalert() is best for user interaction, while console.log() is best for debugging. <h5><br>', NULL, '', 'Next', 'text_image', '', NULL, '');

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
(130, 8, 39, 1, 36, 1, 0, '2025-10-07 04:18:01'),
(131, 8, 39, 2, 183, 1, 0, '2025-10-07 04:18:02'),
(132, 8, 39, 3, 4, 1, 0, '2025-10-07 04:15:45'),
(133, 8, 39, 4, 2, 1, 0, '2025-10-07 04:15:48'),
(134, 8, 39, 5, 160, 1, 0, '2025-10-07 04:15:59'),
(135, 8, 39, 6, 3, 1, 0, '2025-10-07 04:16:03'),
(136, 8, 39, 7, 2, 1, 0, '2025-10-07 04:16:06'),
(137, 8, 39, 8, 23, 1, 0, '2025-10-07 04:16:28'),
(138, 8, 39, 9, 63, 1, 0, '2025-10-07 04:16:32'),
(139, 8, 39, 10, 1, 1, 0, '2025-10-07 04:17:54'),
(140, 8, 40, 1, 6, 1, 0, '2025-09-29 16:48:15'),
(141, 8, 40, 2, 1, 1, 0, '2025-09-29 16:48:16'),
(142, 8, 40, 3, 4, 1, 0, '2025-09-29 16:48:20'),
(143, 8, 40, 4, 2, 1, 0, '2025-09-29 16:48:21'),
(144, 8, 40, 5, 3, 1, 0, '2025-09-29 16:48:24'),
(145, 8, 40, 6, 162, 1, 0, '2025-09-29 16:48:26'),
(146, 8, 40, 7, 45, 1, 0, '2025-09-29 16:48:29'),
(147, 8, 40, 8, 1, 1, 0, '2025-09-29 16:48:31'),
(148, 8, 41, 1, 5, 1, 0, '2025-09-29 17:27:06'),
(149, 8, 41, 2, 0, 1, 0, '2025-09-29 17:27:07'),
(150, 8, 41, 3, 3, 1, 0, '2025-09-29 17:27:10'),
(151, 8, 41, 4, 3, 1, 0, '2025-09-29 17:27:13'),
(152, 8, 41, 5, 1, 1, 0, '2025-09-29 17:27:15'),
(153, 8, 41, 6, 2, 1, 0, '2025-09-29 17:27:17'),
(154, 8, 41, 7, 1, 1, 0, '2025-09-29 17:27:18'),
(155, 8, 41, 8, 6, 1, 0, '2025-09-29 17:27:25'),
(156, 8, 41, 9, 2, 1, 0, '2025-09-29 17:27:27'),
(157, 8, 42, 1, 4, 1, 0, '2025-09-29 19:33:43'),
(158, 8, 44, 1, 14, 1, 0, '2025-10-07 04:13:04'),
(159, 8, 44, 2, 6, 1, 0, '2025-10-05 16:12:25'),
(160, 8, 44, 3, 29, 1, 1, '2025-10-05 16:12:55'),
(161, 8, 44, 4, 40, 1, 1, '2025-10-05 16:13:04'),
(162, 8, 44, 5, 50, 1, 0, '2025-10-05 16:13:07'),
(163, 8, 44, 6, 14, 1, 0, '2025-10-05 16:13:29'),
(164, 8, 44, 7, 4, 1, 0, '2025-10-05 16:13:42'),
(165, 8, 45, 1, 41, 1, 0, '2025-10-01 05:53:04'),
(166, 8, 45, 2, 0, 1, 0, '2025-10-01 05:53:19'),
(167, 8, 45, 3, 13, 1, 0, '2025-10-01 05:53:40'),
(168, 8, 45, 4, 1, 1, 0, '2025-10-01 05:53:45'),
(169, 8, 45, 5, 5, 1, 0, '2025-10-01 05:54:10'),
(170, 8, 45, 6, 1, 1, 0, '2025-10-01 05:54:14'),
(171, 8, 45, 7, 14, 1, 0, '2025-10-01 05:54:38'),
(172, 8, 45, 8, 47, 1, 0, '2025-10-01 05:54:39'),
(173, 8, 45, 9, 1, 1, 0, '2025-10-01 05:54:43'),
(174, 8, 46, 1, 3, 1, 0, '2025-10-01 06:14:50'),
(175, 8, 46, 2, 1, 1, 0, '2025-10-01 06:14:52'),
(176, 8, 46, 3, 17, 1, 1, '2025-10-01 06:15:15'),
(177, 8, 46, 4, 3, 1, 0, '2025-10-01 06:15:23'),
(178, 8, 46, 5, 5, 1, 0, '2025-10-01 06:15:42'),
(179, 8, 46, 6, 1, 1, 0, '2025-10-01 06:16:00'),
(180, 8, 46, 7, 2, 1, 0, '2025-10-01 06:16:05'),
(181, 8, 46, 8, 1, 1, 0, '2025-10-01 06:16:10'),
(182, 8, 42, 2, 0, 1, 0, '2025-09-29 19:33:44'),
(183, 8, 42, 3, 10, 1, 1, '2025-09-29 19:33:54'),
(184, 8, 42, 4, 1, 1, 0, '2025-09-29 19:33:56'),
(185, 8, 42, 5, 8, 1, 1, '2025-09-29 19:34:04'),
(186, 8, 42, 6, 1, 1, 0, '2025-09-29 19:34:06'),
(187, 8, 42, 7, 63, 1, 0, '2025-09-29 19:35:09'),
(188, 8, 42, 8, 1, 1, 0, '2025-09-29 19:35:10'),
(189, 8, 43, 1, 3, 1, 0, '2025-09-29 19:35:17'),
(190, 8, 43, 2, 0, 1, 0, '2025-09-29 19:35:18'),
(191, 8, 43, 3, 0, 1, 0, '2025-09-29 19:35:18'),
(192, 8, 43, 4, 8, 1, 0, '2025-09-29 19:35:27'),
(193, 8, 43, 5, 1, 1, 0, '2025-09-29 19:35:28'),
(194, 8, 43, 6, 1, 1, 0, '2025-09-29 19:35:30'),
(195, 8, 43, 7, 1, 1, 0, '2025-09-29 19:35:32'),
(196, 8, 47, 1, 3, 1, 0, '2025-09-29 19:35:41'),
(197, 8, 47, 2, 3, 1, 0, '2025-09-29 19:35:44'),
(198, 8, 47, 3, 4, 1, 0, '2025-09-29 19:35:49'),
(199, 8, 47, 4, 0, 1, 0, '2025-09-29 19:35:50'),
(200, 8, 47, 5, 5, 1, 0, '2025-09-29 19:35:55'),
(201, 8, 47, 6, 2, 1, 0, '2025-09-29 19:35:57'),
(202, 15, 44, 1, 27, 1, 0, '2025-09-30 07:57:36'),
(203, 15, 44, 2, 10, 1, 0, '2025-09-30 07:57:40'),
(204, 15, 44, 3, 22, 1, 0, '2025-09-30 07:57:47'),
(205, 15, 44, 4, 17, 1, 0, '2025-09-30 07:57:56'),
(206, 15, 44, 5, 16, 1, 0, '2025-09-30 07:58:02'),
(207, 15, 44, 6, 8, 1, 0, '2025-09-30 07:58:04'),
(208, 15, 44, 7, 4, 1, 0, '2025-09-30 07:58:26'),
(209, 15, 45, 1, 35, 1, 0, '2025-09-30 06:31:25'),
(210, 15, 45, 2, 12, 1, 0, '2025-09-30 06:31:16'),
(211, 15, 45, 3, 20, 1, 0, '2025-09-30 06:48:27'),
(212, 15, 45, 4, 225, 1, 0, '2025-09-30 06:48:21'),
(213, 15, 45, 5, 6, 1, 0, '2025-09-30 06:48:20'),
(214, 15, 45, 6, 230, 1, 0, '2025-09-30 06:48:18'),
(215, 15, 45, 7, 4, 1, 0, '2025-09-30 07:43:53'),
(216, 15, 47, 1, 16, 1, 0, '2025-09-30 07:33:47'),
(217, 15, 47, 2, 17, 1, 0, '2025-09-30 07:34:04'),
(218, 15, 47, 3, 6, 1, 0, '2025-09-30 07:49:47'),
(219, 15, 39, 1, 32, 1, 0, '2025-09-30 08:00:53'),
(220, 15, 47, 4, 6, 1, 0, '2025-09-30 07:49:54'),
(221, 15, 47, 5, 12, 1, 0, '2025-09-30 07:50:06'),
(222, 15, 47, 6, 2, 1, 0, '2025-09-30 07:50:08'),
(223, 15, 47, 7, 4, 1, 0, '2025-09-30 07:50:13'),
(224, 15, 39, 2, 1, 1, 0, '2025-09-30 08:00:55'),
(225, 15, 39, 3, 4, 1, 0, '2025-09-30 08:00:59'),
(226, 15, 39, 4, 17, 1, 0, '2025-09-30 08:01:41'),
(227, 15, 39, 5, 11, 1, 0, '2025-09-30 08:01:53');

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
(19, NULL, 'CSS', 'Learn to style your website through Cascading Style Sheets.', NULL, NULL, NULL, '/static/images/logo-css-3-1024.png'),
(20, NULL, 'JavaScript', 'Learn JavaScript to add interactivity, control behavior, and make your sites dynamic.', NULL, NULL, NULL, '/static/images/javascript-logo-javascript-icon-transparent-free-png.webp');

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
  `avatar_path` varchar(255) DEFAULT NULL,
  `google_id` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `email`, `password`, `role`, `created_at`, `avatar_path`, `google_id`) VALUES
(7, 'admin', 'admin@gmail.com', '$2b$12$.cAnGGuGGUWed8UFJUhPlOvbx2q8f23boABXXtZ7V/ayInVZVHCFC', 'admin', '2025-05-12 00:42:42', NULL, NULL),
(8, 'lux', 'luxparradon@gmail.com', '$2b$12$r6Uel/eUjc1IJ1PnO/wm1On62n0EIHU1RyF0Ei9cVPrFlgBO3laoS', '', '2025-05-15 19:38:30', NULL, NULL),
(9, 'leblanc', 'lebevaine@gmail.comm', '$2b$12$DKzzWb63.HbiQeC4TMv2LuizZfctocbeay06zpQf6RG7shcsLYQ46', '', '2025-05-15 22:55:43', NULL, NULL),
(10, 'jeric', 'jericcanva@cesbizmain.store', '$2b$12$Dopi8q3dbQxu.hsRFVqA1eywefQKTa9KUYrDFE3WvGQwdhxCDcU8e', '', '2025-05-23 14:48:59', NULL, NULL),
(14, 'lorena', 'lorena@gmail.com', '$2b$12$dxQO3Be0hvHUC3q56hTYb.cBs7Y105m.gZ.x4FReHgtjSZI7zS2cK', '', '2025-06-18 13:41:25', NULL, NULL),
(15, 'ahri', 'ahri@gmail.com', '$2b$12$5R0uV/Tp7KAGKuqTUSyF.eqVOIheHsAClX05uMHTU7odrkbHUaSTq', '', '2025-06-20 05:43:13', NULL, NULL),
(16, 'anivia', 'anivia@gmail.com', '$2b$12$aQhE8UOVvXVpIPF3Tak15u9vWOIq9umw0CpRQpVI84uDYY.yDgkXm', '', '2025-06-21 23:24:04', NULL, NULL),
(17, 'apple', 'apple@gmail.com', '$2b$12$q9BHeJ6YaBFtFqJO/BCXtunKza0MSw3fH9swyif9NJFfofC9pTbMO', '', '2025-07-01 22:49:54', NULL, NULL),
(19, 'lime', 'lime@gmail.com', '$2b$12$AMN0ndNOXfczWJwQiysvVeCslHXnJIygglojTfTg7zLMJygj6kgkK', '', '2025-07-17 12:10:01', NULL, NULL),
(20, 'leblancevainee', 'lebevaine@gmail.com', '', 'student', '2025-09-24 01:50:55', '/static\\uploads\\lesson_images\\1758653510_6ec175e1-5a0f-4eec-afcd-746f43d35f5a-removebg-preview.png', '105726867713002025007'),
(21, 'peñaverdeannelorraine', 'annelorrainepenaverde@gmail.com', '', 'student', '2025-09-24 13:34:28', '/static\\uploads\\lesson_images\\1758692089_Screenshot_2025-09-23_210750.png', '111382505205402802995');

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
(1272, 8, 39, 100, 1, '2025-09-29 06:03:37'),
(1286, 8, 40, 100, 1, '2025-09-29 16:30:56'),
(1292, 8, 41, 100, 1, '2025-09-29 17:05:32'),
(1302, 8, 42, 100, 1, '2025-09-29 17:27:30'),
(1303, 8, 44, 100, 1, '2025-09-29 19:21:32'),
(1312, 8, 45, 100, 1, '2025-09-29 19:25:30'),
(1323, 8, 46, 100, 1, '2025-09-29 19:32:04'),
(1339, 8, 43, 100, 1, '2025-09-29 19:35:12'),
(1346, 8, 47, 83, 0, '2025-09-29 19:35:38'),
(1352, 15, 44, 100, 1, '2025-09-30 06:14:56'),
(1359, 15, 45, 75, 0, '2025-09-30 06:16:46'),
(1369, 15, 47, 100, 1, '2025-09-30 07:33:29'),
(1375, 15, 39, 44, 0, '2025-09-30 07:40:43');

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
(8, 1750, 1, 875, 0, '2025-09-30 03:35:30'),
(15, 200, 1, 100, 0, '2025-09-30 15:50:08'),
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
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `idx_users_google_id` (`google_id`);

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
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=51;

--
-- AUTO_INCREMENT for table `leaderboards`
--
ALTER TABLE `leaderboards`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `lesson_choices`
--
ALTER TABLE `lesson_choices`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=233;

--
-- AUTO_INCREMENT for table `lesson_content`
--
ALTER TABLE `lesson_content`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=128;

--
-- AUTO_INCREMENT for table `lesson_page_analytics`
--
ALTER TABLE `lesson_page_analytics`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=228;

--
-- AUTO_INCREMENT for table `levels`
--
ALTER TABLE `levels`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=21;

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
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;

--
-- AUTO_INCREMENT for table `user_progress`
--
ALTER TABLE `user_progress`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1407;

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
