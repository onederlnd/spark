import random
import os
from datetime import datetime, timedelta, timezone
import bcrypt
from app import create_app
from app.models import get_db

app = create_app()

# =========================================================
# 🔧 GLOBAL CONFIG (EDIT THESE ONLY)
# =========================y===============================

EMOJIS = ["❤️", "💡", "🤔", "🎯", "⚡", "🌟", "🔥"]

FIRST_NAMES = [
    "Alex",
    "Jordan",
    "Taylor",
    "Morgan",
    "Casey",
    "Riley",
    "Avery",
    "Quinn",
    "Cameron",
    "Drew",
    "Reese",
    "Parker",
    "Rowan",
    "Skyler",
    "Emerson",
    "Finley",
    "Hayden",
    "Jules",
    "Kendall",
    "Logan",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
]

TOPICS = [
    {"name": "Fractions & Decimals", "description": "Working with parts of numbers"},
    {"name": "Multiplication & Division", "description": "Times tables and dividing"},
    {"name": "Geometry", "description": "Shapes, area, and perimeter"},
    {"name": "Word Problems", "description": "Math in real life"},
    {"name": "Class Chat", "description": "Talk with your classmates"},
]

CLASSROOM = {
    "name": "5th Grade Math — Room 12",
    "description": "Let's make math fun!",
    "join_code": "YXG5WH",
}

POSTS = [
    {
        "user_role": "student",
        "topic": "Fractions & Decimals",
        "title": "How do you add fractions with different bottoms?",
        "body": "I get how to add 1/4 + 2/4 but what do you do when the bottom numbers are different? Like 1/3 + 1/4?",
        "replies": [
            {
                "user_role": "student",
                "body": "You have to find a number both bottoms can go into! It's called a common denominator.",
            },
            {
                "user_role": "teacher",
                "body": "Exactly right! For 1/3 + 1/4, both 3 and 4 go into 12. So change them to 4/12 + 3/12 = 7/12.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Multiplication & Division",
        "title": "I keep getting 7 x 8 wrong",
        "body": "I always mix up 7 x 8 and 7 x 9. Any tricks to remember?",
        "replies": [
            {
                "user_role": "student",
                "body": "5, 6, 7, 8 — 56 = 7 x 8! That's how I remember it.",
            },
            {
                "user_role": "teacher",
                "body": "That's a great trick! 5, 6, 7, 8 means 56 = 7 x 8. Say it a few times and it'll stick!",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Geometry",
        "title": "What is the difference between area and perimeter?",
        "body": "I always mix these two up on tests. Can someone explain the difference?",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Great question! Perimeter is the distance all the way around the outside of a shape — like a fence. Area is how much space is inside — like the grass. Perimeter adds all the sides, area multiplies length times width.",
            },
            {
                "user_role": "student",
                "body": "Oh! So if I'm putting a border around a picture frame that's perimeter, and if I'm filling it with paint that's area!",
            },
            {"user_role": "teacher", "body": "That is a perfect example!"},
        ],
    },
    {
        "user_role": "student",
        "topic": "Fractions & Decimals",
        "title": "How do you turn a fraction into a decimal?",
        "body": "My homework says to convert 3/4 to a decimal but I don't know how to do that.",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Divide the top number by the bottom number! 3 divided by 4 = 0.75. The top goes inside the division box.",
            },
            {
                "user_role": "student",
                "body": "Oh that actually makes sense! I tried it and got it right!",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Word Problems",
        "title": "How do I know if I should multiply or divide in a word problem?",
        "body": "Word problems are so confusing. How do I figure out which operation to use?",
        "replies": [
            {
                "user_role": "student",
                "body": "If they're putting equal groups together it's multiply. If they're splitting into equal groups it's divide!",
            },
            {
                "user_role": "teacher",
                "body": "That's a great way to think about it! Also look for keywords — 'each,' 'per,' and 'split equally' usually mean divide. 'In all,' 'total,' and 'altogether' usually mean multiply.",
            },
        ],
    },
    {
        "user_role": "teacher",
        "topic": "Fractions & Decimals",
        "title": "Tip: draw a picture to understand fractions!",
        "body": "When fractions feel confusing, try drawing a circle or rectangle and shading in the parts. A picture can make it way easier to see what's going on. Try it on your next homework!",
        "replies": [
            {
                "user_role": "student",
                "body": "I tried this and suddenly understood why 2/4 and 1/2 are the same!",
            },
            {
                "user_role": "student",
                "body": "Drawing really helped me on the comparing fractions worksheet.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Class Chat",
        "title": "I finally understand long division!!",
        "body": "I have been struggling with long division for weeks and today it finally clicked. Anyone else have a hard time at first?",
        "replies": [
            {
                "user_role": "student",
                "body": "YES it took me forever too. Does, McDonald's Sell Burgers Really helps me remember the steps.",
            },
            {
                "user_role": "student",
                "body": "What does that mean?",
            },
            {
                "user_role": "student",
                "body": "Divide, Multiply, Subtract, Bring down, Repeat! Each first letter.",
            },
            {
                "user_role": "teacher",
                "body": "I love that trick! It's totally normal for long division to take a while to click. Great persistence!",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Geometry",
        "title": "How do you find the area of a triangle?",
        "body": "We learned rectangles but now we have triangles on the homework and I don't remember the formula.",
        "replies": [
            {
                "user_role": "teacher",
                "body": "A triangle is exactly half of a rectangle! So the formula is base times height divided by 2. Write it as: Area = (b x h) / 2.",
            },
            {
                "user_role": "student",
                "body": "Ohhhh that makes sense because if you put two triangles together you get a rectangle!",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Word Problems",
        "title": "My answer keeps being way too big",
        "body": "I keep getting really huge numbers on word problems and I know they're wrong. What am I doing wrong?",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Try reading the problem again and ask yourself: does my answer make sense? If the problem is about how many cookies one person gets, the answer shouldn't be 500!",
            },
            {
                "user_role": "student",
                "body": "I bet you're multiplying when you should be dividing. Check what the question is actually asking!",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Fractions & Decimals",
        "title": "Is 0.5 the same as 1/2?",
        "body": "My teacher said they were equal but I want to make sure I understand why.",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Yes! 1 divided by 2 = 0.5. They are two different ways of writing the same amount. Half a pizza is half a pizza whether you write it as 1/2 or 0.5!",
            },
            {
                "user_role": "student",
                "body": "The pizza explanation makes it really easy to understand!",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Class Chat",
        "title": "Math is actually kind of fun??",
        "body": "I used to really not like math but the pizza fraction stuff today made me laugh. Anyone else starting to like it more?",
        "replies": [
            {
                "user_role": "student",
                "body": "YES! I hated fractions but once I got it I felt so smart.",
            },
            {
                "user_role": "student",
                "body": "Word problems are still hard but geometry is actually cool.",
            },
            {
                "user_role": "teacher",
                "body": "This makes me so happy to read! Math is everywhere once you start looking for it.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Geometry",
        "title": "What is a right angle?",
        "body": "I see right angle on a lot of problems but I want to make sure I know what it looks like.",
        "replies": [
            {
                "user_role": "teacher",
                "body": "A right angle is a perfect square corner — exactly 90 degrees. The corner of a piece of paper or a door is a right angle. You'll see a little square in the corner of diagrams to mark it!",
            },
            {
                "user_role": "student",
                "body": "Oh so every corner of a rectangle is a right angle?",
            },
            {"user_role": "teacher", "body": "Exactly right!"},
        ],
    },
    {
        "user_role": "student",
        "topic": "Multiplication & Division",
        "title": "What does remainder mean?",
        "body": "I got 14 remainder 2 on a division problem and I don't know what to do with the remainder.",
        "replies": [
            {
                "user_role": "teacher",
                "body": "The remainder is what's left over after you divide as evenly as you can! If you share 14 cookies with 6 friends, each person gets 2 and you have 2 left over. Those 2 are the remainder.",
            },
            {
                "user_role": "student",
                "body": "Ohhh so the remainder is just the leftovers that don't fit evenly!",
            },
        ],
    },
    {
        "user_role": "teacher",
        "topic": "Word Problems",
        "title": "Challenge: the pizza party problem!",
        "body": "Try this one: There are 28 students and each pizza has 8 slices. If every student gets 2 slices, how many pizzas do you need? Show your work and post your answer!",
        "replies": [
            {
                "user_role": "student",
                "body": "28 x 2 = 56 slices needed. 56 divided by 8 = 7. You need 7 pizzas!",
            },
            {
                "user_role": "student",
                "body": "I got 7 too! I drew it out first to make sure.",
            },
            {
                "user_role": "teacher",
                "body": "Great work everyone! Drawing it out is always a smart move.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Fractions & Decimals",
        "title": "How do you compare fractions?",
        "body": "I need to put 2/3, 1/2, and 3/4 in order from smallest to biggest but I don't know how.",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Turn them all into decimals! 1/2 = 0.5, 2/3 ≈ 0.67, 3/4 = 0.75. Now it's easy to put them in order: 1/2, 2/3, 3/4.",
            },
            {
                "user_role": "student",
                "body": "You can also draw fraction bars to compare them visually!",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Class Chat",
        "title": "Why did you start liking math?",
        "body": "I started liking math when I figured out I could use it to figure out if a sale at the store was actually a good deal. What about you?",
        "replies": [
            {
                "user_role": "student",
                "body": "I like figuring out sports stats! Like batting averages.",
            },
            {
                "user_role": "student",
                "body": "I used fractions to figure out how to double a recipe for cookies.",
            },
            {
                "user_role": "teacher",
                "body": "These are all amazing real-life examples. Math is literally everywhere!",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Geometry",
        "title": "How do you find perimeter when you only know two sides?",
        "body": "The rectangle on my homework only shows the length and width. How do I find the perimeter?",
        "replies": [
            {
                "user_role": "teacher",
                "body": "A rectangle has 2 long sides and 2 short sides that are equal. So add length + width and then multiply by 2! Perimeter = (length + width) x 2.",
            },
            {
                "user_role": "student",
                "body": "Or you can just add all four sides: length + length + width + width. Same answer!",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Multiplication & Division",
        "title": "Is there a fast way to multiply by 9?",
        "body": "The 9 times table trips me up. Is there a trick?",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Yes! Hold up all 10 fingers. To do 9 x 3, fold down your 3rd finger. You have 2 fingers on the left and 7 on the right — the answer is 27! This works for 9 x 1 through 9 x 10.",
            },
            {
                "user_role": "student",
                "body": "WHAT. That actually works. My mind is blown.",
            },
            {
                "user_role": "student",
                "body": "Also the digits of any 9 times table answer always add up to 9! Like 9x4=36 and 3+6=9.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Word Problems",
        "title": "What does 'difference' mean in a math problem?",
        "body": "The problem says 'find the difference' and I'm not sure what that's asking.",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Difference means subtract! 'Find the difference between 15 and 9' means 15 - 9 = 6. Math has special vocabulary — difference = subtract, sum = add, product = multiply, quotient = divide.",
            },
            {
                "user_role": "student",
                "body": "Oh wow I didn't know all those words. That's really helpful!",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Class Chat",
        "title": "Finished the fraction worksheet early!",
        "body": "Done with the whole thing and double-checked all my answers. Feels so good to be ahead for once!",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Amazing! Since you finished, try the challenge problems on the back — they're tricky but fun!",
            },
            {
                "user_role": "student",
                "body": "Wait there's a back?? Going to finish mine faster next time!",
            },
        ],
    },
]

ANNOUNCEMENTS = [
    {
        "title": "Welcome to Math Class!",
        "body": "So happy to have everyone here! Head to Fractions & Decimals to get started and say hi in Class Chat.",
    },
    {
        "title": "Quiz on Friday!",
        "body": "Don't forget — we have a quiz on fractions and decimals this Friday. Review your notes and practice problems!",
    },
    {
        "title": "Extra Help Tomorrow",
        "body": "I will be available after school tomorrow for anyone who wants extra help before the quiz. You've got this!",
    },
    {
        "title": "Great Work This Week!",
        "body": "I am so proud of how hard everyone is working. The fraction scores are really improving — keep it up!",
    },
]

ASSIGNMENTS = [
    {
        "title": "Fractions Practice",
        "instructions": "Add and subtract these fraction pairs and show your work: 1/2 + 1/4, 3/4 - 1/8, 2/3 + 1/6, 5/6 - 1/3. Remember to find a common denominator when the bottom numbers are different!",
        "submission_rate": 1.0,
        "submissions_template": [
            {
                "body": "1/2 + 1/4 = 2/4 + 1/4 = 3/4\n3/4 - 1/8 = 6/8 - 1/8 = 5/8\n2/3 + 1/6 = 4/6 + 1/6 = 5/6\n5/6 - 1/3 = 5/6 - 2/6 = 3/6 = 1/2",
                "grade": "A",
                "feedback": "Perfect work! You found common denominators correctly every time and even simplified 3/6 to 1/2. Excellent!",
            },
        ],
    },
    {
        "title": "Area and Perimeter",
        "instructions": "Find the area AND perimeter of these shapes. Show your formula and your work for each one. Shape 1: Rectangle, length = 8 cm, width = 5 cm. Shape 2: Square, side = 6 cm. Shape 3: Rectangle, length = 12 cm, width = 3 cm.",
        "submission_rate": 0.85,
        "submissions_template": [
            {
                "body": "Shape 1: Perimeter = (8+5) x 2 = 26 cm. Area = 8 x 5 = 40 sq cm.\nShape 2: Perimeter = 6 x 4 = 24 cm. Area = 6 x 6 = 36 sq cm.\nShape 3: Perimeter = (12+3) x 2 = 30 cm. Area = 12 x 3 = 36 sq cm.",
                "grade": "A",
                "feedback": "All three are correct and you showed your work clearly. Great job remembering to include units (cm and sq cm)!",
            },
            {
                "body": "Shape 1: Area = 8 x 5 = 40. Perimeter = 8 + 5 = 13.\nShape 2: Area = 36. Perimeter = 6 + 6 = 12.",
                "grade": "C",
                "feedback": "Your area is right for shapes 1 and 2! But perimeter needs ALL the sides added together, not just two. A rectangle has 4 sides. Also shape 3 is missing. Review the perimeter formula and try again!",
            },
        ],
    },
    {
        "title": "Multiplication Facts Timed Quiz",
        "instructions": "Solve all 20 multiplication problems. Try to do it without looking at a chart — this is practice for your brain! Problems: 6x7, 8x9, 7x6, 9x4, 6x8, 7x7, 8x6, 9x7, 6x9, 8x8, 7x9, 9x6, 6x6, 8x7, 7x8, 9x9, 6x4, 8x4, 7x4, 9x3.",
        "submission_rate": 0.90,
        "submissions_template": [
            {
                "body": "42, 72, 42, 36, 48, 49, 48, 63, 54, 64, 63, 54, 36, 56, 56, 81, 24, 32, 28, 27",
                "grade": "A",
                "feedback": "20 out of 20 — perfect score! You clearly know your facts. Keep practicing to stay sharp!",
            },
            {
                "body": "42, 72, 42, 36, 48, 49, 48, 63, 54, 64, 63, 54, 36, 56, 54, 81, 24, 32, 28, 27",
                "grade": "B",
                "feedback": "19 out of 20 — really great! Check number 15: 7 x 8 = 56, not 54. One common mix-up. Almost perfect!",
            },
        ],
    },
    {
        "title": "Word Problem Set",
        "instructions": "Solve each word problem and show ALL your work. Write a number sentence and a complete answer sentence for each one. Problem 1: A baker made 144 muffins and packed them into boxes of 12. How many boxes did she fill? Problem 2: A garden is 9 feet long and 7 feet wide. What is its area? Problem 3: Maya had $20. She spent $6.75 on lunch. How much does she have left? Problem 4: A class of 32 students is split into equal groups of 4. How many groups are there?",
        "submission_rate": 0.75,
        "submissions_template": [
            {
                "body": "1. 144 / 12 = 12. She filled 12 boxes.\n2. 9 x 7 = 63. The area is 63 square feet.\n3. $20.00 - $6.75 = $13.25. Maya has $13.25 left.\n4. 32 / 4 = 8. There are 8 groups.",
                "grade": "A",
                "feedback": "All four problems are correct and you wrote complete answer sentences for each one. This is exactly what I'm looking for. Great work!",
            },
            {
                "body": "1. 12 boxes\n2. 63\n3. 13.25\n4. 8 groups",
                "grade": "B",
                "feedback": "All your answers are correct! Next time show your number sentences so I can see how you got there. For example: 144 / 12 = 12.",
            },
            {
                "body": "1. 144 - 12 = 132\n2. 9 + 7 = 16\n3. 13.25\n4. 32 - 4 = 28",
                "grade": "D",
                "feedback": "Problem 3 is correct! But problems 1, 2, and 4 used the wrong operation. Re-read each problem carefully and ask: am I putting groups together or splitting them apart? Come see me and we can work through them together.",
            },
        ],
    },
    {
        "title": "Decimals: Compare and Order",
        "instructions": "Part 1: Put these decimals in order from smallest to biggest: 0.6, 0.06, 0.62, 0.3, 0.09. Part 2: Convert these fractions to decimals: 1/2, 1/4, 3/4, 1/5, 2/5. Part 3: Which is bigger — 0.7 or 3/4? Show how you know.",
        "submission_rate": 0.70,
        "submissions_template": [
            {
                "body": "Part 1: 0.06, 0.09, 0.3, 0.6, 0.62\nPart 2: 1/2=0.5, 1/4=0.25, 3/4=0.75, 1/5=0.2, 2/5=0.4\nPart 3: 3/4 is bigger because 3/4 = 0.75 and 0.75 > 0.7",
                "grade": "A",
                "feedback": "Excellent! All three parts are correct. I especially like that you showed 3/4 = 0.75 to prove which was bigger. That's exactly the right thinking!",
            },
            {
                "body": "Part 1: 0.06, 0.09, 0.3, 0.62, 0.6\nPart 2: 1/2=0.5, 1/4=0.25, 3/4=0.75, 1/5=0.2, 2/5=0.4\nPart 3: 0.7 is bigger",
                "grade": "C",
                "feedback": "Part 2 is perfect! In Part 1, check 0.6 vs 0.62 — which one is larger? In Part 3, convert 3/4 to a decimal and compare again. You're really close!",
            },
        ],
    },
]

QUIZZES = [
    {
        "title": "Quiz: Fractions",
        "instructions": "Show what you know about fractions! Answer all the questions below.",
        "due_date": "2026-04-25",
        "auto_grade": 1,
        "blocks": [
            {
                "type": "text",
                "position": 0,
                "points": 0,
                "required": 0,
                "body": (
                    "A fraction has two parts: the numerator (top number) and the denominator (bottom number). "
                    "The denominator tells you how many equal pieces the whole is split into. "
                    "The numerator tells you how many pieces you have.\n\n"
                    "Example: In 3/4, the whole is cut into 4 equal pieces and you have 3 of them."
                ),
            },
            {
                "type": "multiple_choice",
                "position": 1,
                "points": 2,
                "required": 1,
                "body": "What is the denominator in the fraction 5/8?",
                "choices": [
                    {"body": "5", "is_correct": 0},
                    {"body": "8", "is_correct": 1},
                    {"body": "13", "is_correct": 0},
                    {"body": "3", "is_correct": 0},
                ],
            },
            {
                "type": "true_false",
                "position": 2,
                "points": 1,
                "required": 1,
                "body": "True or False: 1/2 and 2/4 are equal.",
                "choices": [
                    {"body": "True", "is_correct": 1},
                    {"body": "False", "is_correct": 0},
                ],
            },
            {
                "type": "multiple_choice",
                "position": 3,
                "points": 2,
                "required": 1,
                "body": "What is 1/4 + 2/4?",
                "choices": [
                    {"body": "3/8", "is_correct": 0},
                    {"body": "2/8", "is_correct": 0},
                    {"body": "3/4", "is_correct": 1},
                    {"body": "1/2", "is_correct": 0},
                ],
            },
            {
                "type": "short_answer",
                "position": 4,
                "points": 3,
                "required": 1,
                "body": (
                    "In your own words, explain what a fraction means. "
                    "Use a food example to help explain your answer."
                ),
            },
            {
                "type": "short_answer",
                "position": 5,
                "points": 4,
                "required": 1,
                "body": (
                    "What is 1/3 + 1/6? Show your work and explain how you found a common denominator."
                ),
            },
        ],
        "submission_rate": 0.85,
        "submissions_template": [
            {
                "grade": "A",
                "feedback": "Fantastic work! You got every question right and your explanation was really clear.",
                "block_responses": [
                    {"position": 0, "body": None, "score": 0},
                    {"position": 1, "choice_index": 1, "score": 2},
                    {"position": 2, "choice_index": 0, "score": 1},
                    {"position": 3, "choice_index": 2, "score": 2},
                    {
                        "position": 4,
                        "body": "A fraction means part of a whole. Like if you cut a pizza into 8 slices and eat 3, you ate 3/8 of the pizza.",
                        "score": 3,
                    },
                    {
                        "position": 5,
                        "body": "1/3 + 1/6. I changed 1/3 to 2/6 because 3 x 2 = 6. Then 2/6 + 1/6 = 3/6 = 1/2.",
                        "score": 4,
                    },
                ],
            },
            {
                "grade": "B",
                "feedback": "Great job! You got the multiple choice right. Your fraction explanation was good but try to show more steps in your work.",
                "block_responses": [
                    {"position": 0, "body": None, "score": 0},
                    {"position": 1, "choice_index": 1, "score": 2},
                    {"position": 2, "choice_index": 0, "score": 1},
                    {"position": 3, "choice_index": 2, "score": 2},
                    {
                        "position": 4,
                        "body": "A fraction is part of something. Like half a sandwich is 1/2.",
                        "score": 2,
                    },
                    {
                        "position": 5,
                        "body": "I got 3/6 but I'm not sure if that's right.",
                        "score": 2,
                    },
                ],
            },
            {
                "grade": "C",
                "feedback": "You're on the right track! Review equivalent fractions and how to find common denominators. Come see me for extra help!",
                "block_responses": [
                    {"position": 0, "body": None, "score": 0},
                    {"position": 1, "choice_index": 0, "score": 0},
                    {"position": 2, "choice_index": 1, "score": 0},
                    {"position": 3, "choice_index": 0, "score": 0},
                    {
                        "position": 4,
                        "body": "A fraction is a number.",
                        "score": 1,
                    },
                    {
                        "position": 5,
                        "body": "1/3 + 1/6 = 2/9",
                        "score": 0,
                    },
                ],
            },
        ],
    },
    {
        "title": "Quiz: Multiplication & Division",
        "instructions": "Let's practice multiplication and division! Do your best on every question.",
        "due_date": "2026-05-02",
        "auto_grade": 1,
        "blocks": [
            {
                "type": "text",
                "position": 0,
                "points": 0,
                "required": 0,
                "body": (
                    "Multiplication is a fast way to add equal groups. "
                    "Division splits things into equal groups.\n\n"
                    "Example: 4 x 6 means 4 groups of 6 = 24.\n"
                    "24 / 6 means split 24 into groups of 6 = 4 groups."
                ),
            },
            {
                "type": "multiple_choice",
                "position": 1,
                "points": 2,
                "required": 1,
                "body": "What is 7 x 8?",
                "choices": [
                    {"body": "54", "is_correct": 0},
                    {"body": "56", "is_correct": 1},
                    {"body": "63", "is_correct": 0},
                    {"body": "48", "is_correct": 0},
                ],
            },
            {
                "type": "true_false",
                "position": 2,
                "points": 1,
                "required": 1,
                "body": "True or False: 6 x 9 = 9 x 6.",
                "choices": [
                    {"body": "True", "is_correct": 1},
                    {"body": "False", "is_correct": 0},
                ],
            },
            {
                "type": "multiple_choice",
                "position": 3,
                "points": 2,
                "required": 1,
                "body": "63 divided by 9 equals what?",
                "choices": [
                    {"body": "6", "is_correct": 0},
                    {"body": "8", "is_correct": 0},
                    {"body": "7", "is_correct": 1},
                    {"body": "9", "is_correct": 0},
                ],
            },
            {
                "type": "short_answer",
                "position": 4,
                "points": 3,
                "required": 1,
                "body": (
                    "There are 48 students going on a field trip. They ride in vans that hold 8 students each. "
                    "How many vans do they need? Show your work and write a complete answer sentence."
                ),
            },
            {
                "type": "short_answer",
                "position": 5,
                "points": 3,
                "required": 1,
                "body": (
                    "Explain in your own words: what is a remainder? "
                    "Give an example using real objects like candy or stickers."
                ),
            },
        ],
        "submission_rate": 0.80,
        "submissions_template": [
            {
                "grade": "A",
                "feedback": "Excellent! All correct and your word problem explanation was super clear.",
                "block_responses": [
                    {"position": 0, "body": None, "score": 0},
                    {"position": 1, "choice_index": 1, "score": 2},
                    {"position": 2, "choice_index": 0, "score": 1},
                    {"position": 3, "choice_index": 2, "score": 2},
                    {
                        "position": 4,
                        "body": "48 / 8 = 6. They need 6 vans.",
                        "score": 3,
                    },
                    {
                        "position": 5,
                        "body": "A remainder is what's left over when you can't divide evenly. Like if you have 13 stickers and want to share them with 4 friends, each gets 3 and you have 1 left over. That 1 is the remainder.",
                        "score": 3,
                    },
                ],
            },
            {
                "grade": "B",
                "feedback": "Really good work! Check question 1 — 7 x 8 is a tricky one. Your word problem was correct!",
                "block_responses": [
                    {"position": 0, "body": None, "score": 0},
                    {"position": 1, "choice_index": 0, "score": 0},
                    {"position": 2, "choice_index": 0, "score": 1},
                    {"position": 3, "choice_index": 2, "score": 2},
                    {
                        "position": 4,
                        "body": "48 / 8 = 6 vans.",
                        "score": 3,
                    },
                    {
                        "position": 5,
                        "body": "A remainder is the leftovers. Like 10 / 3 = 3 remainder 1.",
                        "score": 2,
                    },
                ],
            },
            {
                "grade": "C",
                "feedback": "Keep practicing those multiplication facts! Try the finger trick for the 9s and the 5-6-7-8 trick for 7x8.",
                "block_responses": [
                    {"position": 0, "body": None, "score": 0},
                    {"position": 1, "choice_index": 2, "score": 0},
                    {"position": 2, "choice_index": 1, "score": 0},
                    {"position": 3, "choice_index": 1, "score": 0},
                    {
                        "position": 4,
                        "body": "48 + 8 = 56 vans",
                        "score": 0,
                    },
                    {
                        "position": 5,
                        "body": "A remainder is a number.",
                        "score": 1,
                    },
                ],
            },
        ],
    },
]

FILTERED_WORDS = ["stupid", "hate"]

BUG_REPORTS = [
    {
        "user_role": "student",
        "title": "Post button not working",
        "description": "Sometimes clicking post does nothing",
        "severity": "medium",
    }
]

CONVERSATIONS = [
    {
        "type": "dm",
        "participants": ["student", "teacher"],
        "messages": [
            {
                "role": "student",
                "body": "Hi! I'm stuck on the fractions homework. I don't know how to find a common denominator.",
            },
            {"role": "teacher", "body": "No problem! Which problem are you stuck on?"},
            {
                "role": "student",
                "body": "1/3 + 1/4. The bottoms are different so I don't know what to do.",
            },
            {
                "role": "teacher",
                "body": "Think about it this way — what number can both 3 and 4 divide into evenly? Try listing the multiples of each!",
            },
            {"role": "student", "body": "Oh! It's 12! So it's 4/12 + 3/12 = 7/12?"},
            {"role": "teacher", "body": "Perfect! You got it!"},
        ],
    },
    {
        "type": "dm",
        "participants": ["student", "teacher"],
        "messages": [
            {
                "role": "teacher",
                "body": "Hey, just checking in — how are you feeling about the area and perimeter assignment?",
            },
            {
                "role": "student",
                "body": "Pretty good! I think I get area now. Perimeter I keep forgetting to add all four sides.",
            },
            {
                "role": "teacher",
                "body": "That's a really common one! Try thinking of it like walking around the outside of your house — you have to go all the way around.",
            },
        ],
    },
    {
        "type": "dm",
        "participants": ["student", "teacher"],
        "messages": [
            {
                "role": "student",
                "body": "Can I have more time on the word problems? I was absent and missed the lesson.",
            },
            {
                "role": "teacher",
                "body": "Of course! You can turn it in by Thursday. Let me know if you need help catching up.",
            },
            {"role": "student", "body": "Thank you so much!"},
        ],
    },
    {
        "type": "group",
        "title": "Fractions Study Group",
        "participant_roles": ["student", "student", "student", "teacher"],
        "messages": [
            {
                "role": "student",
                "body": "Does anyone understand how to compare fractions with different denominators?",
            },
            {
                "role": "student",
                "body": "I just convert them all to decimals and then it's easy to compare!",
            },
            {
                "role": "teacher",
                "body": "That's a great strategy! You can also find a common denominator. Both methods work perfectly.",
            },
            {
                "role": "student",
                "body": "Ohhh I didn't think of converting to decimals. Trying that!",
            },
            {"role": "teacher", "body": "Let me know how it goes!"},
            {"role": "student", "body": "It worked!! That was way easier for me."},
        ],
    },
    {
        "type": "group",
        "title": "Quiz Study Session",
        "participant_roles": ["student", "student", "student"],
        "messages": [
            {
                "role": "student",
                "body": "Anyone want to quiz each other on multiplication facts before Friday?",
            },
            {
                "role": "student",
                "body": "Yes! I keep messing up the 7s and 8s.",
            },
            {
                "role": "student",
                "body": "Me too. Let's make flashcard questions and take turns!",
            },
        ],
    },
    {
        "type": "dm",
        "participants": ["student", "teacher"],
        "coppa": True,
        "messages": [
            {
                "role": "student",
                "body": "I don't get the word problems at all. They're really hard.",
            },
            {
                "role": "teacher",
                "body": "That's okay! Let's work through one together. Read me the first problem and tell me what you think it's asking.",
            },
            {
                "role": "student",
                "body": "It says 24 apples are split into bags of 6. How many bags?",
            },
            {
                "role": "teacher",
                "body": "Great! So are we putting groups together or splitting into equal groups?",
            },
            {
                "role": "student",
                "body": "Splitting! So I divide? 24 divided by 6 is 4!",
            },
            {
                "role": "teacher",
                "body": "Yes!! You just solved it yourself. That's all there is to it!",
            },
        ],
    },
]


# =========================================================
# 👥 USER GENERATION
# =========================================================


def generate_username(first, last, existing):
    base = f"{first.lower()}.{last.lower()}"
    if base not in existing:
        return base
    i = 1
    while True:
        username = f"{base}.{i:02d}"
        if username not in existing:
            return username
        i += 1


def generate_users():
    users = []
    used = set()

    for i, (first, last) in enumerate(zip(FIRST_NAMES, LAST_NAMES)):
        role = "teacher" if i < 2 else "student"
        username = generate_username(first, last, used)
        used.add(username)
        users.append(
            {
                "username": username,
                "role": role,
                "display_name": f"{first} {last}",
            }
        )

    users.append(
        {
            "username": "parent.demo",
            "role": "parent",
            "display_name": "Demo Parent",
        }
    )

    return users


USERS = generate_users()

# =========================================================
# 🧠 HELPERS
# =========================================================


def now():
    """Return current UTC time as a string, timezone-aware."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def days_ago(days):
    """Return UTC datetime string for N days ago, timezone-aware."""
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def insert_and_get_id(db, query, params):
    return db.execute(query, params).lastrowid


def pick_user(users, role):
    pool = [u for u in users.values() if u["role"] == role]
    return random.choice(pool)["id"]


def clear_db(db):
    """
    Drops all user-created tables to reset the database.
    """
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    for t in tables:
        name = t["name"]
        if name.startswith("sqlite_"):
            continue
        db.execute(f"DROP TABLE IF EXISTS {name}")
    db.commit()
    print("🧹 Database cleared!")


# =========================================================
# 🌱 SEED FUNCTIONS
# =========================================================


def seed_admin(db):
    username = os.environ.get("ADMIN_USERNAME")
    password = os.environ.get("ADMIN_PASSWORD")
    role = os.environ.get("ADMIN_ROLE", "teacher")
    display_name = os.environ.get("ADMIN_DISPLAY_NAME")
    db.execute(
        """
        INSERT OR IGNORE INTO users
        (username, password_hash, role, display_name, bio, dob, coppa_status, onboarded, tour_seen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            username,
            bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            role,
            display_name,
            "",
            "2000-01-01",
            "approved",
            0,
            0,
        ),
    )


def seed_users(db):
    users = {}

    for u in USERS:
        db.execute(
            """
            INSERT OR IGNORE INTO users
            (username, password_hash, role, display_name, bio, dob, coppa_status, onboarded, tour_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                u["username"],
                bcrypt.hashpw("pass123".encode(), bcrypt.gensalt()).decode(),
                u["role"],
                u["display_name"],
                f"{u['role']} in Python program",
                "2000-01-01",
                "approved",
                1,
                0,
            ),
        )

    rows = db.execute("SELECT id, username, role FROM users").fetchall()

    for r in rows:
        users[r["username"]] = {"id": r["id"], "role": r["role"]}

    return users


def seed_topics(db):
    ids = {}
    for t in TOPICS:
        db.execute(
            "INSERT OR IGNORE INTO topics (name, description) VALUES (?, ?)",
            (t["name"], t["description"]),
        )

    rows = db.execute("SELECT id, name FROM topics").fetchall()
    for r in rows:
        ids[r["name"]] = r["id"]

    return ids


def seed_classroom(db, users):
    teacher_id = pick_user(users, "teacher")

    classroom_id = insert_and_get_id(
        db,
        """
        INSERT INTO classrooms (teacher_id, name, description, join_code)
        VALUES (?, ?, ?, ?)
        """,
        (
            teacher_id,
            CLASSROOM["name"],
            CLASSROOM["description"],
            CLASSROOM["join_code"],
        ),
    )

    for u in users.values():
        if u["role"] in ["student", "teacher"]:
            db.execute(
                """
                INSERT OR IGNORE INTO classroom_members (classroom_id, user_id, role)
                VALUES (?, ?, ?)
                """,
                (classroom_id, u["id"], u["role"]),
            )

    admin = db.execute(
        "SELECT id FROM users WHERE username = ?", (os.environ.get("ADMIN_USERNAME"),)
    ).fetchone()
    if admin:
        db.execute(
            "INSERT OR IGNORE INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, ?)",
            (classroom_id, admin["id"], "teacher"),
        )

    return classroom_id


def seed_posts(db, users, topics, classroom_id):
    post_ids = []

    for p in POSTS:
        uid = (
            users[p["user"]]["id"] if "user" in p else pick_user(users, p["user_role"])
        )

        pid = insert_and_get_id(
            db,
            """
            INSERT INTO posts (user_id, topic_id, title, body, classroom_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                uid,
                topics[p["topic"]],
                p["title"],
                p["body"],
                classroom_id,
                days_ago(random.randint(0, 3)),
            ),
        )

        post_ids.append(pid)

        for r in p.get("replies", []):
            rid = (
                users[r["user"]]["id"]
                if "user" in r
                else pick_user(users, r["user_role"])
            )

            insert_and_get_id(
                db,
                """
                INSERT INTO posts (user_id, body, parent_id, classroom_id, title, created_at)
                VALUES (?, ?, ?, ?, '', ?)
                """,
                (rid, r["body"], pid, classroom_id, now()),
            )

            db.execute(
                "UPDATE posts SET reply_count = reply_count + 1 WHERE id = ?", (pid,)
            )

    return post_ids


def seed_announcements(db, users, classroom_id):
    teacher_ids = [u["id"] for u in users.values() if u["role"] == "teacher"]

    for a in ANNOUNCEMENTS:
        insert_and_get_id(
            db,
            """
            INSERT INTO posts (
                post_type, user_id, title, body, classroom_id, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "announcement",
                random.choice(teacher_ids),
                a["title"],
                a["body"],
                classroom_id,
                days_ago(random.randint(0, 5)),
            ),
        )


def seed_reactions(db, users, post_ids):
    for pid in post_ids:
        for u in users.values():
            if random.random() < 0.4:
                db.execute(
                    """
                    INSERT OR IGNORE INTO reactions (post_id, user_id, reaction, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (pid, u["id"], random.choice(EMOJIS), now()),
                )


def seed_assignments(db, users, classroom_id):
    students = [u for u in users.values() if u["role"] == "student"]

    for a in ASSIGNMENTS:
        aid = insert_and_get_id(
            db,
            """
            INSERT INTO assignments (classroom_id, title, instructions)
            VALUES (?, ?, ?)
            """,
            (classroom_id, a["title"], a["instructions"]),
        )

        rate = a.get("submission_rate", 1.0)
        templates = a.get("submissions_template", [])
        if not templates:
            continue

        submitting_students = [s for s in students if random.random() < rate]

        for student in submitting_students:
            template = random.choice(templates)
            db.execute(
                """
                INSERT OR IGNORE INTO submissions (assignment_id, user_id, body, grade, feedback)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    aid,
                    student["id"],
                    template["body"],
                    template.get("grade"),
                    template.get("feedback"),
                ),
            )


def seed_quiz_assignment(db, users, classroom_id):
    students = [u for u in users.values() if u["role"] == "student"]

    for q in QUIZZES:
        qid = insert_and_get_id(
            db,
            """
            INSERT INTO assignments (classroom_id, title, instructions)
            VALUES (?,?,?)
            """,
            (classroom_id, q["title"], q["instructions"]),
        )

        block_ids = {}
        block_choice_ids = {}

        for block in q.get("blocks", []):
            bid = insert_and_get_id(
                db,
                """
                INSERT INTO lesson_blocks (assignment_id, type, body, position, points, required)
                VALUES (?,?,?,?,?,?)
                """,
                (
                    qid,
                    block["type"],
                    block["body"],
                    block["position"],
                    block["points"],
                    block.get("required", 1),
                ),
            )
            block_ids[block["position"]] = bid

            if "choices" in block:
                ids = []
                for choice in block["choices"]:
                    cid = insert_and_get_id(
                        db,
                        "INSERT INTO block_choices (block_id, body, is_correct) VALUES (?,?,?)",
                        (bid, choice["body"], choice["is_correct"]),
                    )
                    ids.append(cid)
                block_choice_ids[block["position"]] = ids

        rate = q.get("submission_rate", 1.0)
        templates = q.get("submissions_template", [])
        if not templates:
            continue

        submitting_students = [s for s in students if random.random() < rate]

        for student in submitting_students:
            template = random.choice(templates)
            sub_id = insert_and_get_id(
                db,
                """
                INSERT OR IGNORE INTO submissions (assignment_id, user_id, body, grade, feedback)
                VALUES (?,?,?,?,?)
                """,
                (
                    qid,
                    student["id"],
                    "",
                    template.get("grade"),
                    template.get("feedback"),
                ),
            )

            for resp in template.get("block_responses", []):
                if resp["position"] == 0:
                    continue

                choice_id = None
                if "choice_index" in resp:
                    choice_id = block_choice_ids[resp["position"]][resp["choice_index"]]

                db.execute(
                    """
                    INSERT INTO block_responses (submission_id, block_id, choice_id, body, score)
                    VALUES (?,?,?,?,?)
                    """,
                    (
                        sub_id,
                        block_ids[resp["position"]],
                        choice_id,
                        resp.get("body"),
                        resp.get("score", 0),
                    ),
                )


def seed_filtered_words(db):
    for word in FILTERED_WORDS:
        db.execute("INSERT OR IGNORE INTO filtered_words (word) VALUES (?)", (word,))


def seed_bug_reports(db, users):
    for b in BUG_REPORTS:
        uid = (
            users[b["user"]]["id"] if "user" in b else pick_user(users, b["user_role"])
        )

        db.execute(
            """
            INSERT INTO bug_reports (reported_by, title, description, severity)
            VALUES (?, ?, ?, ?)
            """,
            (uid, b["title"], b["description"], b["severity"]),
        )


def seed_conversations(db, users, classroom_id):
    from app.models.messaging import get_or_create_dm, create_conversation, send_message

    students = [u for u in users.values() if u["role"] == "student"]
    teachers = [u for u in users.values() if u["role"] == "teacher"]

    used_dm_pairs = set()

    for conv in CONVERSATIONS:
        is_coppa = conv.get("coppa", False)

        if conv["type"] == "dm":
            # Pick a unique student/teacher pair
            student = None
            for s in random.sample(students, len(students)):
                for t in random.sample(teachers, len(teachers)):
                    pair = (s["id"], t["id"])
                    if pair not in used_dm_pairs:
                        student, teacher = s, t
                        used_dm_pairs.add(pair)
                        break
                if student:
                    break

            if not student:
                continue

            # Mark student as under-13 for COPPA test conversations
            if is_coppa:
                from datetime import date

                dob = date(date.today().year - 11, 6, 15).isoformat()
                db.execute(
                    "UPDATE users SET dob = ?, coppa_status = 'pending' WHERE id = ?",
                    (dob, student["id"]),
                )

            conv_id = get_or_create_dm(classroom_id, student["id"], teacher["id"])
            role_map = {"student": student["id"], "teacher": teacher["id"]}

        else:  # group
            participant_roles = conv.get(
                "participant_roles", ["student", "student", "teacher"]
            )
            available_students = random.sample(
                students, min(len(students), participant_roles.count("student"))
            )
            available_teachers = random.sample(
                teachers, min(len(teachers), participant_roles.count("teacher"))
            )

            members = []
            si, ti = 0, 0
            for role in participant_roles:
                if role == "student" and si < len(available_students):
                    members.append(available_students[si])
                    si += 1
                elif role == "teacher" and ti < len(available_teachers):
                    members.append(available_teachers[ti])
                    ti += 1

            if len(members) < 2:
                continue

            member_ids = [m["id"] for m in members]
            conv_id = create_conversation(
                classroom_id, member_ids[0], member_ids[1:], title=conv.get("title")
            )
            role_map = {
                "student": [m["id"] for m in members if m["role"] == "student"],
                "teacher": [m["id"] for m in members if m["role"] == "teacher"],
            }

        # Insert messages
        student_idx = teacher_idx = 0
        for msg in conv.get("messages", []):
            if conv["type"] == "dm":
                sender_id = role_map[msg["role"]]
            else:
                pool = role_map[msg["role"]]
                if msg["role"] == "student":
                    sender_id = pool[student_idx % len(pool)]
                    student_idx += 1
                else:
                    sender_id = pool[teacher_idx % len(pool)]
                    teacher_idx += 1

            send_message(conv_id, sender_id, msg["body"])


# =========================================================
# 🚀 MAIN
# =========================================================


def main():
    with app.app_context():
        db = get_db()

        # Clear everything first
        clear_db(db)

        from app.models import init_db

        init_db(app)
        seed_admin(db)
        users = seed_users(db)
        topics = seed_topics(db)
        classroom_id = seed_classroom(db, users)

        seed_announcements(db, users, classroom_id)
        post_ids = seed_posts(db, users, topics, classroom_id)
        seed_reactions(db, users, post_ids)
        seed_assignments(db, users, classroom_id)
        seed_quiz_assignment(db, users, classroom_id)
        seed_filtered_words(db)
        seed_bug_reports(db, users)
        seed_conversations(db, users, classroom_id)
        db.commit()

        print("✅ Demo seed complete!")

        # -------------------------------
        # Print usernames with password
        # -------------------------------

    # -------------------------------
    # Print usernames by role with password
    # -------------------------------
    print("\n📝 Users & Demo Passwords:")

    teachers = [u for u in USERS if u["role"] == "teacher"]
    students = [u for u in USERS if u["role"] == "student"]

    print("\n👩‍ Admin:")
    print("Admin account seeded")

    print("\n👩‍🏫 Teachers:")
    for t in teachers:
        print(
            f"Username: {t['username']:<20} | Role: {t['role']:<7} | Password: pass123"
        )

    print("\n🧑‍🎓 Students:")
    for s in students:
        print(
            f"Username: {s['username']:<20} | Role: {s['role']:<7} | Password: pass123"
        )


if __name__ == "__main__":
    main()
